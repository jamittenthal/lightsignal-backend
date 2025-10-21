import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_insights_shape_demo_no_peers():
    req = {"company_id":"demo","range":"MTD","horizon":"3m","include_peers":False}
    r = client.post("/api/ai/insights/full", json=req)
    assert r.status_code == 200
    body = r.json()
    # Top-level keys present
    keys = ["kpis","current_pulse","internal_analysis","peers","recommendations","efficiency_roi","opportunities","charts","export","_meta"]
    for k in keys:
        assert k in body
    # provenance baseline
    assert body["_meta"]["provenance"]["baseline_source"] == "quickbooks_demo"
    # peers should be null/None when include_peers False
    assert body["peers"] is None


def test_insights_with_peers_sets_priors():
    req = {"company_id":"demo","range":"MTD","horizon":"3m","include_peers":True}
    r = client.post("/api/ai/insights/full", json=req)
    assert r.status_code == 200
    body = r.json()
    assert body["peers"] is not None
    assert body["_meta"]["provenance"]["used_priors"] is True
    assert abs(body["_meta"]["provenance"]["prior_weight"] - 0.4) < 1e-6


def test_heatmap_thresholds_mapping():
    req = {"company_id":"demo","range":"MTD","horizon":"3m","include_peers":False}
    r = client.post("/api/ai/insights/full", json=req)
    body = r.json()
    heat = body["current_pulse"]["heatmap"]
    # find finance dept entry and assert mapping matches ar_days threshold logic
    finance = [h for h in heat if h.get("department") == "finance"][0]
    state = finance.get("state")
    # profile has ar_days default 35 => caution per spec
    assert state in ("good","stable","caution","bad")
    assert state == "caution"
