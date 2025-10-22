import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE = Path(__file__).resolve().parents[2]
DEMO_PATH = BASE / "data" / "demo" / "profile.json"
LOCK = threading.Lock()


def _load_demo() -> Dict[str, Any]:
    if not DEMO_PATH.exists():
        # create a minimal structure
        DEMO_PATH.parent.mkdir(parents=True, exist_ok=True)
        demo = {
            "general": {},
            "industry": {},
            "operations": {},
            "financial": {},
            "assets": [],
            "customers": {},
            "risk": {},
            "objectives": {},
            "uploads": [],
            "completeness": {"percent": 0.0, "missing": []},
            "connectors": {
                "accounting": {"connected": False, "last_sync": None},
                "banking": {"connected": False, "last_sync": None},
                "crm": {"connected": False, "last_sync": None},
                "payroll": {"connected": False, "last_sync": None},
                "inventory": {"connected": False, "last_sync": None},
                "storage": {"connected": False, "last_sync": None},
            },
        }
        DEMO_PATH.write_text(json.dumps(demo, indent=2))
        return demo
    with DEMO_PATH.open() as f:
        return json.load(f)


def _save_demo(data: Dict[str, Any]):
    with LOCK:
        DEMO_PATH.write_text(json.dumps(data, indent=2, default=str))


def make_meta() -> Dict[str, Any]:
    autosave_version = int(datetime.utcnow().timestamp())
    return {
        "source": "demo",
        "confidence": "medium",
        "latency_ms": 0,
        "provenance": {
            "baseline_source": "demo",
            "sources": [],
            "notes": [
                f"autosave_version:{autosave_version}",
                f"last_save:{datetime.utcnow().isoformat()}",
                "optimistic:true"
            ],
            "confidence": "medium",
            "used_priors": False,
            "prior_weight": 0.0,
        },
    }


def get_full(company_id: str, include_financial_summary=False, include_assets=False, include_benchmarks=False, include_uploads=False, include_integrations=False) -> Dict[str, Any]:
    data = _load_demo()
    # deterministic KPI list for demo
    kpis = [
        {"label": "overview_completed_pct", "value": data.get("completeness", {}).get("percent", 0.0)},
    ]
    
    # Mask EIN in general block for PII safety
    general = dict(data.get("general", {}))
    ein = general.get("ein")
    if ein and len(ein) >= 4:
        general["ein"] = "**-***" + ein[-4:]
    
    result = {
        "kpis": kpis,
        "general": general,
        "industry": data.get("industry", {}),
        "operations": data.get("operations", {}),
        "financial": data.get("financial", {}),
        "assets": data.get("assets", []),
        "customers": data.get("customers", {}),
        "risk": data.get("risk", {}),
        "objectives": data.get("objectives", {}),
        "uploads": data.get("uploads", []) if include_uploads else [],
        "completeness": data.get("completeness", {}),
        "_meta": make_meta(),
    }
    return result


def save_general(company_id: str, block: Dict[str, Any]) -> Dict[str, Any]:
    data = _load_demo()
    # store full EIN but keep as provided
    data["general"] = block
    _save_demo(data)
    # return masked EIN
    masked = dict(block)
    ein = masked.get("ein")
    if ein and len(ein) >= 4:
        masked["ein"] = "**-***" + ein[-4:]
    return masked


def save_industry(company_id: str, block: Dict[str, Any]) -> Dict[str, Any]:
    data = _load_demo()
    data["industry"] = block
    # If NAICS provided, set benchmark_set deterministically
    naics = block.get("naics")
    if naics and isinstance(naics, dict):
        block.setdefault("benchmark_set", f"bench-{naics.get('code')[:3]}")
    data["industry"] = block
    _save_demo(data)
    return block


def naics_search(q: str, limit: int = 8) -> List[Dict[str, str]]:
    # small deterministic mapping for demo
    samples = [
        ("238220", "Plumbing, Heating, and Air-Conditioning Contractors"),
        ("236115", "New Single-Family Housing Construction"),
        ("541511", "Custom Computer Programming Services"),
        ("722511", "Full-Service Restaurants"),
        ("523930", "Investment Advice"),
        ("621111", "Offices of Physicians (except Mental Health Specialists)"),
    ]
    ql = q.lower()
    results = [
        {"code": code, "title": title}
        for code, title in samples
        if ql in title.lower() or ql in code
    ]
    if not results:
        results = [{"code": samples[0][0], "title": samples[0][1]}]
    return results[:limit]


