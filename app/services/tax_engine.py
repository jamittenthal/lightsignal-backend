import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional

# In-memory priorities store for demo
_PRIORITIES_STORE: Dict[str, List[Dict[str, Any]]] = {}


def meta_top(baseline_source: str = "quickbooks_demo", sources: Optional[List[str]] = None, notes: Optional[List[str]] = None, confidence: str = "low", latency_ms: int = 20, used_priors: bool = True, prior_weight: float = 0.4):
    if sources is None:
        sources = ["QuickBooks", "Peer filings (Pinecone)", "IRS publications"]
    if notes is None:
        notes = ["Estimates only — confirm with licensed tax advisor."]
    return {
        "source": "lightsignal.orchestrator",
        "confidence": confidence,
        "latency_ms": latency_ms,
        "provenance": {
            "baseline_source": baseline_source,
            "sources": sources,
            "notes": notes,
            "confidence": confidence,
            "used_priors": used_priors,
            "prior_weight": prior_weight,
        },
    }


def load_demo_tax(company_id: str) -> Dict[str, Any]:
    # Try to load data/demo/tax.json; fallback to synthesized values
    try:
        with open("data/demo/tax.json", "r") as f:
            data = json.load(f)
            if data.get("company_id") == company_id:
                return data
    except Exception:
        pass

    # Synthesized deterministic demo
    demo = {
        "company_id": company_id,
        "year": 2025,
        "entity": "llc_sp",
        "owner_salary": 65000,
        "owner_draws": 55000,
        "ytd": {
            "revenue": 900000.0,
            "net_income": 85000.0,
            "tax_expense": 18000.0,
            "paid_estimates": 10000.0,
            "addbacks": 5000.0,
            "non_deductibles": 2000.0,
        },
        "assets_map_path": "data/demo/assets.json",
        "peers": {"industry_median_etr": 0.22},
    }
    return demo


def compute_etr(net_income: float, tax_expense: float) -> float:
    # ETR = tax_expense / net_income, guard for <=0
    if net_income <= 0:
        return 0.0
    return tax_expense / net_income


def estimate_liability(taxable_income: float, blended_rate: float, paid_estimates: float) -> float:
    est = max(0.0, taxable_income * blended_rate - paid_estimates)
    return est


def compute_opportunities(tax_data: Dict[str, Any], max_items: int = 10) -> List[Dict[str, Any]]:
    # Simple heuristic: look for common deductions based on expenses
    ytd = tax_data.get("ytd", {})
    ops = []
    # Section 179 opportunity if assets exist
    try:
        with open(tax_data.get("assets_map_path"), "r") as f:
            assets = json.load(f).get("assets", [])
    except Exception:
        assets = []

    capex_total = sum(a.get("cost", 0) for a in assets[:3])
    if capex_total > 0:
        ops.append({"id": "p-sec179", "title": "Section 179 election potential", "category": "depreciation", "est_savings": min(120000, capex_total) * 0.08, "confidence": "medium", "notes": "Estimate assumes eligible property."})

    # R&D credit stub if payroll exists
    payroll_est = ytd.get("revenue", 0) * 0.15
    if payroll_est > 10000:
        ops.append({"id": "p-rd-credit", "title": "R&D or Innovation credit potential", "category": "credit", "est_savings": payroll_est * 0.02, "confidence": "low", "notes": "Needs payroll analysis."})

    # State sales tax refund opportunities
    ops.append({"id": "p-sales-tax", "title": "Sales tax refund review", "category": "refund", "est_savings": 1200.0, "confidence": "low", "notes": "Potential over-collection."})

    # Fill to max_items with synthetic small items
    i = 1
    while len(ops) < max_items:
        ops.append({"id": f"p-synth-{i}", "title": f"Deduction candidate {i}", "category": "deduction", "est_savings": 250.0 * i, "confidence": "low", "notes": "Synthetic demo item."})
        i += 1

    # Rank by est_savings desc
    ops_sorted = sorted(ops, key=lambda x: x.get("est_savings", 0), reverse=True)
    return ops_sorted[:max_items]


