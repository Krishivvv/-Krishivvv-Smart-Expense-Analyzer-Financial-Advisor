"""Spending forecaster using LinearRegression per category."""
import os
from datetime import datetime, timedelta
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
_MODEL_PATH = os.path.join(_MODELS_DIR, "forecaster.pkl")


class SpendingForecaster:
    def __init__(self):
        self.models: dict = {}  # category -> LinearRegression
        self.daily_means: dict = {}  # category -> mean daily spend
        self.history: dict = {}  # category -> daily series
        self.is_trained = False

    def train(self, expenses_df: pd.DataFrame):
        if expenses_df is None or expenses_df.empty or len(expenses_df) < 10:
            print("[forecaster] Not enough data; skipping.")
            return

        df = expenses_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["day"] = df["date"].dt.normalize()
        df["category"] = df["category"].fillna("Others")

        if df.empty:
            return

        # Index days from oldest to newest
        min_day = df["day"].min()
        df["day_idx"] = (df["day"] - min_day).dt.days

        models_dict = {}
        means_dict = {}
        history_dict = {}

        for cat, grp in df.groupby("category"):
            daily = grp.groupby("day_idx")["amount"].sum().reset_index()
            if len(daily) < 2:
                # Not enough data for regression
                means_dict[cat] = float(daily["amount"].mean()) if len(daily) else 0.0
                history_dict[cat] = daily.to_dict(orient="records")
                continue
            X = daily["day_idx"].values.reshape(-1, 1).astype(float)
            y = daily["amount"].values.astype(float)
            try:
                lr = LinearRegression()
                lr.fit(X, y)
                models_dict[cat] = lr
                means_dict[cat] = float(np.mean(y))
                history_dict[cat] = daily.to_dict(orient="records")
            except Exception as e:
                print(f"[forecaster] {cat} fit failed: {e}")

        self.models = models_dict
        self.daily_means = means_dict
        self.history = history_dict
        self._min_day = min_day
        self.is_trained = True

        try:
            os.makedirs(_MODELS_DIR, exist_ok=True)
            joblib.dump({
                "models": models_dict,
                "daily_means": means_dict,
                "history": history_dict,
                "min_day": min_day,
            }, _MODEL_PATH)
        except Exception as e:
            print(f"[forecaster] Save failed: {e}")

        print(f"[forecaster] Trained for {len(models_dict)} categories.")

    def load(self) -> bool:
        if not os.path.exists(_MODEL_PATH):
            return False
        try:
            blob = joblib.load(_MODEL_PATH)
            self.models = blob["models"]
            self.daily_means = blob["daily_means"]
            self.history = blob.get("history", {})
            self._min_day = blob.get("min_day", datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[forecaster] Load failed: {e}")
            return False

    def forecast_next_month(self, category: Optional[str] = None) -> dict:
        if category is None:
            return {"forecasts": self.forecast_all_categories()}

        now = pd.Timestamp(datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
        next_month_start = (now.replace(day=1) + pd.offsets.MonthBegin(1))
        next_month_end = next_month_start + pd.offsets.MonthEnd(0)
        days_in_next = (next_month_end - next_month_start).days + 1

        # Current month spent
        cur_month_start = now.replace(day=1)
        cur_total = 0.0
        cat_history = self.history.get(category, [])
        for rec in cat_history:
            try:
                d = pd.Timestamp(self._min_day) + pd.Timedelta(days=int(rec["day_idx"]))
                if d >= cur_month_start and d <= now:
                    cur_total += float(rec["amount"])
            except Exception:
                continue

        predicted_daily = []
        total_predicted = 0.0

        if category in self.models:
            lr = self.models[category]
            base_idx = (next_month_start - pd.Timestamp(self._min_day)).days
            for i in range(days_in_next):
                idx = base_idx + i
                pred = float(lr.predict(np.array([[idx]]))[0])
                pred = max(0.0, pred)  # no negative spending
                day = (next_month_start + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
                predicted_daily.append({"date": day, "predicted_amount": round(pred, 2)})
                total_predicted += pred
        else:
            mean = self.daily_means.get(category, 0.0)
            for i in range(days_in_next):
                day = (next_month_start + pd.Timedelta(days=i)).strftime("%Y-%m-%d")
                predicted_daily.append({"date": day, "predicted_amount": round(mean, 2)})
                total_predicted += mean

        # Trend: compare slope to mean
        trend = "stable"
        confidence = 0.5
        if category in self.models:
            slope = float(self.models[category].coef_[0])
            mean = self.daily_means.get(category, 1.0)
            if abs(slope) < 0.05 * max(mean, 1.0):
                trend = "stable"
                confidence = 0.75
            elif slope > 0:
                trend = "increasing"
                confidence = 0.7
            else:
                trend = "decreasing"
                confidence = 0.7

        return {
            "category": category,
            "current_month_spent": round(cur_total, 2),
            "predicted_next_month": round(total_predicted, 2),
            "predicted_daily_breakdown": predicted_daily,
            "trend": trend,
            "confidence": round(confidence, 2),
        }

    def forecast_all_categories(self) -> list:
        cats = set(self.models.keys()) | set(self.daily_means.keys())
        out = []
        for cat in cats:
            try:
                out.append(self.forecast_next_month(cat))
            except Exception as e:
                print(f"[forecaster] forecast for {cat} failed: {e}")
        out.sort(key=lambda x: x["predicted_next_month"], reverse=True)
        return out


_singleton: Optional[SpendingForecaster] = None


def get_forecaster() -> Optional[SpendingForecaster]:
    global _singleton
    if _singleton is not None:
        return _singleton

    f = SpendingForecaster()
    if not f.load():
        try:
            from database import SessionLocal
            import models as m
            db = SessionLocal()
            try:
                rows = db.query(m.Expense).all()
                df = pd.DataFrame([{
                    "amount": r.amount,
                    "category": r.category or "Others",
                    "date": r.date,
                } for r in rows])
            finally:
                db.close()
            f.train(df)
        except Exception as e:
            print(f"[forecaster] Auto-train failed: {e}")

    _singleton = f
    return _singleton
