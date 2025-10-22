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


# ----------------- Business Health Models -----------------


class BusinessHealthRequest(BaseModel):
    company_id: str
    range: str = Field(description="30d|90d|12m")
    include_peers: bool = False
    include_breakdowns: bool = True


class CategoryScore(BaseModel):
    category: str
    score: float
    state: StateEnum
    drivers: List[Dict[str, Any]] = []


class AlertItem(BaseModel):
    id: str
    title: str
    severity: str
    description: Optional[str]
    linked_kpis: Optional[List[str]] = None


class ExportFlags(BaseModel):
    pdf_available: bool = True
    csv_available: bool = False


class CoachExample(BaseModel):
    question: str
    answer: str


class BusinessHealthResponse(BaseModel):
    kpis: Dict[str, Any]
    overview: Dict[str, Any]
    categories: List[CategoryScore]
    alerts: List[AlertItem]
    heatmap: List[HeatmapBlock]
    recommendations: List[Recommendation]
    coach_examples: List[CoachExample]
    export: ExportFlags
    meta: MetaTop = Field(..., alias="_meta")

    model_config = {"populate_by_name": True}


# ----------------- Asset Management Models -----------------
from datetime import datetime


class Asset(BaseModel):
    asset_id: str
    name: Optional[str]
    category: Optional[str]
    site: Optional[str]
    status: Optional[str]
    odometer: Optional[float]
    cost: Optional[float]
    salvage: Optional[float]
    useful_life_months: Optional[int]
    warranty_expires: Optional[str]
    insurance_expires: Optional[str]


class WorkOrder(BaseModel):
    wo_id: str
    asset_id: str
    priority: Optional[str]
    summary: Optional[str]
    status: Optional[str]
    created_at: Optional[str]
    closed_at: Optional[str]


class MaintenancePlan(BaseModel):
    plan_id: Optional[str]
    asset_id: str
    type: str
    interval: Optional[int]
    task: Optional[str]


class TelemetrySample(BaseModel):
    ts: str
    odometer: Optional[float]
    fuel: Optional[float]
    gps: Optional[Dict[str, float]]
    dtc: Optional[List[str]]


class AssetsFullRequest(BaseModel):
    company_id: str
    range: Optional[str]
    include_registry: Optional[bool] = True
    include_maintenance: Optional[bool] = True
    include_telematics: Optional[bool] = True
    include_documents: Optional[bool] = True


class ReplaceVsRepairRequest(BaseModel):
    company_id: str
    asset_id: str
    repair_cost_year: float
    downtime_cost_year: float
    replacement_cost: float
    replacement_useful_life_months: int
    discount_rate_pct: float
    expected_productivity_gain_pct: float


class ReplaceVsRepairResponse(BaseModel):
    tco_3yr_repair: float
    tco_3yr_replace: float
    npv_savings: float
    payback_months: Optional[int]
    recommendation: str
    assumptions: Dict[str, Any]
    meta: MetaTop = Field(..., alias="_meta")

    model_config = {"populate_by_name": True}


class AssetsSearchRequest(BaseModel):
    company_id: str
    query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class AssetsSearchResponse(BaseModel):
    results: List[Asset]
    meta: MetaTop = Field(..., alias="_meta")

    model_config = {"populate_by_name": True}


class ImportRequest(BaseModel):
    company_id: str
    rows: List[Dict[str, Any]]


class ImportResponse(BaseModel):
    imported: int
    skipped: int
    warnings: List[str]
    meta: MetaTop = Field(..., alias="_meta")

    model_config = {"populate_by_name": True}


class AssetsFullResponse(BaseModel):
    kpis: Dict[str, Any]
    integrations: List[str]
    registry: List[Dict[str, Any]]
    work_orders: List[Dict[str, Any]]
    valuation: Dict[str, Any]
    utilization: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    documents: List[Dict[str, Any]]
    quick_actions: Dict[str, Any]
    export: Dict[str, Any]
    meta: MetaTop = Field(..., alias="_meta")

    model_config = {"populate_by_name": True}


class WorkOrderCreateRequest(BaseModel):
    company_id: str
    asset_id: str
    priority: Optional[str] = "normal"
    summary: Optional[str] = ""
    sla_hours: Optional[int] = None


class WorkOrderCreateResponse(BaseModel):
    wo_id: str
    status: str
    meta: MetaTop = Field(..., alias="_meta")

    model_config = {"populate_by_name": True}


class MaintenanceScheduleRequest(BaseModel):
    company_id: str
    asset_id: str
    plan: Dict[str, Any]


class MaintenanceScheduleResponse(BaseModel):
    ok: bool
    meta: MetaTop = Field(..., alias="_meta")

    model_config = {"populate_by_name": True}


class TelemetryIngestRequest(BaseModel):
    company_id: str
    asset_id: str
    samples: List[Dict[str, Any]]


class TelemetryIngestResponse(BaseModel):
    ok: bool
    meta: MetaTop = Field(..., alias="_meta")

    model_config = {"populate_by_name": True}


class DocumentExtractRequest(BaseModel):
    company_id: str
    docs: List[Dict[str, Any]]


class DocumentExtractResponse(BaseModel):
    documents: List[Dict[str, Any]]
    meta: MetaTop = Field(..., alias="_meta")

    model_config = {"populate_by_name": True}


# ----------------- Tax Optimization Models -----------------
class TaxFullRequest(BaseModel):
    company_id: str
    year: int
    include_peers: Optional[bool] = False
    include_assets: Optional[bool] = False
    include_entity_analysis: Optional[bool] = False
    range: Optional[str] = Field(description="MTD|QTD|YTD", default="YTD")


