import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_shape_demo_no_peers():
    req = {"company_id":"demo","range":"30d","include_peers":False,"include_breakdowns":True}
    r = client.post("/api/ai/health/full", json=req)
    assert r.status_code == 200
    body = r.json()
    # Top-level keys present
    keys = ["kpis","overview","categories","alerts","heatmap","recommendations","coach_examples","export","_meta"]
    for k in keys:
        assert k in body
    # provenance baseline
    assert body["_meta"]["provenance"]["baseline_source"] == "quickbooks_demo"
    # categories should be list
    assert isinstance(body["categories"], list)
    assert len(body["categories"]) > 0
    # heatmap should be list
    assert isinstance(body["heatmap"], list)
    # coach examples should be list
    assert isinstance(body["coach_examples"], list)
    assert len(body["coach_examples"]) > 0


def test_health_with_peers_sets_provenance():
    req = {"company_id":"demo","range":"90d","include_peers":True,"include_breakdowns":True}
    r = client.post("/api/ai/health/full", json=req)
    assert r.status_code == 200
    body = r.json()
    # When peers included, should be noted in provenance
    assert any("peer" in note.lower() for note in body["_meta"]["provenance"]["notes"])


def test_health_category_structure():
    req = {"company_id":"demo","range":"30d","include_peers":False,"include_breakdowns":True}
    r = client.post("/api/ai/health/full", json=req)
    body = r.json()
    categories = body["categories"]
    # Should have at least financial, operational, customer, risk categories
    category_names = [c["category"] for c in categories]
    expected_categories = ["Financial Health", "Operational Health", "Customer Health", "Risk Health"]
    for expected in expected_categories:
        assert expected in category_names
    
    # Each category should have required fields
    for cat in categories:
        assert "category" in cat
        assert "score" in cat
        assert "state" in cat
        assert "drivers" in cat
        assert cat["state"] in ["good", "stable", "caution", "bad"]
        assert 0 <= cat["score"] <= 100


def test_health_kpis_structure():
    req = {"company_id":"demo","range":"12m","include_peers":False,"include_breakdowns":True}
    r = client.post("/api/ai/health/full", json=req)
    body = r.json()
    kpis = body["kpis"]
    # Should have overall health score
    assert "overall_health" in kpis
    assert 0 <= kpis["overall_health"] <= 100
    # Should have financial metrics
    assert "revenue" in kpis
    assert "net_income" in kpis
    assert "margin_pct" in kpis
    assert "expense_ratio" in kpis


def test_health_alerts_structure():
    req = {"company_id":"demo","range":"30d","include_peers":False,"include_breakdowns":True}
    r = client.post("/api/ai/health/full", json=req)
    body = r.json()
    alerts = body["alerts"]
    assert isinstance(alerts, list)
    # Each alert should have required structure
    for alert in alerts:
        assert "id" in alert
        assert "title" in alert
        assert "severity" in alert
        assert alert["severity"] in ["low", "medium", "high"]


def test_health_heatmap_departments():
    req = {"company_id":"demo","range":"30d","include_peers":False,"include_breakdowns":True}
    r = client.post("/api/ai/health/full", json=req)
    body = r.json()
    heatmap = body["heatmap"]
    # Should have department breakdown
    departments = [h["department"] for h in heatmap]
    expected_depts = ["sales", "operations", "finance", "marketing"]
    for dept in expected_depts:
        assert dept in departments
    
    # Each heatmap entry should have required fields
    for entry in heatmap:
        assert "department" in entry
        assert "metric" in entry
        assert "state" in entry
        assert entry["state"] in ["good", "stable", "caution", "bad"]


def test_health_recommendations_structure():
    req = {"company_id":"demo","range":"30d","include_peers":False,"include_breakdowns":True}
    r = client.post("/api/ai/health/full", json=req)
    body = r.json()
    recommendations = body["recommendations"]
    assert isinstance(recommendations, list)
    # Each recommendation should have required fields
    for rec in recommendations:
        assert "title" in rec
        assert "confidence" in rec
        assert "timeframe" in rec
        assert rec["confidence"] in ["low", "medium", "high"]


def test_health_export_flags():
    req = {"company_id":"demo","range":"30d","include_peers":False,"include_breakdowns":True}
    r = client.post("/api/ai/health/full", json=req)
    body = r.json()
    export = body["export"]
    assert "pdf_available" in export
    assert isinstance(export["pdf_available"], bool)


def test_health_meta_structure():
    req = {"company_id":"demo","range":"30d","include_peers":False,"include_breakdowns":True}
    r = client.post("/api/ai/health/full", json=req)
    body = r.json()
    meta = body["_meta"]
    assert "source" in meta
    assert "confidence" in meta
    assert "latency_ms" in meta
    assert "provenance" in meta
    assert meta["source"] == "lightsignal.orchestrator"
    assert meta["confidence"] in ["low", "medium", "high"]
    
    provenance = meta["provenance"]
    assert "baseline_source" in provenance
    assert "sources" in provenance
    assert "notes" in provenance
    assert "confidence" in provenance


def test_health_coach_examples():
    req = {"company_id":"demo","range":"30d","include_peers":False,"include_breakdowns":True}
    r = client.post("/api/ai/health/full", json=req)
    body = r.json()
    coach_examples = body["coach_examples"]
    assert isinstance(coach_examples, list)
    assert len(coach_examples) > 0
    
    # Each coach example should have question and answer
    for example in coach_examples:
        assert "question" in example
        assert "answer" in example
        assert isinstance(example["question"], str)
        assert isinstance(example["answer"], str)


def test_health_non_demo_company():
    req = {"company_id":"test_company","range":"30d","include_peers":False,"include_breakdowns":True}
    r = client.post("/api/ai/health/full", json=req)
    assert r.status_code == 200
    body = r.json()
    # Should still return valid structure for non-demo companies
    keys = ["kpis","overview","categories","alerts","heatmap","recommendations","coach_examples","export","_meta"]
    for k in keys:
        assert k in body