# app/routes_ops.py
import csv
import io
from fastapi import APIRouter, Response, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from .models import DB
from .intent import IntentRequest  # reuse schema
from .intent import intent_router   # to reach orchestrator if needed

router = APIRouter()

class SimulateRequest(BaseModel):
    company_id: str
    opportunity: Dict[str, Any]  # the card/item from UI

@router.post("/api/opportunities/simulate")
async def simulate(req: SimulateRequest):
    """
    Bridge to your scenario planner:
    - Map opportunity attributes to scenario inputs (rough stub here).
    - You can later call /api/intent with intent="scenario_chat: ..." for richer output.
    """
    title = req.opportunity.get("title", "Opportunity")
    # Example mapping
    scenario_inputs = {"title": title, "est_revenue": req.opportunity.get("estimated_value") or 0,
                       "cost":  req.opportunity.get("cost") or 0}
    # Here you could call your existing /api/scenario or an intent:
    # return await api_scenario(...)
    return {"ok": True, "scenario_inputs": scenario_inputs, "note": "wire to Scenario Lab later"}

@router.get("/api/opportunities/export.csv")
async def export_csv(company_id: str):
    arr = DB["watchlist"].get(company_id, [])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id","title","category","deadline","date","fit_score","roi_est","status","link","notes"])
    for it in arr:
        writer.writerow([it.id,it.title,it.category,it.deadline,it.date,it.fit_score,it.roi_est,it.status,it.link,it.notes or ""])
    return Response(content=output.getvalue(), media_type="text/csv")
