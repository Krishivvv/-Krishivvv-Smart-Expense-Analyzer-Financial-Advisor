"""Anomaly detection for expenses.

Combines:
  - Per-category z-score (amount > mean + 2.5 * std)
  - IsolationForest on [amount, day_of_week, day_of_month]
"""
import os
from datetime import datetime
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
_MODEL_PATH = os.path.join(_MODELS_DIR, "anomaly_detector.pkl")


class AnomalyDetector:
    def __init__(self):
        self.iso: Optional[IsolationForest] = None
        self.cat_stats: dict = {}  # category -> {mean, std, max}
        self.is_trained = False

    def _features(self, amount: float, date: datetime) -> np.ndarray:
        if not isinstance(date, datetime):
            try:
                date = pd.to_datetime(date).to_pydatetime()
            except Exception:
                date = datetime.utcnow()
        return np.array([[float(amount), float(date.weekday()), float(date.day)]])

    def train(self, expenses_df: pd.DataFrame):
        if expenses_df is None or expenses_df.empty or len(expenses_df) < 10:
            print("[anomaly] Not enough data; skipping training.")
            return

        df = expenses_df.copy()
        df = df[df["amount"].notna()]
        df["category"] = df["category"].fillna("Others")

        # Per-category stats
        stats = {}
        for cat, grp in df.groupby("category"):
            amts = grp["amount"].astype(float)
            stats[cat] = {
                "mean": float(amts.mean()),
                "std": float(amts.std() if len(amts) > 1 else amts.mean() * 0.3),
                "max": float(amts.max()),
                "count": int(len(amts)),
            }
        self.cat_stats = stats

        # IsolationForest features
        try:
            df["date"] = pd.to_datetime(df["date"])
            features = np.column_stack([
                df["amount"].astype(float).values,
                df["date"].dt.weekday.astype(float).values,
                df["date"].dt.day.astype(float).values,
            ])
            iso = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
            iso.fit(features)
            self.iso = iso
            self.is_trained = True
            os.makedirs(_MODELS_DIR, exist_ok=True)
            joblib.dump({"iso": iso, "cat_stats": stats}, _MODEL_PATH)
            print(f"[anomaly] Trained on {len(df)} rows; categories tracked: {len(stats)}")
        except Exception as e:
            print(f"[anomaly] IsolationForest training failed: {e}")

    def load(self) -> bool:
        if not os.path.exists(_MODEL_PATH):
            return False
        try:
            blob = joblib.load(_MODEL_PATH)
            self.iso = blob.get("iso")
            self.cat_stats = blob.get("cat_stats", {})
            self.is_trained = self.iso is not None
            return True
        except Exception as e:
            print(f"[anomaly] Load failed: {e}")
            return False

    def detect(self, expense: dict) -> dict:
        amount = float(expense.get("amount", 0))
        category = expense.get("category", "Others") or "Others"
        date = expense.get("date") or datetime.utcnow()

        # Z-score check vs category
        stat = self.cat_stats.get(category)
        z_anomaly = False
        z_score = 0.0
        threshold = None
        if stat and stat["std"] > 0:
            z_score = (amount - stat["mean"]) / stat["std"]
            threshold = stat["mean"] + 2.5 * stat["std"]
            if amount > threshold:
                z_anomaly = True

        # IsolationForest check
        iso_anomaly = False
        iso_score = 0.0
        if self.iso is not None:
            try:
                feat = self._features(amount, date)
                iso_pred = self.iso.predict(feat)[0]  # -1 anomaly, 1 normal
                iso_score = float(self.iso.score_samples(feat)[0])
                iso_anomaly = iso_pred == -1
            except Exception:
                pass

        is_anomaly = z_anomaly or iso_anomaly

        # Severity & reason
        if z_anomaly and stat:
            ratio = amount / max(stat["mean"], 1.0)
            if ratio >= 4.0:
                severity = "high"
            elif ratio >= 2.5:
                severity = "medium"
            else:
                severity = "low"
            reason = (f"Amount ₹{amount:,.0f} is {ratio:.1f}x the average for {category} "
                      f"(₹{stat['mean']:,.0f}).")
        elif iso_anomaly:
            severity = "medium"
            reason = "Unusual spending pattern detected by AI."
        else:
            severity = "low"
            reason = "Within normal range."

        # Combined anomaly score normalised to [-1, 1]
        combined = float(np.tanh(z_score / 3.0)) if stat else iso_score
        return {
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": round(combined, 3),
            "reason": reason,
            "severity": severity,
        }

    def get_anomalies(self, expenses_df: pd.DataFrame) -> list:
        if expenses_df is None or expenses_df.empty:
            return []
        out = []
        for _, row in expenses_df.iterrows():
            res = self.detect({
                "amount": row.get("amount", 0),
                "category": row.get("category", "Others"),
                "date": row.get("date", datetime.utcnow()),
            })
            if res["is_anomaly"]:
                out.append({
                    "id": int(row.get("id", 0)),
                    "description": row.get("description", ""),
                    "amount": float(row.get("amount", 0)),
                    "category": row.get("category", "Others"),
                    "reason": res["reason"],
                    "severity": res["severity"],
                    "anomaly_score": res["anomaly_score"],
                })
        return out


_singleton: Optional[AnomalyDetector] = None


def get_anomaly_detector() -> Optional[AnomalyDetector]:
    global _singleton
    if _singleton is not None:
        return _singleton

    detector = AnomalyDetector()
    if not detector.load():
        try:
            from database import SessionLocal
            import models as m
            db = SessionLocal()
            try:
                rows = db.query(m.Expense).all()
                df = pd.DataFrame([{
                    "id": r.id,
                    "description": r.description,
                    "amount": r.amount,
                    "category": r.category or "Others",
                    "date": r.date,
                } for r in rows])
            finally:
                db.close()
            detector.train(df)
        except Exception as e:
            print(f"[anomaly] Auto-train failed: {e}")

    _singleton = detector
    return _singleton
