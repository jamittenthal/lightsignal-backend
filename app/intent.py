# app/intent.py
from typing import Any, Dict, List
from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from .agents import call_orchestrator, call_analyst, call_scout
import json

router = APIRouter()

class IntentPayload(BaseModel):
    intent: str                 # e.g., "opportunities", "payroll_hiring"
    company_id: str = "demo"
    input: Dict[str, Any] = {}

# ---------- Utilities ----------

def _json_or_empty(s: str) -> Dict[str, Any]:
    try:
        if not isinstance(s, str):
            return {}
        if "```" in s:
            s = s.replace("```json", "```")
            parts = s.split("```")
            for p in parts:
                if "{" in p and "}" in p:
                    j = p[p.index("{"): p.rfind("}")+1]
                    return json.loads(j)
        return json.loads(s)
    except Exception:
        return {}

def _safe_envelope(cid: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "scenario_type": "general_question",
        "base": {"kpis": {}},
        "scenario": {"kpis": {}},
        "delta": {"kpis": {}},
        "verdict": {"affordable": True, "summary": "OK"},
        "insights": ["(default envelope)"],
        "benchmarks": [],
        "visuals": [],
        "assumptions": {"company_id": cid, "inputs": inputs},
    }

# ---------- Prompt builders (contracts) ----------

def prompt_header(company_id: str) -> str:
    return (
        "You are part of LightSignal, an SMB decision copilot.\n"
        f"Company context: company_id={company_id} (assume HVAC/Services unless otherwise specified).\n"
        "Return STRICT JSON only. No prose. No markdown. No code fences.\n"
    )

def prompt_contract_generic(intent: str, company_id: str, inputs: Dict[str, Any]) -> str:
    """
    Generic contract: ensures 'insights' always exists so UI renders.
    """
    return (
        prompt_header(company_id)
        + "Task: Respond to the intent and inputs with concise, decision-ready analysis.\n"
        f"Intent: {intent}\n"
        f"Inputs: {json.dumps(inputs)}\n\n"
        "JSON schema (STRICT):\n"
        "{\n"
        '  "kpis": { "any_metric": number, "...": number },\n'
        '  "insights": ["short actionable bullet", "..."],\n'
        '  "benchmarks": [{"metric":"string","value":number,"peer_percentile":number}],\n'
        '  "visuals": [{"type":"bar|line","title":"string","labels":[...],"values":[...]}],\n'
        '  "assumptions": {"company_id":"string","inputs":{}}\n'
        "}\n"
        "Constraints: Keep numbers reasonable; if something is unknown, omit it.\n"
    )

def prompt_contract_opportunities(company_id: str, inputs: Dict[str, Any]) -> str:
    """
    Contract for the Opportunities tab: always return insights + items.
    """
    return (
        prompt_header(company_id)
        + "Task: Find near-term business opportunities and risks (grants/events/bids/weather-driven demand spikes/partner leads).\n"
        f"Inputs: {json.dumps(inputs)}\n\n"
        "JSON schema (STRICT):\n"
        "{\n"
        '  "kpis": {\n'
        '    "active_count": number,\n'
        '    "potential_value": number,\n'
        '    "avg_fit_score": number,\n'
        '    "event_readiness": number,\n'
        '    "historical_roi": number\n'
        "  },\n"
        '  "insights": ["short actionable bullet", "..."],\n'
        '  "items": [\n'
        "    {\n"
        '      "title":"string",\n'
        '      "category":"grant|event|bid|partner|weather|lead",\n'
        '      "date":"YYYY-MM-DD",\n'
        '      "deadline":"YYYY-MM-DD",\n'
        '      "fit_score": number,\n'
        '      "roi_est": number,\n'
        '      "weather": "optional string if weather-related",\n'
        '      "link":"optional url"\n'
        "    }\n"
        "  ],\n"
        '  "benchmarks": [{"metric":"string","value":number,"peer_percentile":number}],\n'
        '  "visuals": [{"type":"bar|line","title":"string","labels":[...],"values":[...]}],\n'
        '  "assumptions": {"company_id":"string","inputs":{}}\n'
        "}\n"
        "Constraints: No markdown. No extra keys. Dates in ISO format if used.\n"
    )

def build_prompt(intent: str, company_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns dict with which agent to call and the exact text to send.
    """
    i = intent.lower().strip()

    # Map intents to agents + contracts
    if i in ("opportunities",):
        return {
            "agent": "scout",
            "text": prompt_contract_opportunities(company_id, inputs),
        }

    elif i in (
        "financial_overview", "debt_management_advisor", "payroll_hiring",
        "tax_optimization", "business_health", "asset_management",
        "inventory", "multilocation_inventory", "success_planning",
    ):
        return {
            "agent": "analyst",
            "text": prompt_contract_generic(i, company_id, inputs),
        }

    elif i.startswith("scenario_"):
        return {
            "agent": "orchestrator",
            "text": prompt_contract_generic(i, company_id, inputs),
        }

    # default route → orchestrator with generic contract
    return {
        "agent": "orchestrator",
        "text": prompt_contract_generic(i, company_id, inputs),
    }

# ---------- Route ----------

@router.post("/api/intent")
def route_intent(payload: IntentPayload):
    intent = (payload.intent or "").strip().lower()
    cid = payload.company_id
    inputs = payload.input or {}

    try:
        plan = build_prompt(intent, cid, inputs)
        text = plan["text"]

        if plan["agent"] == "analyst":
            raw = call_analyst(text)
        elif plan["agent"] == "scout":
            raw = call_scout(text)
        else:
            raw = call_orchestrator(text)

        parsed = _json_or_empty(raw)

        if isinstance(parsed, dict) and "error" in parsed:
            return JSONResponse(
                status_code=500,
                content={"intent": intent, "company_id": cid, "error": parsed["error"]}
            )

        # Ensure we always return something the UI can render
        if not isinstance(parsed, dict) or "insights" not in parsed:
            parsed = _safe_envelope(cid, inputs)

        # Always attach assumptions
        parsed.setdefault("assumptions", {"company_id": cid, "inputs": inputs})

        return {"intent": intent, "company_id": cid, "result": parsed}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"intent": intent, "company_id": cid, "error": f"{type(e).__name__}: {str(e)}"}
        )
