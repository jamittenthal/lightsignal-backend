from datetime import date
from typing import List, Tuple, Dict, Any

# Simple demo profile
def get_demo_profile(company_id: str) -> Dict[str, Any]:
    return {
        "company_id": company_id,
        "name": "Demo HVAC Co.",
        "naics": "238220",  # Plumbing, Heating, and Air-Conditioning Contractors
        "region": "FL",
        "employees": 18,
        "fiscal_year_end": "12-31",
        "today": date.today().isoformat(),
    }

# 12 months normalized P&L + simple BS/CF
def get_demo_financials(company_id: str) -> Tuple[List[Dict[str, Any]], Dict[str, float], Dict[str, float]]:
    months = [
        "2024-07","2024-08","2024-09","2024-10","2024-11","2024-12",
        "2025-01","2025-02","2025-03","2025-04","2025-05","2025-06"
    ]
    base_rev = 180_000
    pl = []
    for i, m in enumerate(months):
        revenue = base_rev + i * 5_000
        cogs = revenue * 0.60
        opex = 55_000 + i * 500
        other = 0.0
        pl.append({
            "month": m,
            "revenue": round(revenue, 2),
            "cogs": round(cogs, 2),
            "opex": round(opex, 2),
            "other": round(other, 2),
        })

    bs = {
        "cash": 320_000.0,
        "receivables": 180_000.0,
        "inventory": 95_000.0,
        "current_liab": 330_000.0,
        "debt": 450_000.0,
        "equity": 700_000.0,
    }

    cf = {
        "operating": 210_000.0,
        "investing": -60_000.0,
        "financing": -30_000.0,
    }

    return pl, bs, cf
