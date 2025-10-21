from typing import Dict, Any, List, Optional
from ..schemas import StateEnum
import time
from ..services.benchmarks import vector_benchmarks


def _efficiency_score(expense_ratio: float, margin_pct: float, revenue_per_employee: float, peer_median_rpe: float, weights=(0.4,0.4,0.2)) -> float:
    # Normalize inputs: expense_ratio in 0..1, margin_pct as fraction (e.g., 0.2), revenue_per_employee scaled by peer_median
    a = 1 - expense_ratio
    b = margin_pct
    c = min(1.0, revenue_per_employee / (peer_median_rpe if peer_median_rpe>0 else max(revenue_per_employee,1)))
    raw = weights[0]*a + weights[1]*b + weights[2]*c
    return round(100 * max(0.0, min(1.0, raw)), 1)


def _growth_opportunity_index(features: Dict[str, Any]) -> float:
    # features: market_size, peer_success (0..1), required_capital (inverse), est_roi (0..1)
    market = min(1.0, (features.get("market_size", 0) / (1_000_000)))
    peer_success = min(1.0, float(features.get("peer_success", 0)))
    capital = features.get("required_capital", 1_000_000)
    capital_score = 1.0 / (1.0 + (capital / 100_000))
    roi = min(1.0, float(features.get("est_roi", 0)))
    raw = 0.35*market + 0.25*peer_success + 0.15*capital_score + 0.25*roi
    return round(100 * max(0.0, min(1.0, raw)), 1)


def _map_state(metric: str, value: float) -> StateEnum:
    # Demo thresholds per spec
    if metric == "efficiency":
        if value >= 70:
            return StateEnum.good
        if value >= 60:
            return StateEnum.caution
        return StateEnum.bad
    if metric == "growth_index":
        if value >= 80:
            return StateEnum.good
        if value >= 60:
            return StateEnum.caution
        return StateEnum.bad
    if metric == "ar_days":
        if value <= 32:
            return StateEnum.good
        if value <= 40:
            return StateEnum.caution
        return StateEnum.bad
    # default mapping
    if value >= 0.75:
        return StateEnum.good
    if value >= 0.4:
        return StateEnum.stable
    return StateEnum.caution


def compute_insights(company_id: str, profile: Dict[str, Any], series: List[Dict[str, Any]], include_peers: bool=False) -> Dict[str, Any]:
    start = time.time()
    # Use latest month as MTD demo
    latest = series[-1] if series else {"revenue":0.0, "opex":0.0}
    prev = series[-2] if len(series) > 1 else latest

    revenue = latest.get("revenue", 0.0)
    prev_revenue = prev.get("revenue", 0.0) or 1.0
    revenue_growth_mom = (revenue - prev_revenue) / prev_revenue

    opex = latest.get("opex", 0.0)
    expense_ratio = opex / revenue if revenue else 0.0

    net_income = latest.get("revenue", 0.0) - latest.get("cogs", 0.0) - opex
    margin_pct = (net_income / revenue) if revenue else 0.0

    employees = profile.get("employees", 10)
    revenue_per_employee = revenue / max(1, employees)

    # Peer median revenue_per_employee stub
    peer_median_rpe = revenue_per_employee * 0.9

    efficiency_score = _efficiency_score(expense_ratio, margin_pct, revenue_per_employee, peer_median_rpe)

    # Opportunities demo
    opp_features = {"market_size": 500_000, "peer_success": 0.6, "required_capital": 50_000, "est_roi": 0.25}
    growth_index = _growth_opportunity_index(opp_features)

    # Internal analysis deltas
    internal_analysis = {
        "revenue_mom": round(revenue_growth_mom*100,2),
        "expense_ratio": round(expense_ratio*100,2),
        "margin_pct": round(margin_pct*100,2),
        "explanation": []
    }
    if revenue_growth_mom > 0.05:
        internal_analysis["explanation"].append("Revenue accelerating vs prior period; consider scaling capacity.")
    elif revenue_growth_mom < -0.05:
        internal_analysis["explanation"].append("Revenue declining; investigate demand drivers and collections.")

    # Heatmap per department demo
    departments = ["sales","operations","finance","marketing"]
    heatmap = []
    for d in departments:
        if d == "finance":
            # use AR Days metric demo
            ar = profile.get("ar_days", 35)
            state = _map_state("ar_days", ar)
            heatmap.append({"department": d, "metric": "ar_days", "state": state.value})
        else:
            # random mapping from efficiency/growth
            score = efficiency_score/100 if d in ("operations","finance") else growth_index/100
            s = _map_state(d, score)
            heatmap.append({"department": d, "metric": "composite", "state": s.value})

    # Recommendations
    recommendations = []
    if efficiency_score < 60:
        recommendations.append({
            "title": "Reduce operating expenses",
            "description": "Target top 3 vendors for cost renegotiation.",
            "expected_impact": "Improve margin by 3-7 pts",
            "confidence": "medium",
            "timeframe": "M",
            "lever": {"category":"costs","key":"opex_delta_pct","value":-5}
        })
    else:
        recommendations.append({
            "title": "Invest in growth marketing",
            "description": "Allocate incremental spend to proven channels to capture market opportunity.",
            "expected_impact": "Increase revenue by 5-12%",
            "confidence": "medium",
            "timeframe": "M",
            "lever": {"category":"revenue_demand","key":"marketing_delta_pct","value":5}
        })

    # Peers
    peers_block = None
    provenance = {"baseline_source":"quickbooks_demo", "sources":[], "notes":[], "confidence":"medium", "used_priors":False, "prior_weight":0.0}
    if include_peers:
        # reuse local vector_benchmarks stub
        bench = vector_benchmarks(profile.get("naics",""), profile.get("size",""), profile.get("region",""), ["margin","runway","dso"])
        peers_block = {"benchmarks": [b.dict() for b in bench], "notes": "demo priors"}
        provenance["used_priors"] = True
        provenance["prior_weight"] = 0.4
        provenance["notes"].append("peer values are demo priors")

    result = {
        "kpis": {
            "revenue": revenue,
            "net_income": net_income,
            "margin_pct": round(margin_pct*100,2),
            "expense_ratio": round(expense_ratio*100,2),
            "revenue_per_employee": round(revenue_per_employee,2)
        },
        "current_pulse": {
            "efficiency_score": efficiency_score,
            "growth_index": growth_index,
            "heatmap": heatmap
        },
        "internal_analysis": internal_analysis,
        "peers": peers_block,
        "recommendations": recommendations,
        "efficiency_roi": {"efficiency_score": efficiency_score, "growth_opportunity_index": growth_index, "details": opp_features},
        "opportunities": [
            {"title":"Membership Maintenance Plan Expansion","category":"revenue","fit_score":0.78,"est_roi":0.3,"required_capital":20000,"market_size":120000}
        ],
        "charts": {
            "profit_driver_breakdown": [{"label":"services","value":60},{"label":"parts","value":40}],
            "peer_radar": [{"axis":"margin","value":efficiency_score},{"axis":"growth","value":growth_index}],
            "opportunity_matrix": [{"x":0.5,"y":0.8,"label":"Maintenance Plans"}],
            "efficiency_trendline": [{"period":"T-3","score":efficiency_score-2},{"period":"T-2","score":efficiency_score-1},{"period":"T-1","score":efficiency_score}]
        },
        "export": {"pdf_available": True, "weekly_digest_available": True},
        "_meta": {"source":"lightsignal.orchestrator","confidence":"medium","latency_ms":int((time.time()-start)*1000),"provenance":provenance}
    }

    return result
