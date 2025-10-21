import json
import math
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from ..schemas import Asset, WorkOrder, MaintenancePlan, TelemetrySample


DEMO_PATH = "data/demo/assets.json"


def _load_demo():
    if os.path.exists(DEMO_PATH):
        with open(DEMO_PATH, "r") as f:
            return json.load(f)
    # synthesize minimal demo deterministically
    return {
        "assets": [],
        "work_orders": [],
        "maintenance_plans": [],
        "documents": [],
        "utilization": {},
        "depreciation": {},
    }


def provenance_baseline():
    return {"baseline_source": "quickbooks_demo", "sources": ["cmms_demo", "telematics_demo"], "notes": [], "confidence": "medium", "used_priors": False, "prior_weight": 0.0}


def meta_top(latency_ms=5, confidence="medium"):
    return {"source": "lightsignal.orchestrator", "confidence": confidence, "latency_ms": latency_ms, "provenance": provenance_baseline()}


def compute_utilization(asset_id: str, data: Dict[str, Any], range: str = "30d"):
    # use last period if available
    series = data.get("utilization", {}).get(asset_id, [])
    if not series:
        return {"utilization_pct": None, "availability_pct": None, "downtime_hours": 0}
    last = series[0]
    active = last.get("active_hours", 0)
    avail = last.get("available_hours", 168)
    utilization_pct = active / avail if avail > 0 else None
    # estimate downtime from work orders with open status
    wos = data.get("work_orders", [])
    downtime = 0
    for w in wos:
        if w.get("asset_id") == asset_id and w.get("status") == "open":
            downtime += 8
    availability = (avail - downtime) / avail if avail > 0 else None
    return {"utilization_pct": round(utilization_pct * 100, 2) if utilization_pct is not None else None, "availability_pct": round(availability * 100, 2) if availability is not None else None, "downtime_hours": downtime}


def health_score_for_asset(asset: Dict[str, Any], data: Dict[str, Any]):
    # availability 30%, maintenance compliance 25%, faults freq 20%, freshness 15%, utilization balance 10%
    util = compute_utilization(asset.get("asset_id"), data)
    availability = util.get("availability_pct") or 0
    # maintenance compliance: crude - fraction of closed WOs
    wos = [w for w in data.get("work_orders", []) if w.get("asset_id") == asset.get("asset_id")]
    closed = len([w for w in wos if w.get("status") == "closed"])
    total = len(wos) if wos else 1
    compliance = closed / total if total > 0 else 1.0
    faults = len([w for w in wos if w.get("status") == "open"])  # treat open as fault proxy
    faults_score = max(0, 1 - (faults / 5))
    freshness = 1.0 if asset.get("odometer") is not None else 0.5
    utilization_balance = 1.0 if (util.get("utilization_pct") or 0) < 80 else 0.6

    score = (
        (availability / 100.0) * 30 +
        (compliance) * 25 +
        (faults_score) * 20 +
        (freshness) * 15 +
        (utilization_balance) * 10
    )
    return int(max(0, min(100, round(score))))


def load_assets(company_id: str = "demo"):
    # only demo supported for now
    data = _load_demo()
    return data


_IN_MEMORY_WOS: List[Dict[str, Any]] = []
_IN_MEMORY_TELEMETRY: List[Dict[str, Any]] = []


def create_work_order(company_id: str, asset_id: str, priority: str, summary: str, sla_hours: Optional[int] = None):
    # generate id
    nid = f"WO-{2200 + len(_IN_MEMORY_WOS) + len(load_assets().get('work_orders', [])) + 1}"
    wo = {"wo_id": nid, "asset_id": asset_id, "priority": priority, "summary": summary, "status": "open", "created_at": datetime.now(timezone.utc).isoformat(), "closed_at": None}
    _IN_MEMORY_WOS.append(wo)
    return wo


def schedule_maintenance(company_id: str, asset_id: str, plan: Dict[str, Any]):
    # accept and pretend to persist
    plan_rec = {"plan_id": f"MP-{int(math.fsum([ord(c) for c in asset_id])%1000)}", "asset_id": asset_id}
    plan_rec.update(plan)
    # not persisting to disk for demo
    return True


