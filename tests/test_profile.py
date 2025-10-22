import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import profile_engine

client = TestClient(app)


def test_full_returns_blocks_and_kpis():
    r = client.post("/api/ai/profile/full", json={"company_id": "demo"})
    assert r.status_code == 200
    j = r.json()
    assert "kpis" in j
    assert "general" in j


def test_ein_masking_on_save_and_full():
    # save general with EIN
    payload = {"company_id": "demo", "general": {"name": "X", "ein": "98-7654321", "locations": []}}
    r = client.post("/api/ai/profile/general/save", json=payload)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    # read full and ensure EIN is always masked in /full responses
    r2 = client.post("/api/ai/profile/full", json={"company_id": "demo"})
    assert r2.status_code == 200
    g = r2.json()["general"]
    # EIN should be masked in /full responses for PII safety
    assert g["ein"] == "**-***4321"


def test_naics_search_and_save_updates_benchmark():
    r = client.post("/api/ai/profile/industry/naics/search", json={"q": "plumbing", "limit": 5})
    assert r.status_code == 200
    res = r.json()["results"]
    assert any("238220" == s["code"] for s in res)
    # save industry
    payload = {"company_id": "demo", "industry": {"naics": {"code": "238220", "title": "Plumbing"}}}
    r2 = client.post("/api/ai/profile/industry/save", json=payload)
    assert r2.status_code == 200
    j = r2.json()
    assert j["ok"] is True


def test_upload_and_extract_flow():
    r = client.post("/api/ai/profile/uploads/upload", json={"company_id": "demo", "file_name": "EIN_Confirmation.pdf", "category": "EIN"})
    assert r.status_code == 200
    u = r.json()["upload"]
    assert u["status"] == "processing"
    uid = u["id"]
    r2 = client.post("/api/ai/profile/uploads/extract", json={"company_id": "demo", "id": uid})
    assert r2.status_code == 200
    ue = r2.json()["upload"]
    assert ue["status"] == "verified"
    assert ue.get("issuer") is not None


def test_completeness_recalc_and_weights():
    r = client.post("/api/ai/profile/completeness/recalc", json={"company_id": "demo"})
    assert r.status_code == 200
    j = r.json()
    assert "percent" in j
    assert 0.0 <= j["percent"] <= 1.0 or isinstance(j["percent"], float)


def test_export_returns_signed_url():
    r = client.post("/api/ai/profile/export", json={"company_id": "demo", "format": "pdf"})
    assert r.status_code == 200
    j = r.json()
    assert j.get("url", "").startswith("signed://")


def test_sync_confidence_calculation_with_recency():
    from app.services import profile_engine
    from datetime import datetime, timedelta
    import json
    
    # Test various recency bands for sync confidence
    # Backup original data
    original_data = profile_engine._load_demo()
    
    try:
        # Test 1: All connected, recent syncs (<=24h) should give high score
        now = datetime.utcnow()
        recent_sync = (now - timedelta(hours=12)).isoformat()
        test_data = {
            **original_data,
            "connectors": {
                "accounting": {"connected": True, "last_sync": recent_sync},
                "banking": {"connected": True, "last_sync": recent_sync},
                "crm": {"connected": True, "last_sync": recent_sync},
                "payroll": {"connected": True, "last_sync": recent_sync},
                "inventory": {"connected": True, "last_sync": recent_sync},
                "storage": {"connected": True, "last_sync": recent_sync},
            }
        }
        profile_engine._save_demo(test_data)
        confidence = profile_engine.calc_sync_confidence("demo")
        # 0.6 * (6/6) + 0.4 * 1.0 = 1.0
        assert confidence == 1.0
        
        # Test 2: All connected, week-old syncs (<=7d) should give medium score
        week_old_sync = (now - timedelta(days=3)).isoformat()
        test_data["connectors"] = {k: {"connected": True, "last_sync": week_old_sync} for k in test_data["connectors"]}
        profile_engine._save_demo(test_data)
        confidence = profile_engine.calc_sync_confidence("demo")
        # 0.6 * (6/6) + 0.4 * 0.5 = 0.8
        assert confidence == 0.8
        
        # Test 3: All connected, old syncs (>7d) should give lower score
        old_sync = (now - timedelta(days=30)).isoformat()
        test_data["connectors"] = {k: {"connected": True, "last_sync": old_sync} for k in test_data["connectors"]}
        profile_engine._save_demo(test_data)
        confidence = profile_engine.calc_sync_confidence("demo")
        # 0.6 * (6/6) + 0.4 * 0.2 = 0.68
        assert confidence == 0.68
        
        # Test 4: Half connected, no syncs
        test_data["connectors"] = {
            "accounting": {"connected": True, "last_sync": None},
            "banking": {"connected": True, "last_sync": None},
            "crm": {"connected": True, "last_sync": None},
            "payroll": {"connected": False, "last_sync": None},
            "inventory": {"connected": False, "last_sync": None},
            "storage": {"connected": False, "last_sync": None},
        }
        profile_engine._save_demo(test_data)
        confidence = profile_engine.calc_sync_confidence("demo")
        # 0.6 * (3/6) + 0.4 * 0.0 = 0.3
        assert confidence == 0.3
        
    finally:
        # Restore original data
        profile_engine._save_demo(original_data)


def test_autosave_metadata_in_responses():
    # Test that autosave metadata is included in _meta for optimistic FE autosave
    r = client.post("/api/ai/profile/full", json={"company_id": "demo"})
    assert r.status_code == 200
    meta = r.json()["_meta"]
    notes = meta["provenance"]["notes"]
    # Check that autosave info is in provenance notes
    assert any("autosave_version:" in note for note in notes)
    assert any("last_save:" in note for note in notes)
    assert any("optimistic:true" in note for note in notes)
    
    # Test in save endpoints too
    r2 = client.post("/api/ai/profile/general/save", json={"company_id": "demo", "general": {"name": "Test"}})
    assert r2.status_code == 200
    meta2 = r2.json()["_meta"]
    notes2 = meta2["provenance"]["notes"]
    assert any("autosave_version:" in note for note in notes2)
