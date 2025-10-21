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

# ----------------- Business Insights Models -----------------
from enum import Enum


class StateEnum(str, Enum):
    good = "good"
    stable = "stable"
    caution = "caution"
    bad = "bad"


class BusinessInsightsRequest(BaseModel):
    company_id: str
    range: str = Field(description="MTD|QTD|YTD")
    horizon: str = Field(description="3m|6m|12m|24m|60m")
    include_peers: bool = False


class MetaProvenance(BaseModel):
    baseline_source: str
    sources: List[str] = []
    notes: List[str] = []
    confidence: str = "medium"
    used_priors: bool = False
    prior_weight: float = 0.0


class MetaTop(BaseModel):
    source: str = "lightsignal.orchestrator"
    confidence: str = "medium"
    latency_ms: int = 0
    provenance: MetaProvenance


class Recommendation(BaseModel):
    title: str
    description: Optional[str]
    expected_impact: Optional[str]
    confidence: str
    timeframe: str
    peer_validation: Optional[Dict[str, Any]] = None
    lever: Optional[Dict[str, Any]] = None


class OpportunityItem(BaseModel):
    title: str
    category: str
    fit_score: Optional[float]
    est_roi: Optional[float]
    required_capital: Optional[float]
    market_size: Optional[float]


class HeatmapBlock(BaseModel):
    department: str
    metric: str
    state: StateEnum


class EfficiencyROI(BaseModel):
    efficiency_score: float
    growth_opportunity_index: float
    details: Dict[str, Any]


class ChartsBlock(BaseModel):
    profit_driver_breakdown: List[Dict[str, Any]] = []
    peer_radar: List[Dict[str, Any]] = []
    opportunity_matrix: List[Dict[str, Any]] = []
    efficiency_trendline: List[Dict[str, Any]] = []


class BusinessInsightsResponse(BaseModel):
    kpis: Dict[str, Any]
    current_pulse: Dict[str, Any]
    internal_analysis: Dict[str, Any]
    peers: Optional[Dict[str, Any]]
    recommendations: List[Recommendation]
    efficiency_roi: EfficiencyROI
    opportunities: List[OpportunityItem]
    charts: ChartsBlock
    export: Dict[str, Any]
    meta: MetaTop = Field(..., alias="_meta")

    model_config = {"populate_by_name": True}
