# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .schemas import OverviewResponse, ScenarioRequest, ScenarioResponse
from .services.qbo_adapter import get_financials
from .services.forecast import compute_kpis_and_forecast
from .services.benchmarks import vector_benchmarks
from .services.insights import write_insights

from .intent import router as intent_router
from .routers.profile import router as profile_router
from .routes_watchlist import router as watch_router
from .routes_ops import router as ops_router
from .routes_scenario_lab import router as scenario_lab_router
from .routers.insights import router as insights_router
from .routers.assets import router as assets_router
from .routers.tax import router as tax_router
from .routers.health import router as health_router
from .routers.debt import router as debt_router

app = FastAPI(title="LightSignal API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your Vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OverviewQuery(BaseModel):
    company_id: str
    periods: int = 12

@app.post("/api/overview", response_model=OverviewResponse)
async def api_overview(q: OverviewQuery):
    fin = await get_financials(q.company_id, q.periods)
    kpis = compute_kpis_and_forecast(fin)
    bench = vector_benchmarks(fin.profile.naics, fin.profile.size, fin.profile.region, ["margin","runway","dso"])
    insights = write_insights(kpis, bench)
    return OverviewResponse(financials=fin, kpis=kpis, benchmarks=bench, insights=insights)

@app.post("/api/scenario", response_model=ScenarioResponse)
async def api_scenario(req: ScenarioRequest):
    fin = await get_financials(req.company_id, 12)
    result = compute_kpis_and_forecast(fin, scenario=req.inputs)
    bench = vector_benchmarks(fin.profile.naics, fin.profile.size, fin.profile.region, ["margin","runway"])
    insights = write_insights(result, bench)
    return ScenarioResponse(base=result.base, scenario=result.scenario, visuals=result.visuals, insights=insights)

@app.get("/health")
async def health():
    return {"ok": True}

# NEW: feature routers
app.include_router(intent_router)
app.include_router(profile_router)
app.include_router(watch_router)
app.include_router(ops_router)
app.include_router(scenario_lab_router)
app.include_router(insights_router)
app.include_router(assets_router)
app.include_router(tax_router)
app.include_router(health_router)
app.include_router(debt_router)
