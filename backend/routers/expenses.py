from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from datetime import datetime
from typing import Optional, List

from database import get_db
import models
import schemas

router = APIRouter(prefix="/expenses", tags=["expenses"])


def _categorize_and_detect(expense: models.Expense, db: Session):
    """Run ML categorization + anomaly detection on a saved expense."""
    try:
        from ml.categorizer import get_categorizer
        from ml.anomaly_detector import get_anomaly_detector

        categorizer = get_categorizer()
        if categorizer is not None:
            pred = categorizer.predict(expense.description)
            expense.predicted_category = pred["category"]
            if not expense.category:
                expense.category = pred["category"]

        detector = get_anomaly_detector()
        if detector is not None:
            res = detector.detect({
                "amount": expense.amount,
                "category": expense.category or "Others",
                "date": expense.date,
            })
            expense.is_anomaly = bool(res["is_anomaly"])
            expense.anomaly_score = float(res["anomaly_score"])
        db.commit()
        db.refresh(expense)
    except Exception as e:
        print(f"[expenses] ML enrichment failed: {e}")


@router.post("", response_model=schemas.ExpenseRead)
def create_expense(payload: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    expense = models.Expense(
        description=payload.description,
        amount=payload.amount,
        category=payload.category,
        date=payload.date or datetime.utcnow(),
        payment_method=payload.payment_method,
        notes=payload.notes,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    _categorize_and_detect(expense, db)
    return expense


@router.get("/summary")
def expense_summary(month: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns total by category and totals this/last month."""
    now = datetime.utcnow()
    cur_year = now.year
    cur_month = now.month

    if month:
        try:
            y, m = month.split("-")
            cur_year, cur_month = int(y), int(m)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    # last month
    if cur_month == 1:
        last_year, last_m = cur_year - 1, 12
    else:
        last_year, last_m = cur_year, cur_month - 1

    total_this_month = db.query(func.coalesce(func.sum(models.Expense.amount), 0.0)).filter(
        extract("year", models.Expense.date) == cur_year,
        extract("month", models.Expense.date) == cur_month,
    ).scalar() or 0.0

    total_last_month = db.query(func.coalesce(func.sum(models.Expense.amount), 0.0)).filter(
        extract("year", models.Expense.date) == last_year,
        extract("month", models.Expense.date) == last_m,
    ).scalar() or 0.0

    by_cat_rows = db.query(
        models.Expense.category,
        func.sum(models.Expense.amount),
        func.count(models.Expense.id),
    ).filter(
        extract("year", models.Expense.date) == cur_year,
        extract("month", models.Expense.date) == cur_month,
    ).group_by(models.Expense.category).all()

    by_category = {
        (cat or "Others"): {"total": float(total or 0.0), "count": int(cnt or 0)}
        for cat, total, cnt in by_cat_rows
    }

    count = db.query(func.count(models.Expense.id)).filter(
        extract("year", models.Expense.date) == cur_year,
        extract("month", models.Expense.date) == cur_month,
    ).scalar() or 0

    return {
        "total_this_month": float(total_this_month),
        "total_last_month": float(total_last_month),
        "by_category": by_category,
        "count": int(count),
        "month": f"{cur_year:04d}-{cur_month:02d}",
    }


@router.get("", response_model=List[schemas.ExpenseRead])
def list_expenses(
    month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Expense)
    if month:
        y, m = month.split("-")
        q = q.filter(
            extract("year", models.Expense.date) == int(y),
            extract("month", models.Expense.date) == int(m),
        )
    if category:
        q = q.filter(models.Expense.category == category)
    return q.order_by(models.Expense.date.desc()).all()


@router.get("/{expense_id}", response_model=schemas.ExpenseRead)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.put("/{expense_id}", response_model=schemas.ExpenseRead)
def update_expense(expense_id: int, payload: schemas.ExpenseUpdate, db: Session = Depends(get_db)):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(expense, k, v)
    db.commit()
    db.refresh(expense)
    _categorize_and_detect(expense, db)
    return expense


@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return {"ok": True, "deleted_id": expense_id}
