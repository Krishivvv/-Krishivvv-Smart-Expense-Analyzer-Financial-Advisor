from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import pandas as pd

from database import get_db
import models
import schemas

router = APIRouter(prefix="/advisor", tags=["advisor"])


def _expenses_df(db: Session) -> pd.DataFrame:
    rows = db.query(models.Expense).all()
    if not rows:
        return pd.DataFrame(columns=["id", "description", "amount", "category", "date"])
    return pd.DataFrame([{
        "id": r.id,
        "description": r.description,
        "amount": r.amount,
        "category": r.category or "Others",
        "date": r.date,
        "is_anomaly": r.is_anomaly,
        "payment_method": r.payment_method or "upi",
    } for r in rows])


@router.get("/advice")
def get_advice(db: Session = Depends(get_db)):
    from ml.advisor_engine import FinancialAdvisor
    df = _expenses_df(db)
    budgets = db.query(models.Budget).all()
    advisor = FinancialAdvisor()
    return advisor.analyze(df, budgets=budgets)


@router.get("/budget-alerts")
def budget_alerts(db: Session = Depends(get_db)):
    from ml.advisor_engine import FinancialAdvisor
    df = _expenses_df(db)
    budgets = db.query(models.Budget).all()
    advisor = FinancialAdvisor()
    result = advisor.analyze(df, budgets=budgets)
    return {"alerts": result.get("budget_alerts", [])}


@router.post("/set-budget", response_model=schemas.BudgetRead)
def set_budget(payload: schemas.BudgetCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Budget).filter(
        models.Budget.category == payload.category,
        models.Budget.month == payload.month,
    ).first()
    if existing:
        existing.monthly_limit = payload.monthly_limit
        db.commit()
        db.refresh(existing)
        return existing
    budget = models.Budget(**payload.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.get("/budgets")
def list_budgets(month: str = None, db: Session = Depends(get_db)):
    q = db.query(models.Budget)
    if month:
        q = q.filter(models.Budget.month == month)
    rows = q.all()
    return [{"id": b.id, "category": b.category, "monthly_limit": b.monthly_limit, "month": b.month}
            for b in rows]
