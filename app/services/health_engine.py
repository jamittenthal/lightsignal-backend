from typing import Dict, Any, List, Optional
import time
import json
from ..schemas import StateEnum
from .insights_engine import _efficiency_score, _growth_opportunity_index, _map_state, vector_benchmarks


def _composite_health(financial: float, operational: float, customer: float, risk: float, weights=(0.4,0.25,0.2,0.15)) -> float:
    raw = weights[0]*financial + weights[1]*operational + weights[2]*customer + weights[3]*(1-risk)
    return round(100 * max(0.0, min(1.0, raw)), 1)


def compute_health(company_id: str, profile: Dict[str, Any], series: List[Dict[str, Any]], include_peers: bool=False, include_breakdowns: bool=True) -> Dict[str, Any]:
    start = time.time()
    latest = series[-1] if series else {"revenue":0.0, "opex":0.0}
    prev = series[-2] if len(series) > 1 else latest

    revenue = latest.get("revenue", 0.0)
    prev_revenue = prev.get("revenue", 0.0) or 1.0
    revenue_growth = (revenue - prev_revenue) / prev_revenue

    opex = latest.get("opex", 0.0)
    expense_ratio = opex / revenue if revenue else 0.0

    net_income = latest.get("revenue", 0.0) - latest.get("cogs", 0.0) - opex
    margin_pct = (net_income / revenue) if revenue else 0.0

    employees = profile.get("employees", 10)
    rpe = revenue / max(1, employees)

    peer_rpe = rpe * 0.95
    efficiency = _efficiency_score(expense_ratio, margin_pct, rpe, peer_rpe)
    growth_idx = _growth_opportunity_index({"market_size":200000,"peer_success":0.5,"required_capital":40000,"est_roi":0.2})

    # category scores (demo normalized to 0..1)
    financial_score = min(1.0, max(0.0, (efficiency/100)*0.9 + (margin_pct if margin_pct>0 else 0)*0.1))
    operational_score = min(1.0, max(0.0, (1 - expense_ratio)*0.7 + (rpe/ max(1.0, peer_rpe))*0.3))
    customer_score = 0.8 if profile.get("mode") == "demo" else 0.7
    risk_score = 0.2 if margin_pct>0.1 else 0.35

    overall = _composite_health(financial_score, operational_score, customer_score, risk_score)

    # categories breakdown
    categories = []
    cats = [
        ("Financial Health", financial_score*100, "financial", [{"label":"margin_pct","value":round(margin_pct*100,2)}]),
        ("Operational Health", operational_score*100, "operational", [{"label":"revenue_per_employee","value":round(rpe,2)}]),
        ("Customer Health", customer_score*100, "customer", [{"label":"review_sentiment","value":profile.get("review_sentiment",0.7)}]),
        ("Risk Health", (1-risk_score)*100, "risk", [{"label":"debt_service_ratio","value":profile.get("dsr",1.2)}]),
    ]
    for name, score, key, drivers in cats:
        state = _map_state(key, score/100)
        categories.append({"category": name, "score": round(score,1), "state": state.value, "drivers": drivers})

    # alerts
    alerts = []
    if margin_pct < 0.05:
        alerts.append({"id":"low_margin","title":"Low net margin","severity":"high","description":"Net margin below 5%", "linked_kpis":["margin_pct"]})
    if expense_ratio > 0.6:
        alerts.append({"id":"high_opex","title":"High operating expense ratio","severity":"medium","description":"OPEX is more than 60% of revenue", "linked_kpis":["expense_ratio"]})

    # heatmap - reuse simple departments
    departments = ["sales","operations","finance","marketing"]
    heatmap = []
    for d in departments:
        if d == "finance":
            ar = profile.get("ar_days", 35)
            state = _map_state("ar_days", ar)
            heatmap.append({"department": d, "metric": "ar_days", "state": state.value})
        else:
            score = efficiency/100 if d in ("operations","finance") else growth_idx/100
            s = _map_state(d, score)
            heatmap.append({"department": d, "metric": "composite", "state": s.value})

    # recommendations
    recommendations = []
    if overall < 60:
        recommendations.append({
            "title": "Improve margins and reduce top-line cost drivers",
            "description": "Audit largest 3 expense categories and negotiate vendor terms.",
            "expected_impact": "Increase margin by 3-6 pts",
            "confidence": "medium",
            "timeframe": "M",
            "lever": {"category":"costs","key":"opex_delta_pct","value":-5}
        })
    else:
        recommendations.append({
            "title": "Scale high-margin services",
            "description": "Prioritize sales initiatives for services with >40% gross margin.",
            "expected_impact": "Increase revenue by 5-10%",
            "confidence": "medium",
            "timeframe": "M",
            "lever": {"category":"revenue","key":"service_mix_pct","value":5}
        })

    # coach examples
    coach_examples = [
        {"question":"How's my overall health this period?","answer":f"Overall health score is {overall}. Financial drivers: margin_pct={round(margin_pct*100,2)}%"},
        {"question":"What should I fix first?","answer":"Prioritize improving net margin and reducing top 3 operating vendors"}
    ]

    # peers provenance
    provenance = {"baseline_source":"quickbooks_demo", "sources":["Financial Overview","Inventory","Assets","Reviews","Tax","Opportunities"], "notes":["Composite health score derived from normalized sub-metrics"], "confidence":"low"}
    if include_peers:
        provenance["notes"].append("Peer priors included (demo)")

    res = {
        "kpis": {
            "overall_health": overall,
            "revenue": revenue,
            "net_income": net_income,
            "margin_pct": round(margin_pct*100,2),
            "expense_ratio": round(expense_ratio*100,2)
        },
        "overview": {
            "summary": f"Overall business health is {overall} (demo)",
            "trend": [overall-2, overall-1, overall]
        },
        "categories": categories,
        "alerts": alerts,
        "heatmap": heatmap,
        "recommendations": recommendations,
        "coach_examples": coach_examples,
        "export": {"pdf_available": True, "csv_available": False},
        "_meta": {"source":"lightsignal.orchestrator","confidence":"low","latency_ms":int((time.time()-start)*1000),"provenance":provenance}
    }

    return res
