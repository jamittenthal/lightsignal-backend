from fastapi import APIRouter, HTTPException
from ..schemas import BusinessInsightsRequest, BusinessInsightsResponse
from ..services.insights_engine import compute_insights
import json

router = APIRouter()


@router.post("/api/ai/insights/full", response_model=BusinessInsightsResponse)
async def insights_full(req: BusinessInsightsRequest):
    # demo mode: load profile and series from data files if company_id == 'demo'
    company_id = req.company_id
    if company_id == "demo":
        try:
            with open("data/companies/demo/profile.json","r") as f:
                profile = json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"demo_profile_missing: {e}")
        # simple demo series (monthly) - use fabricated values
        series = [
            {"month":"2025-06","revenue":80000.0,"cogs":30000.0,"opex":25000.0,"cash":50000},
            {"month":"2025-07","revenue":85000.0,"cogs":32000.0,"opex":26000.0,"cash":52000},
            {"month":"2025-08","revenue":90000.0,"cogs":33000.0,"opex":27000.0,"cash":54000},
        ]
    else:
        # For non-demo, return a minimal placeholder
        profile = {"company_id": company_id, "naics":"","size":"","region":"","employees":10}
        series = [{"month":"2025-08","revenue":10000.0,"cogs":4000.0,"opex":3000.0,"cash":10000}]

    # Attach some profile defaults used by engine
    profile.setdefault("employees", 12)
    profile.setdefault("ar_days", 35)

    res = compute_insights(company_id, profile, series, include_peers=req.include_peers)
    # Ensure top-level keys exist per contract
    return BusinessInsightsResponse(
        kpis=res.get("kpis"),
        current_pulse=res.get("current_pulse"),
        internal_analysis=res.get("internal_analysis"),
        peers=res.get("peers"),
        recommendations=res.get("recommendations"),
        efficiency_roi=res.get("efficiency_roi"),
        opportunities=res.get("opportunities"),
        charts=res.get("charts"),
        export=res.get("export"),
        _meta=res.get("_meta"),
    )