def replace_vs_repair_calc(req: Dict[str, Any], data: Dict[str, Any]):
    # Inputs - req is already a dict from model_dump()
    repair_cost_year = float(req.get("repair_cost_year", 0))
    downtime_cost_year = float(req.get("downtime_cost_year", 0))
    replacement_cost = float(req.get("replacement_cost", 0))
    life_months = int(req.get("replacement_useful_life_months", 60))
    discount = float(req.get("discount_rate_pct", 8)) / 100.0
    prod_gain = float(req.get("expected_productivity_gain_pct", 0)) / 100.0

    # 3-year TCO for repair = sum of (repair_cost + downtime_cost) * years(3)
    annual_repair = repair_cost_year + downtime_cost_year
    tco_repair_3 = annual_repair * 3

    # replacement: amortize replacement cost over life, consider productivity gain as negative cost
    amort_annual = replacement_cost / (life_months / 12.0)
    prod_savings_annual = amort_annual * prod_gain
    tco_replace_3 = (amort_annual - prod_savings_annual) * 3

    # NPV comparison over 3 years, simple discounting
    def npv_annuity(annual):
        npv = 0.0
        for y in range(1, 4):
            npv += annual / ((1 + discount) ** y)
        return npv

    npv_repair = npv_annuity(annual_repair)
    npv_replace = npv_annuity(amort_annual - prod_savings_annual) + 0  # purchase treated via amort annual

    npv_savings = round(npv_repair - npv_replace, 2)

    # payback months = replacement_cost / annual_savings if positive
    annual_savings = annual_repair - (amort_annual - prod_savings_annual)
    payback_months = None
    if annual_savings > 0:
        payback_months = int(round((replacement_cost) / annual_savings * 12))

    # heuristic recommendation
    recommendation = "repair"
    if (annual_repair) > 0.6 * (replacement_cost / (life_months / 12.0)):
        recommendation = "replace"
    elif abs(npv_savings) < 1000:
        recommendation = "borderline"

    assumptions = {"mtbf_hours": 520, "mttr_hours": 2.1}

    return {
        "tco_3yr_repair": round(tco_repair_3, 2),
        "tco_3yr_replace": round(tco_replace_3, 2),
        "npv_savings": npv_savings,
        "payback_months": payback_months,
        "recommendation": recommendation,
        "assumptions": assumptions,
        "_meta": meta_top()
    }


def import_rows(company_id: str, rows: List[Dict[str, Any]]):
    imported = 0
    skipped = 0
    warnings = []
    for r in rows:
        if not r.get("asset_id"):
            skipped += 1
            warnings.append("missing asset_id")
            continue
        imported += 1
    return {"imported": imported, "skipped": skipped, "warnings": warnings, "_meta": meta_top()}


def extract_document_dates(company_id: str, docs: List[Dict[str, Any]]):
    """Enhanced demo document date extraction with regex patterns"""
    hints = []
    
    # Common date patterns for expiration dates
    date_patterns = [
        r'expir(?:es?|ation)\s*:?\s*(\d{4}-\d{2}-\d{2})',  # expires: 2025-12-01
        r'expir(?:es?|ation)\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4})',  # expires January 1, 2025
        r'valid\s+until\s+(\w+\s+\d{4})',  # valid until March 2026
        r'due\s*:?\s*(\d{4}-\d{2}-\d{2})',  # due: 2025-11-15
        r'(\d{1,2}/\d{1,2}/\d{4})\s*expir',  # 12/01/2025 expir
    ]
    
    for doc in docs:
        doc_id = doc.get("doc_id")
        text = (doc.get("text") or "").lower()
        found_hints = []
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Try to normalize date format
                try:
                    if '-' in match:  # ISO format
                        parsed_date = datetime.strptime(match, "%Y-%m-%d")
                    elif '/' in match:  # MM/DD/YYYY
                        parsed_date = datetime.strptime(match, "%m/%d/%Y")
                    else:  # Natural language
                        # Simple parsing for demo - could use dateutil.parser in real implementation
                        parsed_date = datetime.strptime("2025-12-01", "%Y-%m-%d")  # fallback
                    
                    # Determine field type based on document type and keywords
                    field = "expiration_date"
                    if "warranty" in text:
                        field = "warranty_expires"
                    elif "insurance" in text:
                        field = "insurance_expires"
                    elif "registration" in text:
                        field = "registration_expires"
                    elif "certification" in text or "cert" in text:
                        field = "certification_expires"
                    
                    found_hints.append({
                        "field": field,
                        "value": parsed_date.strftime("%Y-%m-%d"),
                        "original_text": match,
                        "confidence": "medium" if '-' in match else "low"
                    })
                    
                except Exception:
                    # Fallback hint for unparseable dates
                    found_hints.append({
                        "field": "expiration_date", 
                        "value": "2025-12-01",
                        "original_text": match,
                        "confidence": "low"
                    })
        
        # If no specific patterns found but contains expiration keywords
        if not found_hints and any(word in text for word in ["expire", "expiration", "due", "valid until"]):
            found_hints.append({
                "field": "expiration_date",
                "value": "2025-12-01",
                "original_text": "contains expiration keywords",
                "confidence": "low"
            })
        
        hints.append({
            "doc_id": doc_id,
            "hints": found_hints,
            "confidence": "medium" if found_hints else "low"
        })
    
    return {"documents": hints, "_meta": meta_top()}


