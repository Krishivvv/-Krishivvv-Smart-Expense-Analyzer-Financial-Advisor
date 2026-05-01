"""Rule-based + statistical financial advisor engine."""
from datetime import datetime
from typing import List, Optional
import pandas as pd


class FinancialAdvisor:
    INCOME_MULTIPLIER = 2.5  # assume monthly income ~ total_spend * 2.5

    def analyze(self, expenses_df: pd.DataFrame, budgets: Optional[list] = None) -> dict:
        if expenses_df is None or expenses_df.empty:
            return self._empty_result()

        df = expenses_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        df["category"] = df["category"].fillna("Others")

        now = datetime.utcnow()
        cur_year, cur_month = now.year, now.month
        last_year = cur_year if cur_month > 1 else cur_year - 1
        last_month = cur_month - 1 if cur_month > 1 else 12

        cur_df = df[(df["year"] == cur_year) & (df["month"] == cur_month)]
        prev_df = df[(df["year"] == last_year) & (df["month"] == last_month)]

        total_cur = float(cur_df["amount"].sum())
        total_prev = float(prev_df["amount"].sum())
        avg_daily = total_cur / max(now.day, 1)

        if not cur_df.empty:
            highest_cat = cur_df.groupby("category")["amount"].sum().idxmax()
        else:
            highest_cat = "—"

        income_estimate = max(total_cur * self.INCOME_MULTIPLIER, 1.0)

        # Build budget map
        budget_map = {}
        if budgets:
            cur_month_str = f"{cur_year:04d}-{cur_month:02d}"
            for b in budgets:
                if getattr(b, "month", None) == cur_month_str:
                    budget_map[b.category] = float(b.monthly_limit)

        advice: List[dict] = []
        budget_alerts: List[dict] = []
        top_insights: List[str] = []
        savings_potential = 0.0

        # Per-category share of spend
        cat_totals = cur_df.groupby("category")["amount"].sum().to_dict() if not cur_df.empty else {}

        # Rule 1: Food > 30% of (estimated) income
        food = cat_totals.get("Food", 0.0)
        if food > 0 and food / income_estimate > 0.30:
            advice.append({
                "type": "warning",
                "title": "High food spending",
                "detail": (f"You're spending ₹{food:,.0f} on Food this month — "
                           f"{food/income_estimate*100:.0f}% of estimated income. "
                           f"Consider home-cooked meals to save ₹{food*0.3:,.0f}/month."),
                "impact": "high",
                "category": "Food",
            })

        # Rule 2: Entertainment > 15% of income
        ent = cat_totals.get("Entertainment", 0.0)
        if ent > 0 and ent / income_estimate > 0.15:
            advice.append({
                "type": "warning",
                "title": "Entertainment overspend",
                "detail": (f"Entertainment is ₹{ent:,.0f} ({ent/income_estimate*100:.0f}% of income). "
                           f"Try cutting one subscription or outing per week."),
                "impact": "medium",
                "category": "Entertainment",
            })

        # Rule 3: No health spending → suggest checkup
        if cat_totals.get("Health", 0.0) == 0:
            advice.append({
                "type": "tip",
                "title": "Build a health buffer",
                "detail": "No health expenses logged this month. Consider an annual checkup and an emergency health fund of at least ₹10,000.",
                "impact": "medium",
                "category": "Health",
            })

        # Rule 4: month-over-month change > 20%
        if total_prev > 0:
            change = (total_cur - total_prev) / total_prev * 100.0
            if change > 20:
                advice.append({
                    "type": "warning",
                    "title": "Spending up sharply",
                    "detail": f"Total spending up {change:.1f}% vs last month (₹{total_prev:,.0f} → ₹{total_cur:,.0f}). Review the top categories.",
                    "impact": "high",
                    "category": None,
                })
            elif change < -10:
                advice.append({
                    "type": "achievement",
                    "title": "Great progress!",
                    "detail": f"You're spending {abs(change):.1f}% less than last month. Keep it up — you saved ₹{total_prev - total_cur:,.0f}.",
                    "impact": "high",
                    "category": None,
                })

        # Rule 5: budget breaches
        for cat, limit in budget_map.items():
            spent = cat_totals.get(cat, 0.0)
            if limit > 0 and spent > limit:
                overage_pct = (spent - limit) / limit * 100.0
                budget_alerts.append({
                    "category": cat,
                    "limit": round(limit, 2),
                    "spent": round(spent, 2),
                    "overage_pct": round(overage_pct, 1),
                    "severity": "high" if overage_pct > 50 else "medium",
                })
                advice.append({
                    "type": "warning",
                    "title": f"{cat} budget exceeded",
                    "detail": f"You've spent ₹{spent:,.0f} of ₹{limit:,.0f} ({overage_pct:+.1f}%). Pause non-essentials in this category.",
                    "impact": "high",
                    "category": cat,
                })
            elif limit > 0 and spent > 0.85 * limit:
                budget_alerts.append({
                    "category": cat,
                    "limit": round(limit, 2),
                    "spent": round(spent, 2),
                    "overage_pct": round((spent / limit - 1) * 100.0, 1),
                    "severity": "low",
                })

        # Rule 6: decreasing trend achievement (handled in rule 4)

        # Rule 7: savings potential — categories whose monthly amount > category historical avg by >20%
        if not df.empty:
            historical = df.groupby(["year", "month", "category"])["amount"].sum().reset_index()
            for cat, cur_amt in cat_totals.items():
                hist_for_cat = historical[
                    (historical["category"] == cat) &
                    ~((historical["year"] == cur_year) & (historical["month"] == cur_month))
                ]["amount"]
                if len(hist_for_cat) > 0:
                    avg = float(hist_for_cat.mean())
                    if cur_amt > avg * 1.20:
                        savings_potential += (cur_amt - avg)

        # Rule 8: Generate generic tips based on patterns
        if cat_totals:
            top_cat = max(cat_totals, key=cat_totals.get)
            top_amt = cat_totals[top_cat]
            advice.append({
                "type": "tip",
                "title": f"Watch your {top_cat} spending",
                "detail": f"{top_cat} is your largest category at ₹{top_amt:,.0f}. Setting a hard monthly cap can help.",
                "impact": "medium",
                "category": top_cat,
            })

        if avg_daily > 0:
            advice.append({
                "type": "tip",
                "title": "Daily pace check",
                "detail": f"You're averaging ₹{avg_daily:,.0f}/day. A daily budget mindset can help you stay on track.",
                "impact": "low",
                "category": None,
            })

        # Anomaly count nudge
        if "is_anomaly" in df.columns:
            anom = int(cur_df["is_anomaly"].sum()) if "is_anomaly" in cur_df.columns else 0
            if anom > 0:
                advice.append({
                    "type": "warning",
                    "title": f"{anom} unusual transaction(s) this month",
                    "detail": "Check the Analytics page for details — review whether these were planned.",
                    "impact": "medium",
                    "category": None,
                })

        # Health score: penalise overshooting categories, reward declining spend
        health_score = self._compute_health_score(
            cat_totals, budget_map, total_cur, total_prev, avg_daily, income_estimate
        )

        # Top insights
        if total_prev > 0:
            change = (total_cur - total_prev) / total_prev * 100.0
            top_insights.append(f"Spending change vs last month: {change:+.1f}%")
        if cat_totals:
            top_cat = max(cat_totals, key=cat_totals.get)
            top_insights.append(f"Top category: {top_cat} (₹{cat_totals[top_cat]:,.0f})")
        if budget_alerts:
            top_insights.append(f"{len(budget_alerts)} budget(s) close to or over limit")
        if savings_potential > 0:
            top_insights.append(f"Potential savings: ₹{savings_potential:,.0f}/month")

        return {
            "overall_health_score": int(health_score),
            "health_label": self._label_for_score(health_score),
            "monthly_summary": {
                "total_spent": round(total_cur, 2),
                "total_last_month": round(total_prev, 2),
                "avg_daily": round(avg_daily, 2),
                "highest_category": highest_cat,
                "transaction_count": int(len(cur_df)),
            },
            "advice": advice[:10],
            "savings_potential": round(savings_potential, 2),
            "budget_alerts": budget_alerts,
            "top_insights": top_insights,
        }

    def _compute_health_score(self, cat_totals, budget_map, total_cur, total_prev, avg_daily, income_estimate) -> int:
        score = 100

        # Budget breaches: -15 each (capped)
        breaches = sum(
            1 for cat, lim in budget_map.items()
            if cat_totals.get(cat, 0) > lim and lim > 0
        )
        score -= min(breaches * 15, 45)

        # Spending up vs last month
        if total_prev > 0:
            change = (total_cur - total_prev) / total_prev
            if change > 0.20:
                score -= 15
            elif change > 0.10:
                score -= 8
            elif change < -0.10:
                score += 5

        # Food / entertainment ratios
        if income_estimate > 0:
            if cat_totals.get("Food", 0) / income_estimate > 0.30:
                score -= 10
            if cat_totals.get("Entertainment", 0) / income_estimate > 0.15:
                score -= 8

        # No health spending
        if cat_totals.get("Health", 0) == 0:
            score -= 5

        return max(0, min(100, score))

    def _label_for_score(self, score: int) -> str:
        if score >= 80:
            return "Excellent"
        if score >= 65:
            return "Good"
        if score >= 45:
            return "Fair"
        return "Poor"

    def _empty_result(self) -> dict:
        return {
            "overall_health_score": 70,
            "health_label": "Good",
            "monthly_summary": {
                "total_spent": 0.0,
                "total_last_month": 0.0,
                "avg_daily": 0.0,
                "highest_category": "—",
                "transaction_count": 0,
            },
            "advice": [{
                "type": "tip",
                "title": "Start tracking",
                "detail": "Add expenses or upload a CSV to get personalised advice.",
                "impact": "low",
                "category": None,
            }],
            "savings_potential": 0.0,
            "budget_alerts": [],
            "top_insights": ["No data yet. Upload a CSV or add expenses to begin."],
        }
