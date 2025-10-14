# app/intent.py
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from .openai_client import call_orchestrator, call_finance_analyst, call_research_scout

router = APIRouter()

ASST_ORCHESTRATOR_ID = os.getenv("ASST_ORCHESTRATOR_ID", "")
ASST_FINANCE_ANALYST_ID = os.getenv("ASST_FINANCE_ANALYST_ID", "")
ASST_RESEARCH_SCOUT_ID = os.getenv("ASST_RESEARCH_SCOUT_ID", "")

class IntentRequest(BaseModel):
    intent: str
    company_id: Optional[str] = "demo"
    input: Optional[Dict[str, Any]] = None

def _normalize_opportunities(result: Dict[str, Any]) -> Dict[str, Any]:
    k = result.get("kpis") or {}
    items = result.get("items") or []
    fixed: List[Dict[str, Any]] = []
    for it in items:
        fixed.append({
            "title": it.get("title") or it.get("name") or "Untitled",
            "category": it.get("category") or it.get("kind") or "other",
            "date": it.get("date"),
            "deadline": it.get("deadline") or it.get("due"),
            "fit_score": it.get("fit_score"),
            "roi_est": it.get("roi_est") or it.get("roi"),
            "weather": it.get("weather"),
            "link": it.get("link") or it.get("url"),
        })
    result["kpis"] = {
        "active_count": k.get("active_count"),
        "potential_value": k.get("potential_value"),
        "avg_fit_score": k.get("avg_fit_score"),
        "event_readiness": k.get("event_readiness"),
        "historical_roi": k.get("historical_roi"),
    }
    result["items"] = fixed
    return result

def _demo_opportunities(region: str) -> Dict[str, Any]:
    kpis = {
        "active_count": 5,
        "potential_value": 320000,
        "avg_fit_score": 0.76,
        "event_readiness": 0.68,
        "historical_roi": 0.21,
    }
    insights = [
        f"Severe heat forecast expected near {region} may boost HVAC service demand in the next 10 days.",
        "Local utility efficiency rebates open for SMB retrofits; average award $3k–$12k.",
        "Two city RFPs closing within 14 days; consider partnering to improve award odds.",
    ]
    items = [
        {"title": "City Facilities HVAC Preventive Contract", "category": "bid", "date": "2025-10-18", "deadline": "2025-10-25", "fit_score": 0.83, "roi_est": 0.34, "link": "https://example.gov/rfp/hvac-preventive"},
        {"title": "Austin Energy Small Business Efficiency Rebate", "category": "grant", "deadline": "2025-11-05", "fit_score": 0.71, "roi_est": 0.28, "link": "https://austinenergy.com/rebates/smb"},
        {"title": "Regional Contractor Networking Night", "category": "event", "date": "2025-10-22", "fit_score": 0.62, "roi_est": 0.12, "link": "https://example.com/events/regional-contractors"},
        {"title": "Supplier Bulk Filter Promo (Q4)", "category": "partner", "deadline": "2025-10-30", "fit_score": 0.66, "roi_est": 0.17, "link": "https://supplier.example.com/promos/q4-filters"},
        {"title": "Hot Weather Alert — Load Spike", "category": "weather", "date": "2025-10-20", "fit_score": 0.80, "roi_est": 0.10, "weather": "Heat index >100°F"},
    ]
    visuals = [{"type": "bar", "title": "Potential Value by Category", "labels": ["bid", "grant", "event", "partner", "weather"], "values": [180000, 65000, 10000, 45000, 20000]}]
    return _normalize_opportunities({"kpis": kpis, "insights": insights, "items": items, "visuals": visuals, "assumptions": {"company_id": "demo", "inputs": {"region": region}}})

@router.post("/api/intent")
async def intent_router(req: IntentRequest):
    intent = (req.intent or "").strip().lower()
    company_id = req.company_id or "demo"
    input_data = req.input or {}

    # ---- Opportunities (Orchestrator → Research Scout under the hood) ----
    if intent == "opportunities":
        region = str(input_data.get("region") or "Austin, TX")
        if ASST_ORCHESTRATOR_ID:
            try:
                ai = await call_orchestrator(intent="opportunities", company_id=company_id, input_data=input_data)
                return {"intent": intent, "company_id": company_id, "result": _normalize_opportunities(ai)}
            except Exception as e:
                demo = _demo_opportunities(region)
                return {"intent": intent, "company_id": company_id, "result": demo, "warning": f"assistant_error: {e}"}
        return {"intent": intent, "company_id": company_id, "result": _demo_opportunities(region)}

    # ---- Financial overview (uses Finance Analyst if you want via intent) ----
    if intent == "render_financial_overview":
        if ASST_FINANCE_ANALYST_ID:
            try:
                ai = await call_finance_analyst(company_id=company_id, periods=int(input_data.get("periods", 12)))
                # You can also normalize here if you want a strict envelope shape.
                return {"intent": intent, "company_id": company_id, "result": ai}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"finance_analyst_error: {e}")
        # If not configured, tell caller to hit /api/overview (your deterministic backend math)
        raise HTTPException(status_code=400, detail="Finance Analyst assistant not configured; use /api/overview")

    # ---- Ad-hoc research (direct Research Scout) ----
    if intent == "research_digest":
        if ASST_RESEARCH_SCOUT_ID:
            q = str(input_data.get("query") or "industry updates")
            region = input_data.get("region")
            try:
                ai = await call_research_scout(q, company_id=company_id, region=region)
                return {"intent": intent, "company_id": company_id, "result": ai}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"research_scout_error: {e}")
        raise HTTPException(status_code=400, detail="Research Scout assistant not configured")

    raise HTTPException(status_code=400, detail=f"Unknown intent: {intent}")
