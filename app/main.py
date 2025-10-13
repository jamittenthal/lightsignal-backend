import os
import time
import json
from typing import List, Optional
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# local modules
from .demo_financials import get_demo_financials, get_demo_profile
from .finance_models import compute_all_kpis, default_benchmarks

load_dotenv()

app = FastAPI()

# CORS: allow frontend (Vercel) to call backend (Render)
allowed_origins = [
    "https://lightsignal-frontend.vercel.app",
    "https://*.vercel.app",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    project=os.getenv("OPENAI_PROJECT"),
)

@app.get("/health")
def health():
    return {"ok": True, "project": os.getenv("OPENAI_PROJECT")}

# ---------- Helpers for Assistants ----------
def _wait_for_run(thread_id: str, run_id: str):
    while True:
        status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if status.status == "completed":
            return
        if status.status in ["failed", "cancelled", "expired"]:
            raise Exception(f"Run ended with status: {status.status}")
        time.sleep(1)

def _latest_text(thread_id: str) -> str:
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return messages.data[0].content[0].text.value

def _parse_json_or_none(raw: str) -> Optional[dict]:
    try:
        return json.loads(raw)
    except Exception:
        cleaned = raw.strip().strip("`")
        try:
            return json.loads(cleaned)
        except Exception:
            return None

def run_assistant(assistant_id: str, prompt: str) -> str:
    thread = client.beta.threads.create(messages=[{"role": "user", "content": prompt}])
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
    _wait_for_run(thread.id, run.id)
    return _latest_text(thread.id)

# ---------- Existing single-prompt endpoints ----------
@app.post("/api/orchestrator")
async def orchestrator(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "render_financial_overview for company_id=demo")
    try:
        asst_id = os.getenv("ORCHESTRATOR_ID")
        raw = run_assistant(asst_id, prompt)
        parsed = _parse_json_or_none(raw)
        return JSONResponse(content=parsed if parsed is not None else {"text": raw})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/finance")
async def finance(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "analyze company financials")
    try:
        asst_id = os.getenv("FINANCE_ANALYST_ID")
        raw = run_assistant(asst_id, prompt)
        parsed = _parse_json_or_none(raw)
        return JSONResponse(content=parsed if parsed is not None else {"text": raw})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/research")
async def research(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "latest SMB signals")
    try:
        asst_id = os.getenv("RESEARCH_SCOUT_ID")
        raw = run_assistant(asst_id, prompt)
        parsed = _parse_json_or_none(raw)
        return JSONResponse(content=parsed if parsed is not None else {"text": raw})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ---------- NEW: Chat endpoint for Scenarios ----------
class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

@app.post("/api/orchestrator_chat")
async def orchestrator_chat(req: ChatRequest):
    try:
        asst_id = os.getenv("ORCHESTRATOR_ID")
        thread = client.beta.threads.create(messages=[m.dict() for m in req.messages])
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=asst_id)
        _wait_for_run(thread.id, run.id)
        text = _latest_text(thread.id)
        parsed = _parse_json_or_none(text)
        return JSONResponse(content={"message": {"role": "assistant", "content": text}, "parsed": parsed})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ---------- NEW: Demo-Mode Financial Engine ----------
@app.get("/api/finance/get_financials")
def api_get_financials(company_id: str = Query("demo")):
    """
    Returns normalized financials and a simple business profile.
    Structure:
    {
      "profile": {...},
      "pl": [{"month":"2024-01","revenue":...,"cogs":...,"opex":...,"other":...}, ... 12 months],
      "bs": {"cash":..., "receivables":..., "inventory":..., "current_liab":..., "debt":..., "equity":...},
      "cf": {"operating":..., "investing":..., "financing":...}
    }
    """
    profile = get_demo_profile(company_id)
    pl, bs, cf = get_demo_financials(company_id)
    return {"profile": profile, "pl": pl, "bs": bs, "cf": cf}

@app.get("/api/finance/benchmarks")
def api_benchmarks(company_id: str = Query("demo")):
    """
    Returns peer benchmark percentiles for key metrics (mock).
    """
    profile = get_demo_profile(company_id)
    b = default_benchmarks(profile)
    return {"profile": profile, "benchmarks": b}

@app.get("/api/finance/compute_kpis")
def api_compute_kpis(company_id: str = Query("demo")):
    """
    Computes KPIs/ratios from normalized demo financials + profile.
    """
    profile = get_demo_profile(company_id)
    pl, bs, cf = get_demo_financials(company_id)
    kpis = compute_all_kpis(profile, pl, bs, cf)
    return {"profile": profile, "kpis": kpis}

# ---------- Debug ----------
@app.get("/api/debug/assistants")
def debug_assistants():
    try:
        listing = client.beta.assistants.list(limit=10)
        visible = [{"id": a.id, "name": a.name} for a in listing.data]
        return {"project": os.getenv("OPENAI_PROJECT"), "assistants": visible}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
