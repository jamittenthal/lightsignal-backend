from typing import Any, Dict, List

def safe_div(a: float, b: float) -> float:
    return (a / b) if b else 0.0

def compute_all_kpis(profile: Dict[str, Any], pl: List[Dict[str, float]], bs: Dict[str, float], cf: Dict[str, float]) -> Dict[str, Any]:
    # Trailing totals
    rev_total = sum(x["revenue"] for x in pl)
    cogs_total = sum(x["cogs"] for x in pl)
    opex_total = sum(x["opex"] for x in pl)
    gross_profit = rev_total - cogs_total
    ebitda = gross_profit - opex_total
    net_income = ebitda * 0.52  # crude tax/interest approximation

    # Margins
    gross_margin = safe_div(gross_profit, rev_total)
    ebitda_margin = safe_div(ebitda, rev_total)
    operating_margin = ebitda_margin  # for demo

    # Liquidity/Solvency
    current_assets = bs["cash"] + bs["receivables"] + bs["inventory"]
    current_ratio = safe_div(current_assets, bs["current_liab"])
    quick_ratio = safe_div(bs["cash"] + bs["receivables"], bs["current_liab"])
    debt_to_equity = safe_div(bs["debt"], bs["equity"])

    # Efficiency (very simple demo approximations)
    avg_receivables_days = 40.0
    avg_inventory_days = 30.0
    avg_payables_days = 28.0
    cash_conversion_cycle = avg_receivables_days + avg_inventory_days - avg_payables_days

    # Runway (months)
    monthly_burn = max(0.0, opex_total / 12 - (gross_profit / 12))  # if negative, treat as 0
    runway_months = (bs["cash"] / monthly_burn) if monthly_burn > 0 else 24.0

    # Simple growth estimate from first/last months
    first_rev = pl[0]["revenue"]
    last_rev = pl[-1]["revenue"]
    revenue_growth = safe_div(last_rev - first_rev, first_rev)

    return {
        "revenue_ttm": round(rev_total, 2),
        "gross_profit_ttm": round(gross_profit, 2),
        "ebitda_ttm": round(ebitda, 2),
        "net_income_ttm": round(net_income, 2),
        "cash_balance": round(bs["cash"], 2),
        "gross_margin": round(gross_margin, 3),
        "ebitda_margin": round(ebitda_margin, 3),
        "operating_margin": round(operating_margin, 3),
        "current_ratio": round(current_ratio, 2),
        "quick_ratio": round(quick_ratio, 2),
        "debt_to_equity": round(debt_to_equity, 2),
        "ccc_days": round(cash_conversion_cycle, 1),
        "runway_months": round(runway_months, 1),
        "revenue_growth": round(revenue_growth, 3),
    }

def default_benchmarks(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    # crude mock "peer" numbers for HVAC contractors
    return [
        {"metric": "gross_margin", "peer_median": 0.35, "peer_top_quartile": 0.42},
        {"metric": "ebitda_margin", "peer_median": 0.12, "peer_top_quartile": 0.18},
        {"metric": "current_ratio", "peer_median": 1.5, "peer_top_quartile": 2.0},
        {"metric": "debt_to_equity", "peer_median": 0.8, "peer_top_quartile": 0.5},
        {"metric": "ccc_days", "peer_median": 40, "peer_top_quartile": 30},
        {"metric": "revenue_growth", "peer_median": 0.06, "peer_top_quartile": 0.12},
    ]
