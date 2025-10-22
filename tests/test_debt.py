import pytest
from app.services import debt_engine


def test_weighted_avg_rate():
    accs = [
        {"balance":100, "rate_pct":10},
        {"balance":300, "rate_pct":5}
    ]
    w = debt_engine.weighted_avg_rate(accs)
    assert pytest.approx(w, rel=1e-3) == (100*10+300*5)/(400)


def test_dti_edge_cases():
    assert debt_engine.compute_dti(1000, 0) is None
    assert debt_engine.compute_dti(1000, -100) is None
    assert pytest.approx(debt_engine.compute_dti(1000, 5000)) == 0.2


def test_dscr_edge_cases():
    assert debt_engine.compute_dscr(1000, 0) is None
    assert pytest.approx(debt_engine.compute_dscr(1200, 800)) == 1.5


def test_amortization_basic():
    sched = debt_engine.amortization_schedule(10000, 6.0, 12)
    # monthly payment should be > 800 and length 12
    assert len(sched) == 12
    assert sched[0]["interest"] > 0
    total_principal = sum([p["principal"] for p in sched])
    assert pytest.approx(total_principal, rel=1e-3) == 10000


def test_avalanche_vs_snowball():
    accs = [
        {"account_id":"a1","balance":5000,"rate_pct":20,"monthly_payment":150},
        {"account_id":"a2","balance":2000,"rate_pct":15,"monthly_payment":80},
        {"account_id":"a3","balance":800,"rate_pct":25,"monthly_payment":40},
    ]
    res = debt_engine.avalanche_vs_snowball(accs)
    assert "avalanche" in res and "snowball" in res
    # avalanche should have less or equal interest than snowball
    assert res["avalanche"]["interest"] <= res["snowball"]["interest"] + 1e-6


def test_risk_alerts_thresholds():
    accs = [{"account_id":"b1","name":"x","balance":1000,"rate_pct":30,"monthly_payment":50,"balloon_due_months":2,"variable_rate":False},{"account_id":"b2","name":"y","balance":500,"rate_pct":5,"monthly_payment":25,"variable_rate":True}]
    alerts = debt_engine.risk_alerts(accs, {"term_refi":7.0}, dscr=0.9, utilization_pct=0.6)
    ids = [a["id"] for a in alerts]
    assert any("balloon_b1" in i for i in ids)
    assert any("dscr_low" in i for i in ids)
    assert any("util_high" in i for i in ids)


def test_biweekly_effect_estimate():
    res = debt_engine.biweekly_effect(10000, 10.0, 200)
    assert "interest_saved" in res and "months_earlier" in res
    assert res["interest_saved"] >= 0
