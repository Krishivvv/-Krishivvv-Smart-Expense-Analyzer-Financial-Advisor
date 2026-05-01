from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List


class ExpenseBase(BaseModel):
    description: str
    amount: float
    category: Optional[str] = None
    date: Optional[datetime] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    date: Optional[datetime] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None


class ExpenseRead(ExpenseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predicted_category: Optional[str] = None
    is_anomaly: bool = False
    anomaly_score: Optional[float] = None
    created_at: datetime


class BudgetBase(BaseModel):
    category: str
    monthly_limit: float
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$")


class BudgetCreate(BudgetBase):
    pass


class BudgetRead(BudgetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CategorizeRequest(BaseModel):
    description: str
    amount: Optional[float] = None


class CategorizeResponse(BaseModel):
    category: str
    confidence: float
    alternatives: List[dict] = []


class SummaryResponse(BaseModel):
    total_this_month: float
    total_last_month: float
    by_category: dict
    count: int


class AdviceItem(BaseModel):
    type: str  # warning | tip | achievement
    title: str
    detail: str
    impact: str  # high | medium | low
    category: Optional[str] = None
