"""Seed the database with realistic Indian expense data."""
import random
from datetime import datetime, timedelta

from database import engine, SessionLocal, Base
import models


CATEGORIES = [
    "Food", "Transport", "Shopping", "Utilities", "Entertainment",
    "Health", "Education", "Rent", "Groceries", "Others"
]

PAYMENT_METHODS = ["upi", "card", "cash"]

# (description, category, low, high) — typical INR ranges
EXPENSE_TEMPLATES = [
    # Food
    ("Lunch at Cafe Coffee Day", "Food", 200, 600),
    ("Zomato order - Biryani", "Food", 250, 700),
    ("Swiggy - Pizza", "Food", 300, 800),
    ("Dinner at restaurant", "Food", 400, 1500),
    ("McDonald's meal", "Food", 200, 500),
    ("Tea and snacks", "Food", 50, 150),
    ("Breakfast at hotel", "Food", 100, 350),
    # Transport
    ("Uber to office", "Transport", 100, 400),
    ("Ola ride home", "Transport", 80, 350),
    ("Petrol fill-up", "Transport", 800, 2500),
    ("Metro card recharge", "Transport", 200, 600),
    ("Bus pass", "Transport", 100, 500),
    ("Train ticket", "Transport", 150, 1200),
    # Shopping
    ("Amazon order - Headphones", "Shopping", 800, 4000),
    ("Flipkart - Clothes", "Shopping", 500, 3000),
    ("Myntra T-shirt", "Shopping", 400, 1500),
    ("Shoes from Bata", "Shopping", 1200, 4500),
    ("Watch from Titan", "Shopping", 1500, 8000),
    # Utilities
    ("Electricity bill", "Utilities", 800, 2500),
    ("Water bill", "Utilities", 200, 600),
    ("Wifi internet bill", "Utilities", 500, 1500),
    ("Mobile recharge", "Utilities", 200, 800),
    ("Gas cylinder", "Utilities", 800, 1100),
    # Entertainment
    ("Movie tickets - PVR", "Entertainment", 300, 1200),
    ("Netflix subscription", "Entertainment", 199, 649),
    ("Spotify premium", "Entertainment", 119, 199),
    ("Game purchase Steam", "Entertainment", 500, 3000),
    ("Concert ticket", "Entertainment", 800, 4000),
    # Health
    ("Doctor consultation", "Health", 300, 1500),
    ("Medicine from pharmacy", "Health", 100, 800),
    ("Apollo hospital visit", "Health", 500, 3000),
    ("Gym membership", "Health", 800, 2500),
    # Education
    ("Coursera course", "Education", 500, 4000),
    ("Engineering book", "Education", 300, 1200),
    ("Tuition fees", "Education", 1500, 8000),
    ("Stationery", "Education", 100, 500),
    # Rent
    ("Monthly rent PG", "Rent", 6000, 18000),
    ("Hostel fees", "Rent", 4000, 12000),
    # Groceries
    ("BigBasket grocery order", "Groceries", 800, 3500),
    ("Kirana store - vegetables", "Groceries", 200, 1000),
    ("Fruits from market", "Groceries", 150, 600),
    ("Reliance Fresh shopping", "Groceries", 500, 2500),
    # Others
    ("Salon haircut", "Others", 150, 800),
    ("Gift for friend", "Others", 300, 2000),
    ("Donation", "Others", 100, 1000),
]

# Anomaly templates - unusually high amounts
ANOMALY_TEMPLATES = [
    ("Emergency hospital bill", "Health", 15000, 35000),
    ("Surprise birthday party", "Entertainment", 8000, 18000),
    ("Wedding gift purchase", "Shopping", 12000, 25000),
    ("Laptop purchase", "Shopping", 45000, 80000),
    ("Family dinner at 5-star", "Food", 5000, 12000),
]


def seed_database(force: bool = False):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(models.Expense).count()
        if existing > 0 and not force:
            print(f"[seed] DB already has {existing} expenses, skipping seed.")
            return existing

        if force:
            db.query(models.Expense).delete()
            db.query(models.Budget).delete()
            db.commit()

        random.seed(42)
        today = datetime.utcnow()
        expenses_to_add = []

        # Distribute across last 3 months: ~30 current month, ~30 last month, ~20 month before that
        def pick_offset(slot: int) -> int:
            """slot 0: current month (0..28d), 1: last month (28..58d), 2: 60..90d"""
            if slot == 0:
                return random.randint(0, min(today.day, 28))
            if slot == 1:
                return random.randint(28, 58)
            return random.randint(60, 90)

        slot_counts = [30, 30, 20]
        for slot, n in enumerate(slot_counts):
            for _ in range(n):
                tpl = random.choice(EXPENSE_TEMPLATES)
                desc, cat, lo, hi = tpl
                amount = round(random.uniform(lo, hi), 2)
                days_back = pick_offset(slot)
                date = today - timedelta(days=days_back, hours=random.randint(0, 23))
                expenses_to_add.append(models.Expense(
                    description=desc,
                    amount=amount,
                    category=cat,
                    predicted_category=cat,
                    date=date,
                    is_anomaly=False,
                    payment_method=random.choice(PAYMENT_METHODS),
                    notes=None,
                ))

        # 4 obvious anomalies
        for _ in range(4):
            tpl = random.choice(ANOMALY_TEMPLATES)
            desc, cat, lo, hi = tpl
            amount = round(random.uniform(lo, hi), 2)
            days_back = random.randint(0, 60)
            date = today - timedelta(days=days_back, hours=random.randint(0, 23))
            expenses_to_add.append(models.Expense(
                description=desc,
                amount=amount,
                category=cat,
                predicted_category=cat,
                date=date,
                is_anomaly=True,
                anomaly_score=-0.6,
                payment_method=random.choice(PAYMENT_METHODS),
                notes="High value transaction",
            ))

        db.add_all(expenses_to_add)

        # Default budgets for current month
        cur_month = today.strftime("%Y-%m")
        budgets = [
            ("Food", 6000),
            ("Transport", 4000),
            ("Shopping", 5000),
            ("Utilities", 3000),
            ("Entertainment", 2000),
            ("Health", 3000),
            ("Education", 3000),
            ("Rent", 15000),
            ("Groceries", 5000),
            ("Others", 2000),
        ]
        for cat, lim in budgets:
            db.add(models.Budget(category=cat, monthly_limit=lim, month=cur_month))

        db.commit()
        print(f"[seed] Seeded {len(expenses_to_add)} expenses and {len(budgets)} budgets.")
        return len(expenses_to_add)
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    seed_database(force=force)
