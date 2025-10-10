from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Profile(BaseModel):
    company_id: str
    name: str
    naics: str
    size: str
    region: str
    mode: str = Field(description="demo|live")

class MonthlySeries(BaseModel):
    month: str
    revenue: float
    cogs: float
    opex: float
    cash: float

class FinancialsPayload(BaseModel):
    profile: Profile
    series: List[MonthlySeries]
    provenance: Dict[str, Any]

class KPIBlock(BaseModel):
    revenue_mtd: Optional[float]
    net_income_mtd: Optional[float]
    margin_pct: Optional[float]
    cash_available: Optional[float]
    runway_months: Optional[float]
    confidence: float

class Benchmark(BaseModel):
    metric: str
    value: float
    peer_percentile: float

class OverviewResponse(BaseModel):
    financials: FinancialsPayload
    kpis: KPIBlock
    benchmarks: List[Benchmark]
    insights: List[str]

class ScenarioInputs(BaseModel):
    price_change_pct: Optional[float] = 0
    headcount_delta: Optional[int] = 0
    loan_amount: Optional[float] = 0
    interest_rate: Optional[float] = 0.0
    capex_amount: Optional[float] = 0

class ScenarioRequest(BaseModel):
    company_id: str
    name: str
    inputs: ScenarioInputs

class ScenarioChart(BaseModel):
    name: str
    points: List[Dict[str, float]]

class ScenarioBlock(BaseModel):
    revenue: float
    net_income: float
    margin_pct: float
    runway_months: float

class ScenarioResponse(BaseModel):
    base: ScenarioBlock
    scenario: ScenarioBlock
    visuals: List[ScenarioChart]
    insights: List[str]
