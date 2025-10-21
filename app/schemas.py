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
    points: List[Dict[str, Any]]

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

# Scenario Planning Lab Models
class ScenarioLabRequest(BaseModel):
    company_id: str
    scenario_name: str
    description: Optional[str] = None
    inputs: ScenarioInputs
    horizon_months: Optional[int] = 12
    run_monte_carlo: Optional[bool] = False
    run_stress_test: Optional[bool] = False

class MonteCarloResult(BaseModel):
    p5: float  # 5th percentile
    p50: float  # 50th percentile (median)
    p95: float  # 95th percentile
    metric: str

class StressTestResult(BaseModel):
    scenario_name: str
    revenue_impact_pct: float
    cost_impact_pct: float
    cash_impact: float
    dscr: Optional[float] = None  # Debt Service Coverage Ratio
    icr: Optional[float] = None  # Interest Coverage Ratio

class ScenarioLabKPIs(BaseModel):
    revenue_delta_pct: float
    revenue_delta_dollars: float
    net_income_delta_pct: float
    margin_delta_pts: float
    cash_flow_delta: float
    runway_delta_months: float
    roi_pct: Optional[float] = None
    payback_months: Optional[float] = None

class PeerBenchmark(BaseModel):
    metric: str
    your_value: float
    peer_median: float
    peer_p75: float
    percentile: float
    source: str

class ScenarioLabResponse(BaseModel):
    scenario_name: str
    base: ScenarioBlock
    scenario: ScenarioBlock
    kpis: ScenarioLabKPIs
    visuals: List[ScenarioChart]
    monte_carlo: Optional[List[MonteCarloResult]] = None
    stress_tests: Optional[List[StressTestResult]] = None
    peer_benchmarks: Optional[List[PeerBenchmark]] = None
    recommendations: List[str]
    risks: List[str]
    provenance: Dict[str, Any]
    confidence: float
