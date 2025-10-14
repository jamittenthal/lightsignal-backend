# app/routes_watchlist.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .models import DB, WatchItem, EngagementRecord
from datetime import datetime

router = APIRouter()

class AddWatchItem(BaseModel):
    company_id: str
    title: str
    category: str
    deadline: Optional[str] = None
    date: Optional[str] = None
    fit_score: Optional[float] = None
    roi_est: Optional[float] = None
    link: Optional[str] = None
    notes: Optional[str] = None

class UpdateWatchItem(BaseModel):
    company_id: str
    id: str
    status: Optional[str] = None
    notes: Optional[str] = None

class AddEngagement(BaseModel):
    company_id: str
    opportunity_id: str
    status: str
    cost: Optional[float] = None
    revenue: Optional[float] = None
    roi: Optional[float] = None
    event_weather: Optional[str] = None
    attended_at: Optional[str] = None

@router.get("/api/watchlist/{company_id}")
async def list_watchlist(company_id: str):
    return DB["watchlist"].get(company_id, [])

@router.post("/api/watchlist/add")
async def add_watchitem(payload: AddWatchItem):
    item = WatchItem(
        company_id=payload.company_id,
        title=payload.title,
        category=payload.category,
        deadline=payload.deadline,
        date=payload.date,
        fit_score=payload.fit_score,
        roi_est=payload.roi_est,
        link=payload.link,
        notes=payload.notes,
    )
    arr = DB["watchlist"].setdefault(payload.company_id, [])
    arr.append(item)
    return item

@router.post("/api/watchlist/update")
async def update_watchitem(payload: UpdateWatchItem):
    arr = DB["watchlist"].get(payload.company_id, [])
    for it in arr:
        if it.id == payload.id:
            if payload.status: it.status = payload.status
            if payload.notes is not None: it.notes = payload.notes
            it.updated_at = datetime.utcnow()
            return it
    raise HTTPException(status_code=404, detail="Watch item not found")

@router.get("/api/engagements/{company_id}")
async def list_engagements(company_id: str):
    return DB["engagements"].get(company_id, [])

@router.post("/api/engagements/add")
async def add_engagement(payload: AddEngagement):
    rec = EngagementRecord(**payload.dict())
    arr = DB["engagements"].setdefault(payload.company_id, [])
    arr.append(rec)
    return rec
