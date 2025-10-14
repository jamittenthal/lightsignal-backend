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

# ----------------- Models -----------------

class IntentRequest(BaseModel):
    intent: str
    company_id: Optional[str] = "demo"
    input: Optional[Dict[str, Any]] = None

# ----------------- Helpers -----------------

def _normalize_opportunities_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize whatever came back from the assistant (or demo) into the shape
    the Opportunities UI expects:
      {
        kpis: {
          active_count, potential_value, avg_fit_score, event_readiness, historical_roi
        },
        insights: string[],
        items: [{
          title, category, date?, deadline?, fit_score?, roi_est?, weather?, link?
        }],
        visuals: [{ type, title, labels, values }],
        assumptions: { ... }
      }
    """
    def _as_float(x):
        try:
            return float(x)
        except Exception:
            return None

    # 1) Insights
    insights = payload.get("insights") or payload.get("bullets") or []

    # 2) Items (many assistants use "opportunities", "leads", or "items")
    raw_items = payload.get("items") or payload.get("opportunities") or payload.get("leads") or []
    items: List[Dict[str, Any]] = []
    for it in raw_items:
        items.append({
            "title": it.get("title") or it.get("name") or "Untitled",
            "category": it.get("category") or it.get("kind") or "other",
            "date": it.get("date"),
            "deadline": it.get("deadline") or it.get("due"),
            "fit_score": _as_float(it.get("fit_score")),
            "roi_est": _as_float(it.get("roi_est") or it.get("roi")),
            "weather": it.get("weather"),
            "link": it.get("link") or it.get("url"),
        })

    # 3) Visuals (pass through if present)
    visuals = payload.get("visuals") or []

    # 4) KPIs
    k_src = payload.get("kpis") or {}
    # Try to compute from content if missing:
    active_count = k_src.get("active_count")
    if active_count is None:
        active_count = len(items) if isinstance(items, list) else None

    potential_value = k_src.get("potential_value")
    if potential_value is None:
        # try sum of estimated values if present on items
        total = 0.0
        found = False
        for it in raw_items:
            v = it.get("estimated_value") or it.get("value") or it.get("amount")
            if v is not None:
                try:
                    total += float(v)
                    found = True
                except Exception:
                    pass
        potential_value = total if found else None

    avg_fit_score = k_src.get("avg_fit_score")
    if avg_fit_score is None:
        fs = [_as_float(it.get("fit_score")) for it in items if it.get("fit_score") is not None]
        avg_fit_score = (sum(fs) / len(fs)) if fs else None

    event_readiness = k_src.get("event_readiness")  # leave as-is if provided
    historical_roi = k_src.get("historical_roi")    # leave as-is if provided

    kpis = {
        "active_count": active_count,
        "potential_value": potential_value,
        "avg_fit_score": avg_fit_score,
        "event_readiness": event_readiness,
        "historical_roi": historical_roi,
    }

    # 5) Assumptions passthrough
    assumptions = payload.get("assumptions") or {}

    return {
        "kpis": kpis,
        "insights": insights,
        "items": items,
        "visuals": visuals,
        "assumptions": assumptions,
    }

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
    return {"kpis": kpis, "insights": insights, "items": items, "visuals": visuals, "assumptions": {"company_id": "demo", "inputs": {"region": region}}}

def _is_empty_opportunities(result: Dict[str, Any]) -> bool:
    k = result.get("kpis") or {}
    items = result.get("items") or []
    # empty if no items AND all the main KPIs are None
    return (
        (not items) and
        all(k.get(key) in (None, 0) for key in ("active_count", "potential_value", "avg_fit_score", "event_readiness", "historical_roi"))
    )

# ----------------- Router -----------------

@router.post("/api/intent")
async def intent_router(req: IntentRequest):
    intent = (req.intent or "").strip().lower()
    company_id = req.company_id or "demo"
    input_data = req.input or {}

    # ---- Opportunities (Orchestrator → Research Scout under the hood) ----
    if intent == "opportunities":
        region = str(input_data.get("region") or "Austin, TX")
        # Try assistant if configured
        if ASST_ORCHESTRATOR_ID:
            try:
                ai_raw = await call_orchestrator(intent="opportunities", company_id=company_id, input_data=input_data)
                normalized = _normalize_opportunities_fields(ai_raw)
                if _is_empty_opportunities(normalized):
                    # No usable data from assistant → fallback to demo so UI still looks good
                    demo = _demo_opportunities(region)
                    return {"intent": intent, "company_id": company_id, "result": demo, "warning": "assistant_returned_empty"}
                return {"intent": intent, "company_id": company_id, "result": normalized}
            except Exception as e:
                demo = _demo_opportunities(region)
                return {"intent": intent, "company_id": company_id, "result": demo, "warning": f"assistant_error: {e}"}
        # No assistant configured → demo
        return {"intent": intent, "company_id": company_id, "result": _demo_opportunities(region)}

    # ---- Financial overview via Assistant (optional) ----
    if intent == "render_financial_overview":
        if ASST_FINANCE_ANALYST_ID:
            try:
                ai = await call_finance_analyst(company_id=company_id, periods=int(input_data.get("periods", 12)))
                return {"intent": intent, "company_id": company_id, "result": ai}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"finance_analyst_error: {e}")
        raise HTTPException(status_code=400, detail="Finance Analyst assistant not configured; use /api/overview")

    # ---- Ad-hoc research via Assistant (optional) ----
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
