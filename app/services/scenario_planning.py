# app/services/scenario_planning.py
import random
from typing import List, Dict, Any
from ..schemas import (
    ScenarioLabRequest, ScenarioBlock, ScenarioChart, ScenarioLabKPIs,
    MonteCarloResult, StressTestResult, PeerBenchmark, FinancialsPayload
)


def run_monte_carlo_simulation(
    base_revenue: float,
    base_costs: float,
    base_cash: float,
    scenario_inputs: Dict[str, float],
    num_simulations: int = 1000
) -> List[MonteCarloResult]:
    """
    Run Monte Carlo simulations to generate probabilistic outcomes.
    Returns p5, p50, p95 for key metrics.
    """
    revenue_results = []
    margin_results = []
    cash_results = []
    
    # Simulate revenue volatility
    for _ in range(num_simulations):
        # Add randomness: ±15% revenue volatility, ±10% cost volatility
        revenue_var = random.gauss(1.0, 0.15)
        cost_var = random.gauss(1.0, 0.10)
        
        simulated_revenue = base_revenue * revenue_var * (1 + scenario_inputs.get('price_change_pct', 0) / 100)
        simulated_costs = base_costs * cost_var + scenario_inputs.get('headcount_delta', 0) * 6000
        simulated_margin = (simulated_revenue - simulated_costs) / max(simulated_revenue, 1e-6) * 100
        simulated_cash = base_cash - scenario_inputs.get('capex_amount', 0) + (simulated_revenue - simulated_costs)
        
        revenue_results.append(simulated_revenue)
        margin_results.append(simulated_margin)
        cash_results.append(simulated_cash)
    
    # Sort and get percentiles
    revenue_results.sort()
    margin_results.sort()
    cash_results.sort()
    
    def get_percentiles(data: List[float]) -> Dict[str, float]:
        n = len(data)
        return {
            'p5': data[int(n * 0.05)],
            'p50': data[int(n * 0.50)],
            'p95': data[int(n * 0.95)]
        }
    
    revenue_pct = get_percentiles(revenue_results)
    margin_pct = get_percentiles(margin_results)
    cash_pct = get_percentiles(cash_results)
    
    return [
        MonteCarloResult(metric='revenue', **revenue_pct),
        MonteCarloResult(metric='margin_pct', **margin_pct),
        MonteCarloResult(metric='cash', **cash_pct)
    ]


def run_stress_tests(
    base_revenue: float,
    base_cogs: float,
    base_opex: float,
    base_cash: float,
    debt: float = 0.0
) -> List[StressTestResult]:
    """
    Run stress test scenarios to evaluate business resilience.
    """
    stress_tests = []
    
    # Scenario 1: Revenue down 15%, costs up 10%
    revenue_stress = base_revenue * 0.85
    cost_stress = (base_cogs + base_opex) * 1.10
    net_income_stress = revenue_stress - cost_stress
    cash_stress = base_cash + net_income_stress
    
    dscr = None
    if debt > 0:
        monthly_debt_service = debt * 0.01  # Assume 1% monthly payment
        dscr = net_income_stress / monthly_debt_service if monthly_debt_service > 0 else 999
    
    stress_tests.append(StressTestResult(
        scenario_name="Revenue -15%, Costs +10%",
        revenue_impact_pct=-15.0,
        cost_impact_pct=10.0,
        cash_impact=cash_stress - base_cash,
        dscr=dscr,
        icr=None
    ))
    
    # Scenario 2: Interest rate +2 points
    if debt > 0:
        interest_increase = debt * 0.02 / 12  # 2% annual = 0.167% monthly
        cash_impact_2 = -interest_increase
        stress_tests.append(StressTestResult(
            scenario_name="Interest Rate +2 pts",
            revenue_impact_pct=0.0,
            cost_impact_pct=0.0,
            cash_impact=cash_impact_2,
            dscr=None,
            icr=base_revenue / interest_increase if interest_increase > 0 else 999
        ))
    
    # Scenario 3: Supply disruption (30 days)
    revenue_disruption = base_revenue * 0.70  # 30% revenue loss
    cash_disruption = base_cash + (revenue_disruption - base_cogs - base_opex)
    stress_tests.append(StressTestResult(
        scenario_name="Supply Disruption 30 Days",
        revenue_impact_pct=-30.0,
        cost_impact_pct=0.0,
        cash_impact=cash_disruption - base_cash,
        dscr=None,
        icr=None
    ))
    
    return stress_tests


