# app/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

# ---------- Opportunity Profile ----------
class OpportunityProfile(BaseModel):
    company_id: str
    business_type: Optional[str] = None
    region: Optional[str] = None
    radius_miles: Optional[int] = 50
    preferred_types: List[str] = Field(default_factory=list)  # ["bid","grant","event","partner","weather","lead"]
    budget_max: Optional[float] = None
    travel_max_miles: Optional[int] = None
    capacity_ok: Optional[bool] = True
    risk_appetite: Optional[str] = "low"  # "low" | "medium" | "high"
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ---------- Watchlist ----------
class WatchItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    company_id: str
    title: str
    category: str
    deadline: Optional[str] = None
    date: Optional[str] = None
    fit_score: Optional[float] = None
    roi_est: Optional[float] = None
    link: Optional[str] = None
    status: str = "Open"  # Open | Applied | Attended | Won | Lost | Closed
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ---------- Tracking snapshot (for performance analytics) ----------
class EngagementRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    company_id: str
    opportunity_id: str
    status: str
    cost: Optional[float] = None
    revenue: Optional[float] = None
    roi: Optional[float] = None
    event_weather: Optional[str] = None
    attended_at: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ---------- In-memory stores (swap to DB later) ----------
DB: Dict[str, Any] = {
    "profiles": {},            # key: company_id -> OpportunityProfile
    "watchlist": {},           # key: company_id -> List[WatchItem]
    "engagements": {},         # key: company_id -> List[EngagementRecord]
}
