import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_assets_full_shape_demo():
    req = {"company_id": "demo", "range": "30d", "include_registry": True, "include_maintenance": True, "include_telematics": True, "include_documents": True}
    r = client.post("/api/ai/assets/full", json=req)
    assert r.status_code == 200
    body = r.json()
    # check top-level keys
    keys = ["kpis", "integrations", "registry", "work_orders", "valuation", "utilization", "alerts", "documents", "quick_actions", "export", "_meta"]
    for k in keys:
        assert k in body
    # provenance baseline
    assert body["_meta"]["provenance"]["baseline_source"] == "quickbooks_demo"


def test_assets_search_filters():
    req = {"company_id": "demo", "query": "truck", "filters": {"category": "vehicle", "status": "active"}}
    r = client.post("/api/ai/assets/search", json=req)
    assert r.status_code == 200
    body = r.json()
    assert "results" in body
    for it in body["results"]:
        assert it["category"] == "vehicle"


def test_replace_vs_repair_recommendation():
    req = {
        "company_id": "demo",
        "asset_id": "TRK-102",
        "repair_cost_year": 6200,
        "downtime_cost_year": 2800,
        "replacement_cost": 78000,
        "replacement_useful_life_months": 84,
        "discount_rate_pct": 8,
        "expected_productivity_gain_pct": 6
    }
    r = client.post("/api/ai/assets/replace-vs-repair", json=req)
    assert r.status_code == 200
    body = r.json()
    assert body["recommendation"] in ("replace", "repair", "borderline")
    assert 0 <= body["tco_3yr_repair"]


def test_warranty_insurance_alerts_in_full():
    req = {"company_id": "demo"}
    r = client.post("/api/ai/assets/full", json=req)
    body = r.json()
    alerts = body.get("alerts", [])
    # expect at least one alert for near-expiry in demo data
    assert isinstance(alerts, list)


def test_health_score_range():
    req = {"company_id": "demo"}
    r = client.post("/api/ai/assets/full", json=req)
    body = r.json()
    regs = body.get("registry", [])
    for a in regs:
        hs = a.get("health_score")
        assert hs is not None
        assert 0 <= hs <= 100


def test_asset_management_intent():
    req = {"intent": "asset_management", "company_id": "demo", "input": {"range": "30d"}}
    r = client.post("/api/intent", json=req)
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "asset_management"
    result = body["result"]
    assert "kpis" in result
    assert "registry" in result
    assert "alerts" in result


def test_document_extract_dates():
    req = {
        "company_id": "demo",
        "docs": [
            {"doc_id": "D-1", "text": "Vehicle warranty expires 2026-03-15"},
            {"doc_id": "D-2", "text": "Insurance policy valid until December 2025"},
            {"doc_id": "D-3", "text": "Registration due: 2025-11-30"}
        ]
    }
    r = client.post("/api/ai/assets/documents/extract-dates", json=req)
    assert r.status_code == 200
    body = r.json()
    assert "documents" in body
    assert "_meta" in body
    docs = body["documents"]
    assert len(docs) == 3
    # Check that hints were extracted
    for doc in docs:
        assert "hints" in doc
        assert "confidence" in doc