def save_operations(company_id: str, block: Dict[str, Any]) -> Dict[str, Any]:
    data = _load_demo()
    data["operations"] = block
    _save_demo(data)
    return block


def save_generic(company_id: str, section: str, block: Any):
    data = _load_demo()
    data[section] = block
    _save_demo(data)
    return block


def upsert_asset(company_id: str, asset: Dict[str, Any]):
    data = _load_demo()
    assets = data.get("assets", [])
    # upsert by id
    idx = next((i for i, a in enumerate(assets) if a.get("id") == asset.get("id")), None)
    if idx is None:
        assets.append(asset)
    else:
        assets[idx].update(asset)
    data["assets"] = assets
    _save_demo(data)
    return asset


def delete_asset(company_id: str, asset_id: str):
    data = _load_demo()
    assets = data.get("assets", [])
    for a in assets:
        if a.get("id") == asset_id:
            a["status"] = "deleted"
    _save_demo(data)
    return True


def list_uploads(company_id: str) -> List[Dict[str, Any]]:
    data = _load_demo()
    return data.get("uploads", [])


def upload_file(company_id: str, file_name: str, category: str, upload_id: Optional[str] = None) -> Dict[str, Any]:
    data = _load_demo()
    uid = upload_id or f"doc-{int(datetime.utcnow().timestamp())}"
    item = {"id": uid, "file": file_name, "category": category, "status": "processing"}
    data.setdefault("uploads", []).append(item)
    _save_demo(data)
    return item


def extract_upload(company_id: str, id: str) -> Dict[str, Any]:
    data = _load_demo()
    for u in data.get("uploads", []):
        if u.get("id") == id:
            # simulate extraction
            u.update({
                "type": u.get("category"),
                "issuer": "IRS" if "EIN" in u.get("file", "") or u.get("category") == "EIN" else "Unknown",
                "effective": "2018-04-01",
                "expiration": None,
                "status": "verified",
            })
            _save_demo(data)
            return u
    raise KeyError("upload not found")


def recalc_completeness(company_id: str) -> Dict[str, Any]:
    data = _load_demo()
    # required fields per section (simple demo mapping)
    required = {
        "general": ["name", "ein", "locations"],
        "industry": ["naics"],
        "operations": ["employees"],
        "financial": ["last_year_revenue"],
        "assets": ["assets"],
        "customers": ["annual_customers"],
        "risk": ["assessments"],
        "objectives": ["items"],
        "uploads": ["uploads"],
    }
    weights = {"general": 15, "industry": 15, "operations": 10, "financial": 15, "assets": 10, "customers": 10, "risk": 10, "objectives": 10, "uploads": 5}
    total_weight = sum(weights.values())
    score = 0.0
    missing = []
    for section, reqs in required.items():
        block = data.get(section)
        filled = 0
        total = len(reqs)
        for r in reqs:
            v = None
            if isinstance(block, dict):
                v = block.get(r)
            elif isinstance(block, list):
                v = block
            if v:
                filled += 1
        section_score = (filled / total) if total > 0 else 0
        score += section_score * (weights.get(section, 0) / total_weight)
        if section_score < 1.0:
            missing.append({"section": section.capitalize(), "item": "; ".join([r for r in reqs])})
    percent = round(score, 2)
    data["completeness"] = {"percent": percent, "missing": missing}
    _save_demo(data)
    return data["completeness"]


def calc_sync_confidence(company_id: str) -> float:
    data = _load_demo()
    conns = data.get("connectors", {})
    total = len(conns)
    connected = sum(1 for v in conns.values() if v.get("connected"))
    # recency weights
    weights = []
    for v in conns.values():
        ts = v.get("last_sync")
        if not ts:
            weights.append(0.0)
            continue
        last = datetime.fromisoformat(ts)
        age = datetime.utcnow() - last
        if age <= timedelta(hours=24):
            weights.append(1.0)
        elif age <= timedelta(days=7):
            weights.append(0.5)
        else:
            weights.append(0.2)
    avg_recency = sum(weights) / total if total else 0.0
    sync_score = 0.6 * (connected / total if total else 0.0) + 0.4 * avg_recency
    return round(sync_score, 2)


def export_profile(company_id: str, fmt: str) -> str:
    # return a fake signed URL
    return f"signed://business-profile.{fmt}"
