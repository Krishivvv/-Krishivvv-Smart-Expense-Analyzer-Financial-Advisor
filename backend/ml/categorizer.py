"""Expense auto-categorization model.

TF-IDF + RandomForest, with a keyword rule fallback for short / unseen text.
"""
import os
import re
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline


CATEGORIES = [
    "Food", "Transport", "Shopping", "Utilities", "Entertainment",
    "Health", "Education", "Rent", "Groceries", "Others",
]


KEYWORDS = {
    "Food": [
        "food", "restaurant", "cafe", "zomato", "swiggy", "lunch", "dinner",
        "breakfast", "pizza", "burger", "biryani", "snacks", "tea", "coffee",
        "mcdonald", "kfc", "domino", "subway",
    ],
    "Transport": [
        "uber", "ola", "petrol", "fuel", "bus", "metro", "train", "auto",
        "rickshaw", "rapido", "taxi", "transport", "parking", "toll",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "clothes", "shoes", "shirt", "watch",
        "shopping", "h&m", "decathlon", "ikea", "headphones", "backpack",
        "phone case", "bata",
    ],
    "Utilities": [
        "electricity", "wifi", "internet", "water", "bill", "recharge", "mobile",
        "gas", "cylinder", "dth", "maintenance", "society",
    ],
    "Entertainment": [
        "movie", "netflix", "spotify", "game", "concert", "pvr", "bookmyshow",
        "hotstar", "prime", "disney", "bowling", "amusement",
    ],
    "Health": [
        "doctor", "medicine", "pharmacy", "hospital", "apollo", "gym",
        "dental", "eye", "checkup", "vitamins", "supplement", "clinic",
    ],
    "Education": [
        "course", "book", "tuition", "college", "school", "coursera", "udemy",
        "stationery", "notebook", "fees", "engineering",
    ],
    "Rent": ["rent", "pg", "hostel", "flat"],
    "Groceries": [
        "grocery", "vegetables", "fruits", "kirana", "bigbasket", "dmart",
        "reliance fresh", "spencer", "jiomart", "milk", "bread",
    ],
    "Others": [
        "salon", "gift", "donation", "laundry", "haircut", "miscellaneous",
    ],
}


_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
_MODEL_PATH = os.path.join(_MODELS_DIR, "categorizer.pkl")


def _normalise(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _rule_based_predict(description: str) -> tuple[str, float]:
    norm = _normalise(description)
    best_cat = "Others"
    best_score = 0
    for cat, kws in KEYWORDS.items():
        for kw in kws:
            if kw in norm:
                score = len(kw)  # longer keywords = stronger match
                if score > best_score:
                    best_cat = cat
                    best_score = score
    confidence = min(0.6 + best_score / 50.0, 0.95) if best_score > 0 else 0.3
    return best_cat, confidence


class ExpenseCategorizer:
    def __init__(self):
        self.pipeline: Optional[Pipeline] = None
        self.classes_: Optional[list] = None
        self.is_trained = False

    def train(self, expenses_df: pd.DataFrame):
        """Train on description -> category. Falls back gracefully if data is sparse."""
        if expenses_df is None or expenses_df.empty:
            print("[categorizer] No data to train on, using rule-based only.")
            return

        df = expenses_df.copy()
        df = df[df["category"].notna()]
        df = df[df["description"].notna()]
        if len(df) < 5:
            print("[categorizer] Too few rows, using rule-based only.")
            return

        X = df["description"].astype(str).map(_normalise).tolist()
        y = df["category"].astype(str).tolist()

        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=500, ngram_range=(1, 2))),
            ("clf", RandomForestClassifier(n_estimators=100, random_state=42)),
        ])

        try:
            pipeline.fit(X, y)
            self.pipeline = pipeline
            self.classes_ = list(pipeline.named_steps["clf"].classes_)
            self.is_trained = True
            os.makedirs(_MODELS_DIR, exist_ok=True)
            joblib.dump({"pipeline": pipeline, "classes": self.classes_}, _MODEL_PATH)
            print(f"[categorizer] Trained on {len(df)} rows -> {len(self.classes_)} classes")
        except Exception as e:
            print(f"[categorizer] Training failed: {e}")

    def load(self) -> bool:
        if not os.path.exists(_MODEL_PATH):
            return False
        try:
            blob = joblib.load(_MODEL_PATH)
            self.pipeline = blob["pipeline"]
            self.classes_ = blob["classes"]
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[categorizer] Load failed: {e}")
            return False

    def predict(self, description: str) -> dict:
        norm = _normalise(description)

        # Rule-based first if obvious
        rule_cat, rule_conf = _rule_based_predict(description)

        # ML if trained
        if self.is_trained and self.pipeline is not None and norm:
            try:
                proba = self.pipeline.predict_proba([norm])[0]
                idx_sorted = np.argsort(proba)[::-1]
                top_cat = self.classes_[idx_sorted[0]]
                top_conf = float(proba[idx_sorted[0]])

                alternatives = []
                for i in idx_sorted[1:4]:
                    alternatives.append({
                        "category": self.classes_[i],
                        "confidence": round(float(proba[i]), 3),
                    })

                # Combine: if rule confidence is much higher, prefer rule
                if rule_conf > top_conf and rule_conf > 0.7:
                    return {
                        "category": rule_cat,
                        "confidence": round(rule_conf, 3),
                        "alternatives": [{"category": top_cat, "confidence": round(top_conf, 3)}] + alternatives[:2],
                    }

                return {
                    "category": top_cat,
                    "confidence": round(top_conf, 3),
                    "alternatives": alternatives,
                }
            except Exception as e:
                print(f"[categorizer] Predict failed: {e}")

        return {
            "category": rule_cat,
            "confidence": round(rule_conf, 3),
            "alternatives": [],
        }

    def get_category_keywords(self) -> dict:
        return KEYWORDS


_singleton: Optional[ExpenseCategorizer] = None


def get_categorizer() -> Optional[ExpenseCategorizer]:
    global _singleton
    if _singleton is not None:
        return _singleton

    cat = ExpenseCategorizer()
    if not cat.load():
        # Train from DB + CSV
        try:
            from database import SessionLocal
            import models as m
            db = SessionLocal()
            try:
                rows = db.query(m.Expense).all()
                if rows:
                    df = pd.DataFrame([
                        {"description": r.description, "category": r.category}
                        for r in rows if r.category
                    ])
                else:
                    df = pd.DataFrame(columns=["description", "category"])
            finally:
                db.close()

            # Augment with CSV training data
            csv_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "sample_expenses.csv"
            )
            if os.path.exists(csv_path):
                csv_df = pd.read_csv(csv_path)
                if {"description", "category"}.issubset(csv_df.columns):
                    df = pd.concat([df, csv_df[["description", "category"]]], ignore_index=True)

            cat.train(df)
        except Exception as e:
            print(f"[categorizer] Auto-train failed: {e}")

    _singleton = cat
    return _singleton
