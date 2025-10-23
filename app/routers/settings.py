# app/routers/settings.py
"""
Settings router for user and company preferences.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from ..utils_demo import is_demo, meta
from ..demo_seed import DEMO_SETTINGS_FULL

router = APIRouter()


class SettingsRequest(BaseModel):
    company_id: Optional[str] = "demo"


@router.post("/api/settings/full")
@router.get("/api/settings/full")
async def settings_full(req: SettingsRequest = None):
    """
    Get full settings for user and company.
    Demo: returns seed data. Non-demo: returns stub for now.
    """
    company_id = req.company_id if req else "demo"
    
    if is_demo(company_id):
        response = DEMO_SETTINGS_FULL.copy()
        return meta(response)
    
    # Non-demo stub
    return {
        "user": {"name": "User", "email": "user@example.com", "role": "owner"},
        "company": {"company_id": company_id, "name": "Company", "timezone": "America/Chicago"},
        "notifications": {},
        "integrations": [],
        "preferences": {},
        "_meta": {"demo": False, "stub": True},
    }
