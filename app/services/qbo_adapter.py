from ..schemas import FinancialsPayload, Profile, MonthlySeries
from datetime import datetime, timedelta

async def get_financials(company_id: str, periods: int) -> FinancialsPayload:
    # DEMO MODE: generate synthetic but realistic series
    today = datetime.utcnow().date().replace(day=1)
    series = []
    revenue = 30000.0
    cogs_ratio = 0.45
    opex = 14000.0
    cash = 80000.0
    for i in range(periods):
        m = (today - timedelta(days=30*i)).strftime('%Y-%m')
        rev = revenue * (1.0 + (i % 6 - 3) * 0.01)
        cogs = rev * cogs_ratio
        ox = opex * (1.0 + ((i % 4) - 2) * 0.01)
        cash += (rev - cogs - ox)
        series.append(MonthlySeries(month=m, revenue=rev, cogs=cogs, opex=ox, cash=cash))
    profile = Profile(company_id=company_id, name="DemoCo", naics="238220", size="small", region="FL", mode="demo")
    provenance = {"source": "playground|synthetic", "confidence": 0.8, "last_sync": "demo"}
    return FinancialsPayload(profile=profile, series=list(reversed(series)), provenance=provenance)