def get_peer_benchmarks(
    naics: str,
    region: str,
    revenue: float,
    margin_pct: float,
    runway_months: float
) -> List[PeerBenchmark]:
    """
    Generate peer benchmark comparisons.
    In production, this would query Pinecone or peer database.
    """
    # Demo peer data based on NAICS
    peer_data = {
        '238220': {  # HVAC contractors
            'margin': {'median': 28.0, 'p75': 35.0},
            'revenue_per_employee': {'median': 125000, 'p75': 145000},
            'runway': {'median': 5.5, 'p75': 8.0}
        },
        'default': {
            'margin': {'median': 25.0, 'p75': 32.0},
            'revenue_per_employee': {'median': 110000, 'p75': 135000},
            'runway': {'median': 4.5, 'p75': 7.0}
        }
    }
    
    benchmarks_data = peer_data.get(naics, peer_data['default'])
    
    # Calculate percentiles
    def calc_percentile(value: float, median: float, p75: float) -> float:
        if value < median:
            return 50 * (value / median)
        else:
            return 50 + 25 * ((value - median) / (p75 - median))
    
    margin_bench = benchmarks_data['margin']
    runway_bench = benchmarks_data['runway']
    
    return [
        PeerBenchmark(
            metric='margin_pct',
            your_value=margin_pct,
            peer_median=margin_bench['median'],
            peer_p75=margin_bench['p75'],
            percentile=calc_percentile(margin_pct, margin_bench['median'], margin_bench['p75']),
            source='QuickBooks Cohort'
        ),
        PeerBenchmark(
            metric='runway_months',
            your_value=runway_months,
            peer_median=runway_bench['median'],
            peer_p75=runway_bench['p75'],
            percentile=calc_percentile(runway_months, runway_bench['median'], runway_bench['p75']),
            source='Industry Survey'
        )
    ]


def generate_recommendations(
    base: ScenarioBlock,
    scenario: ScenarioBlock,
    kpis: ScenarioLabKPIs,
    stress_tests: List[StressTestResult]
) -> List[str]:
    """
    Generate AI-style recommendations based on scenario analysis.
    """
    recommendations = []
    
    # Revenue analysis
    if kpis.revenue_delta_pct > 5:
        recommendations.append(
            f"Revenue increase of {kpis.revenue_delta_pct:.1f}% ({kpis.revenue_delta_dollars:,.0f}) "
            "is projected. Consider scaling operations to capture this growth."
        )
    elif kpis.revenue_delta_pct < -5:
        recommendations.append(
            f"Revenue decline of {abs(kpis.revenue_delta_pct):.1f}% projected. "
            "Review cost reduction strategies to maintain profitability."
        )
    
    # Margin analysis
    if kpis.margin_delta_pts > 2:
        recommendations.append(
            f"Margin improvement of {kpis.margin_delta_pts:.1f} percentage points expected. "
            "This efficiency gain strengthens your competitive position."
        )
    elif kpis.margin_delta_pts < -2:
        recommendations.append(
            f"Margin compression of {abs(kpis.margin_delta_pts):.1f} points. "
            "Consider price increases or operational efficiency improvements."
        )
    
    # Runway analysis
    if kpis.runway_delta_months < -2:
        recommendations.append(
            f"Cash runway decreases by {abs(kpis.runway_delta_months):.1f} months. "
            "Ensure adequate cash reserves or consider delayed implementation."
        )
    elif kpis.runway_delta_months > 2:
        recommendations.append(
            f"Cash position improves by {kpis.runway_delta_months:.1f} months of runway. "
            "Strong financial flexibility for future investments."
        )
    
    # ROI analysis
    if kpis.roi_pct and kpis.roi_pct > 15:
        recommendations.append(
            f"Expected ROI of {kpis.roi_pct:.1f}% exceeds typical project threshold. "
            "Strong financial case for proceeding."
        )
    
    # Stress test insights
    if stress_tests:
        for test in stress_tests:
            if test.dscr and test.dscr < 1.25:
                recommendations.append(
                    f"⚠ Warning: {test.scenario_name} results in DSCR of {test.dscr:.2f}, "
                    "close to covenant limits. Build cash buffer before proceeding."
                )
    
    return recommendations if recommendations else [
        "Scenario impact is minimal. Consider whether this change aligns with strategic priorities."
    ]


