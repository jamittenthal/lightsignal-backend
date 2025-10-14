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

app = FastAPI(title="LightSignal API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
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

# Mount the unified intent router
app.include_router(intent_router)
