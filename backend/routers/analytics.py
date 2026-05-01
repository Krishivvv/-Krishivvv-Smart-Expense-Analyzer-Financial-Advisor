from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

from database import get_db
import models
import schemas

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _expenses_df(db: Session) -> pd.DataFrame:
    rows = db.query(models.Expense).all()
    if not rows:
        return pd.DataFrame(columns=[
            "id", "description", "amount", "category", "date",
            "is_anomaly", "payment_method"
        ])
    return pd.DataFrame([{
        "id": r.id,
        "description": r.description,
        "amount": r.amount,
        "category": r.category or "Others",
        "date": r.date,
        "is_anomaly": r.is_anomaly,
        "payment_method": r.payment_method or "upi",
    } for r in rows])


@router.post("/categorize", response_model=schemas.CategorizeResponse)
def categorize_expense(payload: schemas.CategorizeRequest):
    from ml.categorizer import get_categorizer
    categorizer = get_categorizer()
    if categorizer is None:
        raise HTTPException(status_code=503, detail="Categorizer not available")
    result = categorizer.predict(payload.description)
    return result


@router.get("/categorize")
def categorize_query(description: str):
    from ml.categorizer import get_categorizer
    categorizer = get_categorizer()
    if categorizer is None:
        raise HTTPException(status_code=503, detail="Categorizer not available")
    return categorizer.predict(description)


@router.get("/anomalies")
def list_anomalies(db: Session = Depends(get_db)):
    from ml.anomaly_detector import get_anomaly_detector
    detector = get_anomaly_detector()
    df = _expenses_df(db)
    if df.empty:
        return {"anomalies": [], "count": 0}

    anomalies = []
    for _, row in df.iterrows():
        if detector is not None:
            res = detector.detect({
                "amount": float(row["amount"]),
                "category": row["category"],
                "date": row["date"],
            })
        else:
            res = {"is_anomaly": bool(row.get("is_anomaly", False)),
                   "anomaly_score": 0.0, "reason": "", "severity": "low"}

        if res["is_anomaly"]:
            anomalies.append({
                "id": int(row["id"]),
                "description": row["description"],
                "amount": float(row["amount"]),
                "category": row["category"],
                "date": row["date"].isoformat() if hasattr(row["date"], "isoformat") else str(row["date"]),
                "anomaly_score": float(res["anomaly_score"]),
                "reason": res["reason"],
                "severity": res["severity"],
            })

    anomalies.sort(key=lambda x: x["amount"], reverse=True)
    return {"anomalies": anomalies, "count": len(anomalies)}


@router.get("/forecast")
def forecast(category: Optional[str] = None, db: Session = Depends(get_db)):
    from ml.forecaster import get_forecaster
    forecaster = get_forecaster()
    if forecaster is None:
        raise HTTPException(status_code=503, detail="Forecaster not available")
    if category:
        return forecaster.forecast_next_month(category)
    return {"forecasts": forecaster.forecast_all_categories()}


@router.get("/summary")
def analytics_summary(db: Session = Depends(get_db)):
    df = _expenses_df(db)
    now = datetime.utcnow()

    cur_year, cur_month = now.year, now.month
    last_year = cur_year if cur_month > 1 else cur_year - 1
    last_month = cur_month - 1 if cur_month > 1 else 12

    if df.empty:
        return {
            "total_this_month": 0.0,
            "total_last_month": 0.0,
            "change_percent": 0.0,
            "by_category": {},
            "daily_totals": [],
            "top_merchants": [],
            "payment_method_split": {"cash": 0, "card": 0, "upi": 0},
            "anomaly_count": 0,
        }

    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    this_month_df = df[(df["year"] == cur_year) & (df["month"] == cur_month)]
    last_month_df = df[(df["year"] == last_year) & (df["month"] == last_month)]

    total_this = float(this_month_df["amount"].sum())
    total_last = float(last_month_df["amount"].sum())
    change = ((total_this - total_last) / total_last * 100.0) if total_last > 0 else 0.0

    # Budgets for current month
    budgets = db.query(models.Budget).filter(
        models.Budget.month == f"{cur_year:04d}-{cur_month:02d}"
    ).all()
    budget_map = {b.category: b.monthly_limit for b in budgets}

    by_category = {}
    for cat, grp in this_month_df.groupby("category"):
        total = float(grp["amount"].sum())
        cnt = int(len(grp))
        avg = float(grp["amount"].mean()) if cnt > 0 else 0.0
        limit = float(budget_map.get(cat, 0.0))
        used_pct = (total / limit * 100.0) if limit > 0 else 0.0
        by_category[cat] = {
            "total": round(total, 2),
            "count": cnt,
            "avg": round(avg, 2),
            "budget_limit": round(limit, 2),
            "budget_used_pct": round(used_pct, 1),
        }

    # daily totals last 30 days
    cutoff = now - timedelta(days=30)
    last30 = df[df["date"] >= cutoff].copy()
    last30["day"] = last30["date"].dt.strftime("%Y-%m-%d")
    daily = last30.groupby("day")["amount"].sum().reset_index()
    daily_totals = [{"date": r["day"], "amount": round(float(r["amount"]), 2)} for _, r in daily.iterrows()]
    daily_totals.sort(key=lambda x: x["date"])

    # Top merchants (by description)
    top = (this_month_df.groupby("description")
           .agg(total=("amount", "sum"), count=("amount", "count"))
           .reset_index()
           .sort_values("total", ascending=False)
           .head(5))
    top_merchants = [{"description": r["description"], "total": round(float(r["total"]), 2),
                      "count": int(r["count"])} for _, r in top.iterrows()]

    # Payment method split (this month)
    pm_total = this_month_df["amount"].sum()
    pm_split = {"cash": 0.0, "card": 0.0, "upi": 0.0}
    if pm_total > 0:
        for pm in ["cash", "card", "upi"]:
            s = float(this_month_df[this_month_df["payment_method"] == pm]["amount"].sum())
            pm_split[pm] = round(s / pm_total * 100.0, 1)

    anomaly_count = int(df["is_anomaly"].sum()) if "is_anomaly" in df.columns else 0

    return {
        "total_this_month": round(total_this, 2),
        "total_last_month": round(total_last, 2),
        "change_percent": round(change, 1),
        "by_category": by_category,
        "daily_totals": daily_totals,
        "top_merchants": top_merchants,
        "payment_method_split": pm_split,
        "anomaly_count": anomaly_count,
    }


@router.get("/health")
def analytics_health(db: Session = Depends(get_db)):
    from ml.advisor_engine import FinancialAdvisor
    df = _expenses_df(db)
    budgets = db.query(models.Budget).all()
    advisor = FinancialAdvisor()
    return advisor.analyze(df, budgets=budgets)