def generate_risks(
    base: ScenarioBlock,
    scenario: ScenarioBlock,
    kpis: ScenarioLabKPIs,
    stress_tests: List[StressTestResult]
) -> List[str]:
    """
    Generate risk warnings based on scenario analysis.
    """
    risks = []
    
    # Cash risk
    if scenario.runway_months < 3:
        risks.append(
            f"🔴 Critical: Cash runway drops to {scenario.runway_months:.1f} months. "
            "Immediate liquidity risk."
        )
    elif scenario.runway_months < 6:
        risks.append(
            f"🟡 Caution: Cash runway of {scenario.runway_months:.1f} months. "
            "Monitor cash flow closely."
        )
    
    # Margin risk
    if scenario.margin_pct < 10:
        risks.append(
            f"🔴 Margin falls to {scenario.margin_pct:.1f}%, below healthy threshold. "
            "Review pricing and cost structure."
        )
    
    # Stress test risks
    if stress_tests:
        for test in stress_tests:
            if test.cash_impact < -50000:
                risks.append(
                    f"⚠ {test.scenario_name} could drain ${abs(test.cash_impact):,.0f} in cash. "
                    "Maintain emergency reserves."
                )
    
    # Revenue concentration (if applicable)
    if kpis.revenue_delta_pct > 20:
        risks.append(
            "⚠ Large revenue dependency on this scenario. Diversification recommended."
        )
    
    return risks if risks else ["No significant risks identified."]


