# Smart Expense Analyzer + Financial Advisor

A full-stack web application that turns raw expense data into actionable financial advice. Upload or enter expenses, and the app **auto-categorizes** them with ML, **detects anomalies**, **forecasts next-month spending**, and produces a **personalised health score** with rule-based + statistical advice.

## Features

- **AI Auto-categorization** — describe an expense and a TF-IDF + RandomForest model picks one of 10 categories (with keyword fallback for unseen text)
- **Anomaly detection** — per-category z-score + IsolationForest highlight unusual transactions and explain *why*
- **Spending forecast** — per-category LinearRegression projects next month's daily spend
- **Financial Advisor** — rule-based engine produces a 0–100 health score, savings potential, budget alerts, and 3–10 personalised tips
- **Beautiful dark dashboard** — React + Tailwind + Recharts, fully responsive
- **CSV bulk upload** — drop a CSV and every row gets categorized + anomaly-checked on the fly
- **Editable monthly budgets** — alerts when you cross 85% / 100% of any category limit
- **Live ML feedback in the Add form** — debounced auto-categorize and high-amount warnings as you type

## Screenshots

> _Add screenshots of Dashboard, Analytics, Advisor, Upload, and Expenses pages here._

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, Uvicorn |
| ML | scikit-learn (TF-IDF, RandomForest, IsolationForest, LinearRegression), pandas, numpy, joblib |
| Database | SQLite (`expenses.db`) |
| Frontend | React 18, Vite, Tailwind CSS, Recharts, Axios, React Router v6, lucide-react |

## Setup

### Option 1 — One command

```bash
bash start.sh
```

This installs both backends, seeds the database, and launches the API on `:8000` and the frontend on `:5173`.

### Option 2 — Manual

**Backend**

```bash
cd backend
pip install -r requirements.txt
python seed.py        # seeds 80 normal + 4 anomalous expenses + 10 budgets
uvicorn main:app --reload --port 8000
```

**Frontend** (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173> in your browser.

ML models train automatically the first time the API starts and are cached to `backend/models/*.pkl`.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/expenses` | List expenses (`?month=YYYY-MM` filter) |
| POST | `/api/expenses` | Create expense (auto-categorized + scored) |
| GET | `/api/expenses/{id}` | Get one expense |
| PUT | `/api/expenses/{id}` | Update expense |
| DELETE | `/api/expenses/{id}` | Delete expense |
| GET | `/api/expenses/summary` | Totals by category, this/last month |
| GET | `/api/analytics/categorize?description=...` | Predict category from text |
| POST | `/api/analytics/categorize` | Same as above with body `{description, amount}` |
| GET | `/api/analytics/anomalies` | All anomalous expenses with reasons |
| GET | `/api/analytics/forecast` | Next-month forecast for every category |
| GET | `/api/analytics/forecast?category=Food` | Forecast for a single category |
| GET | `/api/analytics/summary` | Daily totals, top merchants, payment-method split, etc. |
| GET | `/api/analytics/health` | Full advisor analysis (same as `/api/advisor/advice`) |
| GET | `/api/advisor/advice` | Health score + advice + budget alerts + insights |
| GET | `/api/advisor/budget-alerts` | Just the budget alerts |
| POST | `/api/advisor/set-budget` | `{category, monthly_limit, month}` upsert |
| GET | `/api/advisor/budgets?month=YYYY-MM` | List budgets |
| POST | `/api/upload/csv` | Multipart CSV upload — bulk-import + classify |
| GET | `/api/upload/template` | Download a starter CSV |

Interactive docs available at <http://localhost:8000/docs>.

## ML models

| Model | Algorithm | Purpose |
|---|---|---|
| **Categorizer** | TF-IDF (max 500 features, 1–2 grams) → RandomForest (100 trees) | Predict expense category from description text. Keyword rules act as fallback and as a tie-breaker for very confident matches. |
| **Anomaly detector** | Per-category z-score (mean + 2.5σ) + IsolationForest on `[amount, weekday, day_of_month]` (5% contamination) | Flag transactions that are far from the user's normal pattern. Severity is derived from how many times the category mean is exceeded. |
| **Forecaster** | One LinearRegression per category, trained on `(day_index → daily total)` | Project next-month daily spend per category and infer trend (increasing / decreasing / stable) from the slope. |
| **Advisor** | Rule + statistical engine | Combines the above with monthly comparisons, budget tracking, and >20% over-trend detection to produce a health score and a ranked list of tips, warnings, and achievements. |

All models train on the seed data + `backend/data/sample_expenses.csv` and persist to `backend/models/`. Re-train at any time by deleting `backend/models/*.pkl` and restarting.

## Uploading a CSV

1. Go to **Upload CSV** in the sidebar.
2. Click **Download CSV template** — minimum required columns: `description`, `amount`. Optional: `category`, `date`, `payment_method`.
3. Drag your file in or click to browse.
4. Hit **Upload & Analyze**. You'll see how many were inserted, how many anomalies were detected, and a per-category breakdown.

## Project structure

```
smart-expense-analyzer/
├── backend/
│   ├── main.py                FastAPI app + lifespan (creates DB, seeds, trains ML)
│   ├── database.py            SQLAlchemy engine + session
│   ├── models.py              ORM: Expense, Budget
│   ├── schemas.py             Pydantic v2 schemas
│   ├── seed.py                Seeder (84 expenses, 10 budgets, 4 anomalies)
│   ├── routers/
│   │   ├── expenses.py        CRUD + per-month summary
│   │   ├── analytics.py       Categorize, anomalies, forecast, summary, health
│   │   ├── advisor.py         Advice, budget alerts, set-budget
│   │   └── upload.py          CSV upload + template download
│   ├── ml/
│   │   ├── categorizer.py     TF-IDF + RandomForest + keyword rules
│   │   ├── anomaly_detector.py  Z-score + IsolationForest
│   │   ├── forecaster.py      Per-category LinearRegression
│   │   └── advisor_engine.py  Rule-based health analysis
│   ├── data/sample_expenses.csv  (~100 demo rows for ML training)
│   ├── requirements.txt
│   └── models/                (pickled models — created at runtime)
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx, App.jsx
│   │   ├── api/client.js      Axios instance with /api baseURL
│   │   ├── pages/             Dashboard, Expenses, Analytics, Advisor, Upload
│   │   ├── components/        Navbar, ExpenseCard, CategoryBadge, AnomalyAlert, SpendingChart, ForecastChart, BudgetMeter, AdviceCard, StatCard
│   │   └── hooks/useExpenses.js
│   ├── index.html, vite.config.js, tailwind.config.js, postcss.config.js, package.json
│
├── README.md
└── start.sh                   One-command launcher
```

## Notes & gotchas

- The "income" used by the advisor's percentage rules is **estimated** as `total_monthly_spend × 2.5`. Replace this with a real income field if you need accurate ratios.
- Currency is INR (₹) — strings only, no currency conversion.
- SQLite is intentional for sprint speed; swap to Postgres by changing `DATABASE_URL` in `database.py` (the rest of the code is engine-agnostic).
- Seed dates are anchored to "today" (`datetime.utcnow()`) so the dashboard always has fresh current-month, last-month, and trailing-90-day data on first launch.
