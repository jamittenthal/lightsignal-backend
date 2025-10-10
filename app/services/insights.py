from typing import List

def write_insights(kpis_or_result, benchmarks) -> List[str]:
    out = []
    if hasattr(kpis_or_result, "revenue_mtd"):
        margin = kpis_or_result.margin_pct or 0
        runway = kpis_or_result.runway_months or 0
        out.append(f"Margin at {margin:.1f}% — {'healthy' if margin>25 else 'watch'}.")
        out.append(f"Runway ~ {runway:.1f} months; consider AR acceleration if < 4 months.")
    else:
        out.append(f"Scenario margin {kpis_or_result.scenario.margin_pct:.1f}% vs base {kpis_or_result.base.margin_pct:.1f}%.")
        out.append(f"Runway change → {kpis_or_result.base.runway_months:.1f} → {kpis_or_result.scenario.runway_months:.1f} months.")
    return out
