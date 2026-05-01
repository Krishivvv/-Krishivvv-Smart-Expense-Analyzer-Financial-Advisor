import os
import sys
from contextlib import asynccontextmanager

# Ensure backend dir is in path so router imports work
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base, SessionLocal
import models  # noqa: F401  (ensures models are registered with Base)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    Base.metadata.create_all(bind=engine)

    # Seed if empty
    db = SessionLocal()
    try:
        count = db.query(models.Expense).count()
        if count == 0:
            print("[startup] Empty DB - seeding...")
            from seed import seed_database
            seed_database()
        else:
            print(f"[startup] DB has {count} expenses.")
    finally:
        db.close()

    # Train ML models (best-effort; app still works without)
    try:
        from ml.categorizer import get_categorizer
        from ml.anomaly_detector import get_anomaly_detector
        from ml.forecaster import get_forecaster
        get_categorizer()
        get_anomaly_detector()
        get_forecaster()
        print("[startup] ML models initialised.")
    except Exception as e:
        print(f"[startup] ML init warning: {e}")

    yield


app = FastAPI(title="Smart Expense Analyzer API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "Smart Expense Analyzer API", "status": "ok", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Routers — import lazily after app construction
from routers import expenses as expenses_router
from routers import analytics as analytics_router
from routers import advisor as advisor_router
from routers import upload as upload_router

app.include_router(expenses_router.router, prefix="/api")
app.include_router(analytics_router.router, prefix="/api")
app.include_router(advisor_router.router, prefix="/api")
app.include_router(upload_router.router, prefix="/api")
