# /backend/main.py
import os, json
from pathlib import Path
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

# Paths
BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT   = BACKEND_DIR.parent

# Env / config
OPENAI_API_KEY   = os.environ["OPENAI_API_KEY"]
ASSISTANT_ID_ORCH = os.environ["ASSISTANT_ID_ORCH"]

# Defaults point to folders at repo root
AI_TABS_DIR = REPO_ROOT / "ai" / "tabs"
DATA_DIR    = REPO_ROOT / "data" / "companies"

# App
app = FastAPI(title="LightSignal Backend")
router = APIRouter()
client = OpenAI(api_key=OPENAI_API_KEY)

# CORS (allow your Vercel URL; "*" is fine for quick testing)
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Intent registry (sibling module)
from .ai_registry import get_tab_spec, list_intents  # relative import from /backend

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
    # TODO: replace with your real QuickBooks fetch
    return {
        "financial_overview": {
            "revenue_mtd": 31666.67,
            "net_income_mtd": -3166.67,
            "cash_available": 52000
        }
    }

def call_orchestrator(tab_spec: dict, context: dict) -> dict:
    # Threads API (simple). Swap to Responses API if you prefer.
    thread = client.beta.threads.create(
        messages=[{"role":"user","content":json.dumps({"tab_spec": tab_spec, "context": context})}]
    )
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID_ORCH)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    msgs = client.beta.threads.messages.list(thread_id=thread.id)
    content = msgs.data[0].content[0].text.value
    return json.loads(content)

@app.get("/health")
def health():
    return {"ok": True}

@router.get("/intents")
def intents():
    return {"intents": list_intents()}

@router.post("/api/intent")
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

app.include_router(router)
