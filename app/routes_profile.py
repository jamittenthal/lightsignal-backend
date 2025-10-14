# app/routes_profile.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .models import DB, OpportunityProfile

router = APIRouter()

class UpsertProfile(BaseModel):
    company_id: str
    business_type: Optional[str] = None
    region: Optional[str] = None
    radius_miles: Optional[int] = 50
    preferred_types: Optional[list[str]] = None
    budget_max: Optional[float] = None
    travel_max_miles: Optional[int] = None
    capacity_ok: Optional[bool] = True
    risk_appetite: Optional[str] = "low"

@router.get("/api/opportunity_profile/{company_id}")
async def get_profile(company_id: str):
    prof = DB["profiles"].get(company_id)
    if not prof:
        # return an empty default; UI can upsert
        prof = OpportunityProfile(company_id=company_id)
        DB["profiles"][company_id] = prof
    return prof

@router.post("/api/opportunity_profile")
async def upsert_profile(payload: UpsertProfile):
    prof = OpportunityProfile(
        company_id=payload.company_id,
        business_type=payload.business_type,
        region=payload.region,
        radius_miles=payload.radius_miles or 50,
        preferred_types=payload.preferred_types or [],
        budget_max=payload.budget_max,
        travel_max_miles=payload.travel_max_miles,
        capacity_ok=payload.capacity_ok,
        risk_appetite=payload.risk_appetite or "low",
    )
    DB["profiles"][payload.company_id] = prof
    return prof
