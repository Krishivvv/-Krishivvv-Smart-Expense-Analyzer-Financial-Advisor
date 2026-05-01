import io
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd

from database import get_db
import models

router = APIRouter(prefix="/upload", tags=["upload"])


REQUIRED_COLUMNS = {"description", "amount"}


@router.post("/csv")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    df.columns = [c.strip().lower() for c in df.columns]
    if not REQUIRED_COLUMNS.issubset(set(df.columns)):
        raise HTTPException(
            status_code=400,
            detail=f"CSV must contain at least columns: {sorted(REQUIRED_COLUMNS)}"
        )

    # Lazy ML imports
    categorizer = None
    detector = None
    try:
        from ml.categorizer import get_categorizer
        from ml.anomaly_detector import get_anomaly_detector
        categorizer = get_categorizer()
        detector = get_anomaly_detector()
    except Exception as e:
        print(f"[upload] ML not ready: {e}")

    inserted = 0
    anomalies_found = 0
    cat_counts: dict = {}

    for _, row in df.iterrows():
        try:
            desc = str(row["description"]).strip()
            amount = float(row["amount"])
        except Exception:
            continue
        if not desc or amount <= 0:
            continue

        # Optional columns
        cat = str(row["category"]).strip() if "category" in row and pd.notna(row.get("category")) else None
        date_val = None
        if "date" in row and pd.notna(row.get("date")):
            try:
                date_val = pd.to_datetime(row["date"]).to_pydatetime()
            except Exception:
                date_val = None
        pm = str(row["payment_method"]).strip().lower() if "payment_method" in row and pd.notna(row.get("payment_method")) else "upi"

        predicted = None
        if categorizer is not None:
            try:
                pred = categorizer.predict(desc)
                predicted = pred["category"]
                if not cat:
                    cat = predicted
            except Exception:
                pass

        is_anomaly = False
        anomaly_score = None
        if detector is not None:
            try:
                res = detector.detect({
                    "amount": amount,
                    "category": cat or "Others",
                    "date": date_val or datetime.utcnow(),
                })
                is_anomaly = bool(res["is_anomaly"])
                anomaly_score = float(res["anomaly_score"])
            except Exception:
                pass

        expense = models.Expense(
            description=desc,
            amount=amount,
            category=cat,
            predicted_category=predicted,
            date=date_val or datetime.utcnow(),
            payment_method=pm,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
        )
        db.add(expense)
        inserted += 1
        if is_anomaly:
            anomalies_found += 1
        if cat:
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    db.commit()

    return {
        "inserted": inserted,
        "anomalies_found": anomalies_found,
        "categories_detected": cat_counts,
    }


@router.get("/template")
def download_template():
    """Return a sample CSV the user can fill in."""
    sample = (
        "description,amount,category,date,payment_method\n"
        "Lunch at cafe,320,Food,2026-04-01,upi\n"
        "Uber to office,180,Transport,2026-04-01,upi\n"
        "Amazon order,1200,Shopping,2026-04-02,card\n"
        "Electricity bill,1800,Utilities,2026-04-05,upi\n"
        "Movie tickets,800,Entertainment,2026-04-03,card\n"
    )
    return StreamingResponse(
        io.StringIO(sample),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses_template.csv"},
    )
