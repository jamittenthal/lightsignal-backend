import pytest
from app.services.tax_engine import compute_etr, estimate_liability, compute_quarterly_plan, analyze_entity, plan_depreciation, save_priorities, get_priorities, tax_full


def test_etr_zero_income():
    assert compute_etr(0, 1000) == 0.0


def test_etr_negative_income():
    assert compute_etr(-5000, 100) == 0.0


def test_estimate_liability_basic():
    liab = estimate_liability(50000, 0.2, 3000)
    assert liab == max(0, 50000 * 0.2 - 3000)


def test_quarterly_plan_set_aside():
    out = compute_quarterly_plan("demo", 2025, [])
    assert "next_due_date" in out
    assert out["estimate_due"] >= 0
    assert out["set_aside_weekly"] >= 0


def test_entity_analysis_bounds():
    out = analyze_entity("demo", 65000, 55000, "llc_sp")
    assert out["current"] == "llc_sp"
    assert isinstance(out["options"], list)


def test_depreciation_totals():
    out = plan_depreciation("demo", ["TRK-102","GEN-01"], 2025)
    timeline = out.get("timeline", [])
    total = sum(item.get("write_off", 0) for item in timeline)
    assert total >= 0


def test_priorities_persistence():
    items = [{"id": "p-sec179", "text": "Maximize Section 179", "deadline": "2025-12-31", "assignee": "accountant"}]
    res = save_priorities("demo", items)
    assert res.get("ok") is True
    got = get_priorities("demo")
    assert got[0]["id"] == "p-sec179"


def test_tax_full_payload_shape():
    res = tax_full("demo", 2025)
    top_keys = ["kpis", "overview", "opportunities", "benchmarks", "deduction_finder", "quarterly_plan", "entity_analysis", "depreciation", "priority_actions", "coach_examples", "export", "_meta"]
    for k in top_keys:
        assert k in res