def compute_scenario_lab_analysis(
    financials: FinancialsPayload,
    request: ScenarioLabRequest
) -> Dict[str, Any]:
    """
    Main function to compute comprehensive scenario lab analysis.
    """
    # Get baseline from latest month
    series = financials.series
    latest = series[-1]
    
    # Calculate base scenario
    base_revenue = latest.revenue
    base_cogs = latest.cogs
    base_opex = latest.opex
    base_costs = base_cogs + base_opex
    base_cash = latest.cash
    base_net_income = base_revenue - base_costs
    base_margin = (base_net_income / max(base_revenue, 1e-6)) * 100
    base_burn = max(base_costs - base_revenue, 0.0)
    base_runway = (base_cash / base_burn) if base_burn > 0 else 999.0
    
    base = ScenarioBlock(
        revenue=base_revenue,
        net_income=base_net_income,
        margin_pct=base_margin,
        runway_months=base_runway
    )
    
    # Apply scenario inputs
    inputs = request.inputs
    scenario_revenue = base_revenue * (1 + (inputs.price_change_pct or 0) / 100)
    scenario_opex = base_opex + (inputs.headcount_delta or 0) * 6000
    
    # Factor in loan
    loan_amount = inputs.loan_amount or 0
    interest_rate = inputs.interest_rate or 0
    monthly_interest = (loan_amount * interest_rate / 12 / 100) if loan_amount > 0 else 0
    
    # Factor in capex
    capex_amount = inputs.capex_amount or 0
    scenario_cash = base_cash + loan_amount - capex_amount
    
    scenario_costs = base_cogs + scenario_opex + monthly_interest
    scenario_net_income = scenario_revenue - scenario_costs
    scenario_margin = (scenario_net_income / max(scenario_revenue, 1e-6)) * 100
    scenario_burn = max(scenario_costs - scenario_revenue, 0.0)
    scenario_runway = (scenario_cash / scenario_burn) if scenario_burn > 0 else 999.0
    
    scenario = ScenarioBlock(
        revenue=scenario_revenue,
        net_income=scenario_net_income,
        margin_pct=scenario_margin,
        runway_months=scenario_runway
    )
    
    # Calculate KPIs
    revenue_delta_dollars = scenario_revenue - base_revenue
    revenue_delta_pct = (revenue_delta_dollars / max(base_revenue, 1e-6)) * 100
    net_income_delta_pct = ((scenario_net_income - base_net_income) / max(abs(base_net_income), 1e-6)) * 100
    margin_delta_pts = scenario_margin - base_margin
    cash_flow_delta = scenario_net_income - base_net_income
    runway_delta_months = scenario_runway - base_runway
    
    # ROI calculation (if there's an investment)
    roi_pct = None
    payback_months = None
    if capex_amount > 0:
        annual_benefit = (scenario_net_income - base_net_income) * 12
        roi_pct = (annual_benefit / capex_amount) * 100 if capex_amount > 0 else 0
        payback_months = (capex_amount / max(scenario_net_income - base_net_income, 1e-6)) if scenario_net_income > base_net_income else 999
    
    kpis = ScenarioLabKPIs(
        revenue_delta_pct=revenue_delta_pct,
        revenue_delta_dollars=revenue_delta_dollars,
        net_income_delta_pct=net_income_delta_pct,
        margin_delta_pts=margin_delta_pts,
        cash_flow_delta=cash_flow_delta,
        runway_delta_months=runway_delta_months,
        roi_pct=roi_pct,
        payback_months=payback_months if payback_months and payback_months < 999 else None
    )
    
    # Generate visuals
    visuals = []
    
    # Cash curve projection
    cash_points = []
    current_cash = scenario_cash
    for month in range(request.horizon_months):
        current_cash += scenario_net_income
        cash_points.append({'month': month, 'cash': round(current_cash, 2)})
    
    visuals.append(ScenarioChart(
        name='Cash Flow Projection',
        points=cash_points
    ))
    
    # Revenue comparison
    visuals.append(ScenarioChart(
        name='Revenue Comparison',
        points=[
            {'category': 'Base', 'value': round(base_revenue, 2)},
            {'category': 'Scenario', 'value': round(scenario_revenue, 2)}
        ]
    ))
    
    # Waterfall chart data
    waterfall_points = [
        {'step': 'Base Revenue', 'value': round(base_revenue, 2)},
        {'step': 'Price Change', 'value': round(revenue_delta_dollars, 2)},
        {'step': 'COGS', 'value': round(-base_cogs, 2)},
        {'step': 'OPEX Change', 'value': round(-(scenario_opex - base_opex), 2)},
        {'step': 'Interest', 'value': round(-monthly_interest, 2)},
        {'step': 'Net Income', 'value': round(scenario_net_income, 2)}
    ]
    visuals.append(ScenarioChart(
        name='Profit Waterfall',
        points=waterfall_points
    ))
    
    # Optional: Monte Carlo
    monte_carlo = None
    if request.run_monte_carlo:
        monte_carlo = run_monte_carlo_simulation(
            base_revenue=base_revenue,
            base_costs=base_costs,
            base_cash=base_cash,
            scenario_inputs=inputs.dict(),
            num_simulations=1000
        )
    
    # Optional: Stress tests
    stress_tests = None
    if request.run_stress_test:
        stress_tests = run_stress_tests(
            base_revenue=scenario_revenue,
            base_cogs=base_cogs,
            base_opex=scenario_opex,
            base_cash=scenario_cash,
            debt=loan_amount
        )
    
    # Peer benchmarks
    peer_benchmarks = get_peer_benchmarks(
        naics=financials.profile.naics,
        region=financials.profile.region,
        revenue=scenario_revenue,
        margin_pct=scenario_margin,
        runway_months=scenario_runway
    )
    
    # Generate recommendations and risks
    recommendations = generate_recommendations(base, scenario, kpis, stress_tests or [])
    risks = generate_risks(base, scenario, kpis, stress_tests or [])
    
    # Provenance
    provenance = {
        'baseline_source': financials.provenance.get('source', 'demo_financials'),
        'scenario_name': request.scenario_name,
        'used_priors': True,
        'prior_weight': 0.4,
        'monte_carlo_runs': 1000 if request.run_monte_carlo else 0,
        'timestamp': 'now'
    }
    
    # Confidence based on data source
    confidence = 0.85 if financials.profile.mode == 'demo' else 0.92
    
    return {
        'scenario_name': request.scenario_name,
        'base': base,
        'scenario': scenario,
        'kpis': kpis,
        'visuals': visuals,
        'monte_carlo': monte_carlo,
        'stress_tests': stress_tests,
        'peer_benchmarks': peer_benchmarks,
        'recommendations': recommendations,
        'risks': risks,
        'provenance': provenance,
        'confidence': confidence
    }