def ingest_telemetry(company_id: str, asset_id: str, samples: List[Dict[str, Any]]):
    for s in samples:
        rec = {"company_id": company_id, "asset_id": asset_id, "sample": s}
        _IN_MEMORY_TELEMETRY.append(rec)
    return {"ok": True, "_meta": meta_top()}


def search_registry(company_id: str, query: Optional[str], filters: Optional[Dict[str, Any]]):
    data = load_assets(company_id)
    items = data.get("assets", [])
    res = []
    q = (query or "").lower()
    for it in items:
        ok = True
        if q:
            ok = q in (it.get("name") or "").lower() or q in (it.get("asset_id") or "").lower() or q in (it.get("category") or "").lower()
        if not ok:
            continue
        if filters:
            for k, v in filters.items():
                if k not in it or (v is not None and str(it.get(k)).lower() != str(v).lower()):
                    ok = False
                    break
        if ok:
            res.append(it)
    return {"results": res, "_meta": meta_top()}
    data = load_assets(company_id)
    items = data.get("assets", [])
    res = []
    q = (query or "").lower()
    for it in items:
        ok = True
        if q:
            ok = q in (it.get("name") or "").lower() or q in (it.get("asset_id") or "").lower() or q in (it.get("category") or "").lower()
        if not ok:
            continue
        if filters:
            for k, v in filters.items():
                if k not in it or (v is not None and str(it.get(k)).lower() != str(v).lower()):
                    ok = False
                    break
        if ok:
            res.append(it)
    return {"results": res, "_meta": meta_top()}


def full_overview(req: Dict[str, Any]):
    # req is already a dict from model_dump()
    company_id = req.get("company_id", "demo")
    data = load_assets(company_id)
    # Build top-level response keys
    assets = data.get("assets", [])
    registry = assets if req.get("include_registry", True) else []
    work_orders = data.get("work_orders", []) + _IN_MEMORY_WOS
    # KPIs: counts and utilization averages
    kpis = {"total_assets": len(assets), "active_assets": len([a for a in assets if a.get("status") == "active"]), "avg_utilization_pct": None}
    util_vals = []
    for a in assets:
        u = compute_utilization(a.get("asset_id"), data)
        if u.get("utilization_pct") is not None:
            util_vals.append(u.get("utilization_pct"))
    if util_vals:
        kpis["avg_utilization_pct"] = round(sum(util_vals) / len(util_vals), 2)

    # Valuation (simple straight-line monthly depreciation current book value approximation)
    valuation = {}
    for a in assets:
        dep = data.get("depreciation", {}).get(a.get("asset_id")) or {"cost": a.get("cost") or 0, "salvage": a.get("salvage") or 0, "useful_life_months": a.get("useful_life_months") or 60}
        monthly = (dep["cost"] - dep["salvage"]) / max(1, dep["useful_life_months"])
        valuation[a.get("asset_id")] = {"book_value_monthly": round(monthly, 2), "current_book": round(max(0, dep["cost"] - monthly * 12), 2)}

    # utilization series
    utilization = data.get("utilization", {})

    # alerts: warranties expiring in next 60 days
    alerts = []
    now = datetime.now()
    for a in assets:
        for fld, label in (("warranty_expires", "warranty"), ("insurance_expires", "insurance")):
            v = a.get(fld)
            if v:
                try:
                    d = datetime.fromisoformat(v)
                except Exception:
                    try:
                        d = datetime.strptime(v, "%Y-%m-%d")
                    except Exception:
                        continue
                delta = (d - now).days
                if delta <= 60:
                    alerts.append({"asset_id": a.get("asset_id"), "type": label, "expires_in_days": delta})

    # quick actions and export placeholders
    quick_actions = {"create_work_order": True, "schedule_maintenance": True}
    export = {"csv": "/export/assets.csv"}

    # health scores
    registry_with_health = []
    for a in assets:
        ah = dict(a)
        ah["health_score"] = health_score_for_asset(a, data)
        registry_with_health.append(ah)

    return {
        "kpis": kpis,
        "integrations": ["quickbooks_demo", "cmms_demo"],
        "registry": registry_with_health,
        "work_orders": work_orders,
        "valuation": valuation,
        "utilization": utilization,
        "alerts": alerts,
        "documents": data.get("documents", []),
        "quick_actions": quick_actions,
        "export": export,
        "_meta": meta_top()
    }
