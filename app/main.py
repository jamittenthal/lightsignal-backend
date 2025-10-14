# app/main.py
import os
import json
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

# --- Include the unified Intent router ---
from .intent import router as intent_router

# --- Optional: OpenAI orchestrator wiring (for /api/orchestrator* endpoints) ---
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT = os.getenv("OPENAI_PROJECT", None)
ASST_ORCH_ID = os.getenv("ASST_ORCHESTRATOR_ID")          # e.g., asst_...
ASST_ANALYST_ID = os.getenv("ASST_FINANCE_ANALYST_ID")     # optional
ASST_SCOUT_ID = os.getenv("ASST_RESEARCH_SCOUT_ID")        # optional

client_kwargs: Dict[str, Any] = {}
if OPENAI_API_KEY:
    client_kwargs["api_key"] = OPENAI_API_KEY
if OPENAI_PROJECT:
    client_kwargs["project"] = OPENAI_PROJECT
_openai: Optional[OpenAI] = OpenAI(**client_kwargs) if client_kwargs else None

# ------------------------------------------------------------------------------
# FastAPI app & CORS
# ------------------------------------------------------------------------------
app = FastAPI(title="LightSignal Backend")

FRONTEND_URL = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatPayload(BaseModel):
    messages: List[ChatMessage]

class PromptPayload(BaseModel):
    prompt: str

# ------------------------------------------------------------------------------
# Health
# ------------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True, "orchestrator_set": bool(ASST_ORCH_ID)}

# ------------------------------------------------------------------------------
# Serve your OpenAPI YAML (if present at app/ai/openapi.yaml)
# ------------------------------------------------------------------------------
@app.get("/ai/openapi.yaml", response_class=PlainTextResponse)
def serve_openapi_yaml():
    yaml_path = os.path.join(os.path.dirname(__file__), "ai", "openapi.yaml")
    if not os.path.exists(yaml_path):
        raise HTTPException(status_code=404, detail="openapi.yaml not found")
    with open(yaml_path, "r", encoding="utf-8") as f:
        return f.read()

# ------------------------------------------------------------------------------
# Existing: Orchestrator endpoints (one-shot & chat-style)
# These use OpenAI and expect your Assistant to return JSON-in-text.
# ------------------------------------------------------------------------------
def _extract_json(text: str) -> Dict[str, Any]:
    """Best effort to extract JSON from a model response (handles ```json fences)."""
    try:
        if "```" in text:
            text = text.replace("```json", "```")
            parts = text.split("```")
            for p in parts:
                if "{" in p and "}" in p:
                    p = p[p.index("{"): p.rfind("}") + 1]
                    return json.loads(p)
        return json.loads(text)
    except Exception:
        return {"raw": text}

def _chat_complete(messages: List[Dict[str, str]]) -> str:
    if not _openai:
        raise HTTPException(status_code=500, detail="OpenAI client not configured")
    # You can swap to Responses API; this keeps chat.completions for simplicity.
    resp = _openai.chat.completions.create(
        model="gpt-5.1-mini",
        messages=messages,
        temperature=0.2,
    )
    return resp.choices[0].message.content or "{}"

@app.post("/api/orchestrator")
def orchestrator_one_shot(payload: PromptPayload):
    """
    One-shot call: send a structured prompt to your Orchestrator Assistant.
    Frontend typically sends: intent=..., company_id=..., inputs={...}
    """
    if not ASST_ORCH_ID:
        # Fallback: call model without a dedicated assistant id
        text = _chat_complete([
            {"role": "system", "content": "You are the LightSignal Orchestrator. Return JSON only."},
            {"role": "user", "content": payload.prompt}
        ])
        return _extract_json(text)

    # If you want to actually use the Assistant ID, you can still call via chat with a hint
    text = _chat_complete([
        {"role": "system", "content": f"You are the LightSignal Orchestrator (id {ASST_ORCH_ID}). Return JSON only."},
        {"role": "user", "content": payload.prompt},
    ])
    return _extract_json(text)

@app.post("/api/orchestrator_chat")
def orchestrator_chat(payload: ChatPayload):
    """
    Chat-style call: accepts {messages:[{role,content},...]} and returns JSON-ish.
    """
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages[] required")

    preface = [{"role": "system", "content": "You are the LightSignal Orchestrator. Return JSON only."}]
    user_msgs = [{"role": m.role, "content": m.content} for m in payload.messages]
    text = _chat_complete(preface + user_msgs)
    parsed = _extract_json(text)

    # Ensure a minimal envelope so the UI never breaks
    if not isinstance(parsed, dict) or "insights" not in parsed:
        parsed = {
            "scenario_type": "general_question",
            "base": {"kpis": {}},
            "scenario": {"kpis": {}},
            "delta": {"kpis": {}},
            "verdict": {"affordable": True, "summary": "OK"},
            "insights": ["Result returned.", "Adjust agent instructions to refine shape."],
            "benchmarks": [],
            "visuals": [],
            "assumptions": {}
        }
    return parsed

# ------------------------------------------------------------------------------
# Demo/Stub endpoints for tabs (keep these so your UI stays populated)
# ------------------------------------------------------------------------------
@app.get("/api/dashboard")
def dashboard():
    return {
        "kpis": {
            "revenue_mtd": 152000,
            "net_margin_pct": 0.12,
            "cashflow_mtd": 38000,
            "runway_months": 7.8,
            "ai_health": 0.86
        },
        "snapshot": "Revenue up 7.2% vs last month; expenses flat; margin 28%.",
        "alerts": [
            {"level": "red", "text": "Low cash alert if runway < 3 months (currently 7.8)"},
            {"level": "yellow", "text": "Spending spike detected in Marketing (watch)"},
            {"level": "green", "text": "Ahead of target this month"}
        ],
        "insights": [
            "Profit margin improved; AR collection slowed slightly.",
            "Labor costs trending 11% above peers.",
            "Marketing +5% appears sustainable."
        ],
        "reminders": [
            {"text": "Quarterly tax payment due in 6 days."},
            {"text": "Renew business insurance next week."},
            {"text": "Invoice follow-up: 3 clients overdue."}
        ],
        "provenance": {"source": "quickbooks", "confidence": 0.7}
    }

@app.get("/api/financial_overview")
def financial_overview():
    return {
        "kpis": {
            "revenue_ttm": 2300000,
            "gross_profit_ttm": 920000,
            "ebitda_ttm": 395000,
            "net_income_ttm": 245000,
            "cash_on_hand": 210000,
            "runway_months": 8.4,
            "gross_margin": 0.40,
            "ebitda_margin": 0.17,
            "current_ratio": 1.7,
            "debt_to_equity": 0.6
        },
        "benchmarks": [
            {"metric": "Gross Margin", "value": 0.40, "peer_percentile": 70},
            {"metric": "EBITDA Margin", "value": 0.17, "peer_percentile": 62}
        ],
        "insights": [
            "COGS creep last quarter; monitor vendor pricing.",
            "Runway healthy; consider early-pay discounts to accelerate AR."
        ],
        "provenance": {"source": "quickbooks", "confidence": 0.65}
    }

# ------------------------------------------------------------------------------
# Mount the unified Intent API (tabs call POST /api/intent with {intent, ...})
# ------------------------------------------------------------------------------
app.include_router(intent_router)
