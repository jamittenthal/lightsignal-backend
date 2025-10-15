# /backend/main.py
import os, json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ---------- Paths / Config ----------
BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT   = BACKEND_DIR.parent

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # may be None
# Accept either env var name for your assistant ID
ASSISTANT_ID = os.getenv("ASSISTANT_ID_ORCH") or os.getenv("ASST_ORCHESTRATOR_ID")

AI_TABS_DIR = REPO_ROOT / "ai" / "tabs"         # expects /ai/tabs/*.yaml at repo root
DATA_DIR    = REPO_ROOT / "data" / "companies"  # expects /data/companies/<id>/profile.json

# ---------- App ----------
app = FastAPI(title="LightSignal Backend")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- OpenAI client (lazy) ----------
_openai_client = None
def get_openai_client():
    global _openai_client
    if _openai_client is None and OPENAI_API_KEY:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client

# ---------- Intent registry ----------
from .ai_registry import get_tab_spec, list_intents, list_files  # local module

# ---------- Helpers ----------
def load_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def get_profile(company_id: str) -> dict:
    return load_json(DATA_DIR / company_id / "profile.json")

def get_financials(company_id: str) -> dict:
    # TODO: replace with real QuickBooks fetch
    return {
        "financial_overview": {
            "revenue_mtd": 31666.67,
            "net_income_mtd": -3166.67,
            "cash_available": 52000
        }
    }

def call_orchestrator(tab_spec: dict, context: dict) -> dict:
    # If OpenAI not configured yet, return stub so you can still test end-to-end
    if not OPENAI_API_KEY or not ASSISTANT_ID:
        return {
            "stub": True,
            "message": "OpenAI not configured (missing OPENAI_API_KEY or Assistant ID).",
            "echo": {"tab_spec_present": bool(tab_spec), "context_keys": list(context.keys())}
        }

    client = get_openai_client()
    # Threads API (simple). Swap to Responses API if you prefer.
    thread = client.beta.threads.create(
        messages=[{"role":"user","content":json.dumps({"tab_spec": tab_spec, "context": context})}]
    )
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    msgs = client.beta.threads.messages.list(thread_id=thread.id)
    content = msgs.data[0].content[0].text.value
    return json.loads(content)

# ---------- Routes ----------
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/version")
def version():
    # Render exposes commit SHA as env var RENDER_GIT_COMMIT
    return {
        "commit": os.getenv("RENDER_GIT_COMMIT", "unknown"),
        "has_openai_key": bool(OPENAI_API_KEY),
        "has_assistant_id": bool(ASSISTANT_ID)
    }

@app.get("/debug")
def debug():
    return {
        "repo_root": str(REPO_ROOT),
        "ai_tabs_dir": str(AI_TABS_DIR),
        "data_dir": str(DATA_DIR),
        "exists_ai_tabs": AI_TABS_DIR.exists(),
        "exists_data_dir": DATA_DIR.exists(),
        "yaml_files_found": list_files(),
        "intents_now": list_intents(),
        "assistant_id_env_used": (
            "ASSISTANT_ID_ORCH" if os.getenv("ASSISTANT_ID_ORCH")
            else ("ASST_ORCHESTRATOR_ID" if os.getenv("ASST_ORCHESTRATOR_ID") else None)
        ),
    }

@app.get("/intents")
def intents():
    return {"intents": list_intents()}

@app.post("/api/intent")
def api_intent(payload: dict):
    intent      = payload.get("intent")
    company_id  = payload.get("company_id", "demo")
    user_input  = payload.get("input", {})

    tab_spec = get_tab_spec(intent)
    if not tab_spec:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Unknown intent: {intent}", "available_intents": list_intents()}
        )

    profile    = get_profile(company_id)
    financials = get_financials(company_id)

    context = {
        "company_id": company_id,
        "intent": intent,
        "input": user_input,
        "profile": profile,
        "financials": financials,
        "spec_dir": str(AI_TABS_DIR)
    }
    return call_orchestrator(tab_spec, context)
