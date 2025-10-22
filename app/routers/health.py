from fastapi import APIRouter, HTTPException
from ..schemas import BusinessHealthRequest, BusinessHealthResponse
from ..services.health_engine import compute_health
import json

router = APIRouter()


@router.post("/api/ai/health/full", response_model=BusinessHealthResponse)
async def health_full(req: BusinessHealthRequest):
    company_id = req.company_id
    if company_id == "demo":
        try:
            with open("data/companies/demo/profile.json","r") as f:
                profile = json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"demo_profile_missing: {e}")
        # simple fabricated series
        series = [
            {"month":"2025-06","revenue":80000.0,"cogs":30000.0,"opex":25000.0,"cash":50000},
            {"month":"2025-07","revenue":85000.0,"cogs":32000.0,"opex":26000.0,"cash":52000},
            {"month":"2025-08","revenue":90000.0,"cogs":33000.0,"opex":27000.0,"cash":54000},
        ]
    else:
        profile = {"company_id": company_id, "naics":"","size":"","region":"","employees":10}
        series = [{"month":"2025-08","revenue":10000.0,"cogs":4000.0,"opex":3000.0,"cash":10000}]

    profile.setdefault("employees", 12)
    profile.setdefault("ar_days", 35)

    res = compute_health(company_id, profile, series, include_peers=req.include_peers, include_breakdowns=req.include_breakdowns)

    # Ensure top-level keys exist per contract
    return BusinessHealthResponse(
        kpis=res.get("kpis"),
        overview=res.get("overview"),
        categories=res.get("categories"),
        alerts=res.get("alerts"),
        heatmap=res.get("heatmap"),
        recommendations=res.get("recommendations"),
        coach_examples=res.get("coach_examples"),
        export=res.get("export"),
        _meta=res.get("_meta"),
    )
