# app/intent.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter()

# ---------- Schemas for request/response ----------

class IntentRequest(BaseModel):
    intent: str
    company_id: Optional[str] = "demo"
    input: Optional[Dict[str, Any]] = None

# ---------- Normalizers and demo builders ----------

def _normalize_opportunities(result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize keys to match the UI in app/opportunities/page.tsx."""
    k = result.get("kpis") or {}
    items = result.get("items") or []

    fixed_items: List[Dict[str, Any]] = []
    for it in items:
        fixed_items.append({
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
    result["items"] = fixed_items
    return result

def _build_demo_opportunities(region: str) -> Dict[str, Any]:
    """Deterministic demo payload that matches your UI types.
    TODO: Replace this with a call to your Orchestrator/Research Scout Assistant.
    """
    kpis = {
        "active_count": 5,
        "potential_value": 320000,  # dollars
        "avg_fit_score": 0.76,      # 0..1
        "event_readiness": 0.68,    # 0..1
        "historical_roi": 0.21,     # 0..1
    }

    insights = [
        f"Severe heat forecast expected near {region} may boost HVAC service demand in the next 10 days.",
        "Local utility efficiency rebates open for SMB retrofits; average award $3k–$12k.",
        "Two city RFPs closing within 14 days; consider partnering to improve award odds.",
    ]

    items = [
        {
            "title": "City Facilities HVAC Preventive Contract",
            "category": "bid",
            "date": "2025-10-18",
            "deadline": "2025-10-25",
            "fit_score": 0.83,
            "roi_est": 0.34,
            "link": "https://example.gov/rfp/hvac-preventive",
        },
        {
            "title": "Austin Energy Small Business Efficiency Rebate",
            "category": "grant",
            "deadline": "2025-11-05",
            "fit_score": 0.71,
            "roi_est": 0.28,
            "link": "https://austinenergy.com/rebates/smb",
        },
        {
            "title": "Regional Contractor Networking Night",
            "category": "event",
            "date": "2025-10-22",
            "fit_score": 0.62,
            "roi_est": 0.12,
            "link": "https://example.com/events/regional-contractors",
        },
        {
            "title": "Supplier Bulk Filter Promo (Q4)",
            "category": "partner",
            "deadline": "2025-10-30",
            "fit_score": 0.66,
            "roi_est": 0.17,
            "link": "https://supplier.example.com/promos/q4-filters",
        },
        {
            "title": "Hot Weather Alert — Load Spike",
            "category": "weather",
            "date": "2025-10-20",
            "fit_score": 0.80,
            "roi_est": 0.10,
            "weather": "Heat index >100°F",
        },
    ]

    visuals = [
        {
            "type": "bar",
            "title": "Potential Value by Category",
            "labels": ["bid", "grant", "event", "partner", "weather"],
            "values": [180000, 65000, 10000, 45000, 20000],
        }
    ]

    result: Dict[str, Any] = {
        "kpis": kpis,
        "insights": insights,
        "items": items,
        "visuals": visuals,
        "assumptions": {"company_id": "demo", "inputs": {"region": region}},
    }
    return _normalize_opportunities(result)

# ---------- Router ----------

@router.post("/api/intent")
async def intent_router(req: IntentRequest):
    intent = (req.intent or "").strip().lower()
    company_id = req.company_id or "demo"
    input_data = req.input or {}

    if intent == "opportunities":
        region = str(input_data.get("region") or "Austin, TX")
        # TODO: when ready, replace demo with a call to your Orchestrator Assistant and normalize the result.
        # ai_payload = await call_orchestrator("opportunities", company_id=company_id, input=input_data)
        # result = _normalize_opportunities(ai_payload)
        result = _build_demo_opportunities(region)
        return {"intent": intent, "company_id": company_id, "result": result}

    # Add additional intents here as you bring new tabs online:
    # elif intent == "business_health": ...
    # elif intent == "payroll_hiring": ...
    # elif intent == "fraud_compliance": ...

    raise HTTPException(status_code=400, detail=f"Unknown intent: {intent}")
