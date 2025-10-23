# app/routers/ai_tabs.py
"""
Unified router for all /api/ai/* tab endpoints with demo mode support.
When company_id='demo', returns deterministic seed data without calling external APIs.
"""
import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from ..utils_demo import is_demo, meta
from ..demo_seed import (
    DEMO_SCENARIOS_FULL,
    DEMO_OPPORTUNITIES_FULL,
    DEMO_DEMAND_FULL,
    DEMO_REVIEWS_FULL,
    DEMO_HEALTH_FULL,
    DEMO_DEBT_FULL,
    DEMO_TAX_FULL,
    DEMO_ASSETS_FULL,
    DEMO_INVENTORY_FULL,
)

router = APIRouter()

DEV_NONDEMO_STUB = os.getenv("DEV_NONDEMO_STUB", "false").lower() == "true"


# -----------------------------------------------------------------------------
# Request Models
# -----------------------------------------------------------------------------
class TabRequest(BaseModel):
    company_id: Optional[str] = "demo"
    range: Optional[str] = "30d"
    include_details: Optional[bool] = True


# -----------------------------------------------------------------------------
# Helper: Non-demo stub response
# -----------------------------------------------------------------------------
def nondemo_stub(endpoint: str, company_id: str) -> dict:
    """Returns a safe stub when DEV_NONDEMO_STUB=true and not in demo mode."""
    return {
        "company_id": company_id,
        "endpoint": endpoint,
        "message": "Non-demo stub (DEV_NONDEMO_STUB=true)",
        "kpis": {},
        "insights": [],
        "_meta": {"demo": False, "stub": True},
    }


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.post("/api/ai/scenarios/full")
async def scenarios_full(req: TabRequest):
    """
    Scenario planning full analysis.
    Demo: returns seed data. Non-demo: current logic or stub.
    """
    if is_demo(req.company_id):
        response = DEMO_SCENARIOS_FULL.copy()
        response["company_id"] = req.company_id
        return meta(response)
    
    if DEV_NONDEMO_STUB:
        return nondemo_stub("/api/ai/scenarios/full", req.company_id)
    
    # TODO: Call existing scenario planning logic
    # from ..services.scenario_planning import compute_scenario_lab_analysis
    # return compute_scenario_lab_analysis(...)
    return {"error": "Non-demo implementation pending", "_meta": {"demo": False}}


@router.post("/api/ai/opportunities/full")
async def opportunities_full(req: TabRequest):
    """
    Opportunities discovery full analysis.
    Demo: returns seed data. Non-demo: current logic or stub.
    """
    if is_demo(req.company_id):
        response = DEMO_OPPORTUNITIES_FULL.copy()
        response["company_id"] = req.company_id
        return meta(response)
    
    if DEV_NONDEMO_STUB:
        return nondemo_stub("/api/ai/opportunities/full", req.company_id)
    
    # TODO: Call existing opportunities logic if available
    return {"error": "Non-demo implementation pending", "_meta": {"demo": False}}


@router.post("/api/ai/demand/full")
async def demand_full(req: TabRequest):
    """
    Demand forecasting full analysis.
    Demo: returns seed data. Non-demo: current logic or stub.
    """
    if is_demo(req.company_id):
        response = DEMO_DEMAND_FULL.copy()
        response["company_id"] = req.company_id
        return meta(response)
    
    if DEV_NONDEMO_STUB:
        return nondemo_stub("/api/ai/demand/full", req.company_id)
    
    # TODO: Call existing demand forecasting logic if available
    return {"error": "Non-demo implementation pending", "_meta": {"demo": False}}


@router.post("/api/ai/reviews/full")
async def reviews_full(req: TabRequest):
    """
    Reviews analysis full data.
    Demo: returns seed data. Non-demo: current logic or stub.
    """
    if is_demo(req.company_id):
        response = DEMO_REVIEWS_FULL.copy()
        response["company_id"] = req.company_id
        return meta(response)
    
    if DEV_NONDEMO_STUB:
        return nondemo_stub("/api/ai/reviews/full", req.company_id)
    
    # TODO: Call existing reviews analysis logic if available
    return {"error": "Non-demo implementation pending", "_meta": {"demo": False}}


@router.post("/api/ai/health/full")
async def health_full(req: TabRequest):
    """
    Business health score full analysis.
    Demo: returns seed data. Non-demo: current logic or stub.
    """
    if is_demo(req.company_id):
        response = DEMO_HEALTH_FULL.copy()
        response["company_id"] = req.company_id
        return meta(response)
    
    if DEV_NONDEMO_STUB:
        return nondemo_stub("/api/ai/health/full", req.company_id)
    
    # TODO: Call existing health score logic if available
    return {"error": "Non-demo implementation pending", "_meta": {"demo": False}}


@router.post("/api/ai/inventory/full")
async def inventory_full(req: TabRequest):
    """
    Inventory management full analysis.
    Demo: returns seed data. Non-demo: current logic or stub.
    """
    if is_demo(req.company_id):
        response = DEMO_INVENTORY_FULL.copy()
        response["company_id"] = req.company_id
        return meta(response)
    
    if DEV_NONDEMO_STUB:
        return nondemo_stub("/api/ai/inventory/full", req.company_id)
    
    # TODO: Call existing inventory management logic if available
    return {"error": "Non-demo implementation pending", "_meta": {"demo": False}}
