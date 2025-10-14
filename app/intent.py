# app/intent.py
from typing import Any, Dict
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

@router.post("/api/intent")
def route_intent(payload: IntentPayload):
    intent = (payload.intent or "").strip().lower()
    cid = payload.company_id
    inputs = payload.input or {}

    try:
        if intent in (
            "financial_overview", "debt_management_advisor", "payroll_hiring",
            "tax_optimization", "business_health", "asset_management",
            "inventory", "multilocation_inventory", "success_planning",
        ):
            raw = call_analyst(f"intent={intent}; company_id={cid}; inputs={json.dumps(inputs)}")

        elif intent in (
            "opportunities", "demand_forecasting", "reputation_intel",
            "fraud_compliance", "regulatory_risk", "market_research",
        ):
            raw = call_scout(f"intent={intent}; company_id={cid}; inputs={json.dumps(inputs)}")

        elif intent.startswith("scenario_"):
            raw = call_orchestrator(f"intent={intent}; company_id={cid}; inputs={json.dumps(inputs)}")

        else:
            raw = call_orchestrator(f"intent={intent}; company_id={cid}; inputs={json.dumps(inputs)}")

        parsed = _json_or_empty(raw)

        # If the assistant returned an {error:"..."} string, pass that back clearly
        if isinstance(parsed, dict) and "error" in parsed:
            return JSONResponse(
                status_code=500,
                content={"intent": intent, "company_id": cid, "error": parsed["error"]}
            )

        if not isinstance(parsed, dict) or "insights" not in parsed:
            parsed = _safe_envelope(cid, inputs)

        return {"intent": intent, "company_id": cid, "result": parsed}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"intent": intent, "company_id": cid, "error": f"{type(e).__name__}: {str(e)}"}
        )