def compute_quarterly_plan(company_id: str, year: int, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Next due date (simple): Jan 15 of next year
    next_due = date(year + 1, 1, 15)
    # Synthesize estimate_due by basic taxable income * blended rate
    tax_data = load_demo_tax(company_id)
    ytd = tax_data.get("ytd", {})
    net_income = ytd.get("net_income", 0)
    blended_rate = 0.22
    taxable_income = max(0.0, net_income + ytd.get("addbacks", 0) - ytd.get("non_deductibles", 0))
    estimate = estimate_liability(taxable_income, blended_rate, ytd.get("paid_estimates", 0))
    # weeks until due
    weeks = max(1, (next_due - date.today()).days // 7)
    set_aside_weekly = max(0.0, (estimate) / max(1, weeks))

    scenario_results = []
    for s in scenarios or []:
        name = s.get("name")
        capex = s.get("capex", 0)
        method = s.get("method", "sec179")
        defer = s.get("defer", False)
        if defer:
            delta = 0.0
        else:
            if method == "sec179":
                delta = -min(capex, 120000) * 0.08
            elif method == "bonus":
                delta = -capex * 0.5 * 0.22
            else:
                delta = 0.0
        scenario_results.append({"name": name, "delta_liability": round(delta, 2)})

    return {
        "next_due_date": next_due.isoformat(),
        "estimate_due": round(estimate, 2),
        "set_aside_weekly": round(set_aside_weekly, 2),
        "scenarios": scenario_results,
        "_meta": meta_top(confidence="low"),
    }


def analyze_entity(company_id: str, owner_salary: float, owner_draws: float, current_entity: str) -> Dict[str, Any]:
    # Simple heuristic: S-corp saves on self-employment tax on distributions
    # SE tax diff rate approx 15.3% -> effective saving on distributions after reasonable salary
    pass_through_profit = max(0.0, load_demo_tax(company_id).get("ytd", {}).get("net_income", 0))
    reasonable_salary = owner_salary
    distributions = max(0.0, pass_through_profit - reasonable_salary)
    se_tax_diff_rate = 0.076  # conservative delta after employer/employee split
    payroll_admin_cost = 800.0
    s_scorp_savings = min(distributions, owner_draws) * se_tax_diff_rate - payroll_admin_cost
    s_scorp_savings = max(0.0, round(s_scorp_savings, 2))

    options = [
        {"type": "s_corp", "est_savings_year": s_scorp_savings, "assumptions": {"salary": reasonable_salary}, "notes": "Reasonable comp + distributions"},
        {"type": "c_corp", "est_savings_year": 0.0, "assumptions": {}, "notes": "Double taxation risk"},
    ]

    return {"current": current_entity, "options": options, "_meta": meta_top(confidence="low")}


def plan_depreciation(company_id: str, assets: List[str], year: int) -> Dict[str, Any]:
    # Load asset map and schedule simple write-offs
    notes = []
    try:
        with open("data/demo/assets.json", "r") as f:
            assets_map = json.load(f).get("assets", [])
    except Exception:
        assets_map = []

    timeline = []
    total_179 = 0.0
    for a in assets_map:
        if assets and a.get("asset_id") not in assets:
            continue
        cost = a.get("cost", 0)
        # simple rule: vehicles eligible for 179 up to cap
        if a.get("category") in ("vehicle", "equipment") and total_179 < 120000:
            take_179 = min(cost, 120000 - total_179)
            timeline.append({"month": f"{year}-12", "write_off": round(take_179, 2)})
            total_179 += take_179
            remaining = cost - take_179
            if remaining > 0:
                timeline.append({"month": f"{year+1}-01", "write_off": round(remaining * 0.2, 2)})
        else:
            timeline.append({"month": f"{year+1}-01", "write_off": round(cost * 0.1, 2)})

    if total_179 > 0:
        notes.append("179 cap OK; bonus phasedown modeled.")
    else:
        notes.append("No 179 eligible assets selected.")

    return {"timeline": timeline, "notes": notes, "_meta": meta_top(confidence="medium")}


def save_priorities(company_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    _PRIORITIES_STORE[company_id] = items
    return {"ok": True, "_meta": meta_top(confidence="high")}


def get_priorities(company_id: str) -> List[Dict[str, Any]]:
    return _PRIORITIES_STORE.get(company_id, [])


def tax_full(company_id: str, year: int, include_peers: bool = True, include_assets: bool = True, include_entity_analysis: bool = True, range: str = "YTD") -> Dict[str, Any]:
    tax_data = load_demo_tax(company_id)
    ytd = tax_data.get("ytd", {})
    net_income = ytd.get("net_income", 0)
    tax_expense = ytd.get("tax_expense", 0)
    etr = compute_etr(net_income, tax_expense)

    taxable_income = max(0.0, net_income + ytd.get("addbacks", 0) - ytd.get("non_deductibles", 0))
    blended_rate = 0.22
    estimate_due = estimate_liability(taxable_income, blended_rate, ytd.get("paid_estimates", 0))

    # KPIs
    kpis = [
        {"label": "effective_tax_rate", "value": round(etr, 4), "pct_change": None},
        {"label": "ytd_taxable_income", "value": round(taxable_income, 2), "pct_change": None},
        {"label": "estimated_liability_due", "value": round(estimate_due, 2), "pct_change": None},
    ]

    # opportunities
    opportunities = compute_opportunities(tax_data, max_items=8)

    # deduction finder: map some common codes
    deduction_finder = [
        {"code": "§179", "title": "Section 179 deduction", "est_value": round(sum(o.get("est_savings", 0) for o in opportunities if o.get("category")=="depreciation"),2), "source": "Pub 946"},
        {"code": "Bonus", "title": "Bonus depreciation", "est_value": 0.0, "source": "IRC"},
    ]

    quarterly_plan = compute_quarterly_plan(company_id, year, [])

    entity_analysis = analyze_entity(company_id, tax_data.get("owner_salary", 65000), tax_data.get("owner_draws", 55000), tax_data.get("entity", "llc_sp")) if include_entity_analysis else {"current": tax_data.get("entity"), "options": [], "_meta": meta_top()}

    depreciation = plan_depreciation(company_id, [], year)

    priorities = get_priorities(company_id)

    export = {"formats": ["pdf", "csv"], "variants": ["optimization", "quarterly"]}

    benchmarks = {"industry_median_etr": tax_data.get("peers", {}).get("industry_median_etr", 0.22)} if include_peers else {}

    coach_examples = [{"q": "If I buy a $60k truck this quarter, what’s the tax impact?", "a": "Estimated Sec. 179 deduction up to $60k subject to limits; projected Q4 liability down ~$2.4k."}]

    return {
        "kpis": kpis,
        "overview": {"entity": tax_data.get("entity"), "owner_salary": tax_data.get("owner_salary")},
        "opportunities": opportunities,
        "benchmarks": benchmarks,
        "deduction_finder": deduction_finder,
        "quarterly_plan": {k: v for k, v in quarterly_plan.items() if k != "_meta"},
        "entity_analysis": {k: v for k, v in entity_analysis.items() if k != "_meta"},
        "depreciation": {k: v for k, v in depreciation.items() if k != "_meta"},
        "priority_actions": priorities,
        "coach_examples": coach_examples,
        "export": export,
        "_meta": meta_top(confidence="low"),
    }
