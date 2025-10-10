from ..schemas import FinancialsPayload, KPIBlock, ScenarioInputs, ScenarioBlock, ScenarioChart

def compute_kpis_and_forecast(fin: FinancialsPayload, scenario: ScenarioInputs|None=None):
    s = fin.series
    latest = s[-1]
    margin = (latest.revenue - latest.cogs - latest.opex) / max(latest.revenue, 1e-6)
    burn = max((latest.cogs + latest.opex) - latest.revenue, 0.0)
    runway = (latest.cash / burn) if burn > 0 else 999.0

    kpis = KPIBlock(
        revenue_mtd=latest.revenue,
        net_income_mtd=latest.revenue - latest.cogs - latest.opex,
        margin_pct=margin*100,
        cash_available=latest.cash,
        runway_months=runway,
        confidence=0.8 if str(fin.provenance.get("source","demo")).startswith("playground") else 0.9
    )

    base = ScenarioBlock(
        revenue=latest.revenue,
        net_income=latest.revenue - latest.cogs - latest.opex,
        margin_pct=margin*100,
        runway_months=runway
    )

    if scenario:
        rev = latest.revenue * (1 + (scenario.price_change_pct or 0)/100)
        opex = latest.opex + (scenario.headcount_delta or 0)*6000
        interest = (scenario.loan_amount or 0) * ((scenario.interest_rate or 0)/12/100)
        net = rev - latest.cogs - opex - interest
        burn2 = max((latest.cogs + opex + interest) - rev, 0.0)
        runway2 = (latest.cash - (scenario.capex_amount or 0)) / burn2 if burn2>0 else 999.0
        scen_block = ScenarioBlock(
            revenue=rev,
            net_income=net,
            margin_pct=(net/max(rev,1e-6))*100,
            runway_months=runway2
        )
        charts = [
            ScenarioChart(name="Cash Curve 90d", points=[{"t": i, "cash": latest.cash + i*(net)} for i in range(0,4)])
        ]
        return type("ScenarioResult", (), {"base": base, "scenario": scen_block, "visuals": charts})
    else:
        return kpis