class TaxKPI(BaseModel):
    label: str
    value: float
    pct_change: Optional[float] = None


class OpportunityDetail(BaseModel):
    id: str
    title: str
    category: str
    est_savings: float
    confidence: str
    notes: Optional[str]


class DeductionFinderItem(BaseModel):
    code: str
    title: str
    est_value: float
    source: Optional[str]


class QuarterlyScenarioResult(BaseModel):
    name: str
    delta_liability: float


class QuarterlyPlanResponse(BaseModel):
    next_due_date: str
    estimate_due: float
    set_aside_weekly: float
    scenarios: List[QuarterlyScenarioResult]
    meta: MetaTop = Field(..., alias="_meta")


class EntityOption(BaseModel):
    type: str
    est_savings_year: float
    assumptions: Optional[Dict[str, Any]]
    notes: Optional[str]


class EntityAnalysisResponse(BaseModel):
    current: str
    options: List[EntityOption]
    meta: MetaTop = Field(..., alias="_meta")


class DepreciationTimelineItem(BaseModel):
    month: str
    write_off: float


class DepreciationPlanResponse(BaseModel):
    timeline: List[DepreciationTimelineItem]
    notes: List[str]
    meta: MetaTop = Field(..., alias="_meta")


class PriorityItem(BaseModel):
    id: str
    text: str
    deadline: Optional[str]
    assignee: Optional[str]


class PrioritiesSaveRequest(BaseModel):
    company_id: str
    items: List[PriorityItem]


class ExportRequest(BaseModel):
    company_id: str
    format: str = Field(description="pdf|csv")
    variant: str = Field(description="optimization|quarterly")


class TaxAskRequest(BaseModel):
    company_id: str
    query: str
    year: Optional[int]


class TaxAskResponse(BaseModel):
    answer: str
    assumptions: Dict[str, Any]
    links: List[Dict[str, str]]
    actions: List[Dict[str, Any]]
    meta: MetaTop = Field(..., alias="_meta")


class TaxFullResponse(BaseModel):
    kpis: List[TaxKPI]
    overview: Dict[str, Any]
    opportunities: List[OpportunityDetail]
    benchmarks: Dict[str, Any]
    deduction_finder: List[DeductionFinderItem]
    quarterly_plan: QuarterlyPlanResponse
    entity_analysis: EntityAnalysisResponse
    depreciation: DepreciationPlanResponse
    priority_actions: List[PriorityItem]
    coach_examples: List[Dict[str, Any]]
    export: Dict[str, Any]
    meta: MetaTop = Field(..., alias="_meta")

    model_config = {"populate_by_name": True}


# ----------------- Debt Management Models -----------------
from typing import Literal


class DebtAccount(BaseModel):
    account_id: str
    type: str  # equipment_loan|vehicle_loan|credit_card|loc
    name: Optional[str]
    balance: float
    rate_pct: float
    monthly_payment: Optional[float]
    term_months: Optional[int]
    orig_balance: Optional[float]
    orig_term_months: Optional[int]
    next_due_date: Optional[str]
    balloon_due_months: Optional[int]
    variable_rate: Optional[bool] = False
    limit: Optional[float] = None
    history: Optional[List[Dict[str, Any]]] = []


class DebtFullRequest(BaseModel):
    company_id: str
    range: Optional[str] = Field(description="30d|QTD|YTD", default="30d")
    include_market_rates: Optional[bool] = True
    include_credit_score: Optional[bool] = True
    include_integrations: Optional[bool] = True


class DebtKPIs(BaseModel):
    weighted_avg_rate_pct: float
    total_balance: float
    monthly_payments: float
    dti: Optional[float]
    dscr: Optional[float]
    utilization_pct: Optional[float]


class DebtChartBlock(BaseModel):
    balance_trend: List[Dict[str, Any]] = []
    payment_breakdown: List[Dict[str, Any]] = []


class DebtOptimizationItem(BaseModel):
    id: str
    type: str
    description: str
    est_savings_annual: float
    est_fee: Optional[float]
    confidence: str


class DebtScenarioRequest(BaseModel):
    company_id: str
    scenario: str
    inputs: Dict[str, Any]


class DebtScenarioResponse(BaseModel):
    new_monthly: float
    interest_saved: float
    months_earlier: int
    new_payoff_date: Optional[str]
    per_account_impacts: List[Dict[str, Any]]
    meta: MetaTop = Field(..., alias="_meta")


class DebtAskRequest(BaseModel):
    company_id: str
    query: str
    filters: Optional[Dict[str, Any]] = None


class ConnectorRequest(BaseModel):
    company_id: str
    provider: str
    oauth_stub: Optional[bool] = True


class ConnectorResponse(BaseModel):
    ok: bool
    status: str
    meta: MetaTop = Field(..., alias="_meta")


class DebtAlert(BaseModel):
    id: str
    title: str
    severity: str
    description: Optional[str]


class CreditScoreBlock(BaseModel):
    score: int
    factors: List[Dict[str, Any]]


class DebtFullResponse(BaseModel):
    kpis: DebtKPIs
    accounts: List[DebtAccount]
    charts: DebtChartBlock
    utilization: Dict[str, Any]
    optimization: List[DebtOptimizationItem]
    scenarios: List[Dict[str, Any]]
    risk: Dict[str, Any]
    credit_score: Optional[CreditScoreBlock]
    recommendations: List[Recommendation]
    export: Dict[str, Any]
    meta: MetaTop = Field(..., alias="_meta")

    model_config = {"populate_by_name": True}

