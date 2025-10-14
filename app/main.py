import os
import json
import time
from typing import Optional, List, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# -------- Env & OpenAI client --------
load_dotenv()

from openai import OpenAI
client = OpenAI(project=os.getenv("OPENAI_PROJECT"))  # uses OPENAI_API_KEY from env

ORCHESTRATOR_ID = os.getenv("ORCHESTRATOR_ID", "").strip()
RESEARCH_ID     = os.getenv("RESEARCH_ID", "").strip()
FINANCE_ID      = os.getenv("FINANCE_ID", "").strip()

# -------- FastAPI app --------
app = FastAPI(title="LightSignal Backend", version="1.0.1")

# Allow your Vercel domain & localhost
allowed_origins = [
    os.getenv("FRONTEND_ORIGIN", "").strip() or "https://lightsignal-frontend.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Models --------
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class PromptRequest(BaseModel):
    prompt: str

# -------- Helpers: OpenAI Threads API --------
def _wait_for_run(thread_id: str, run_id: str, timeout_s: int = 90):
    t0 = time.time()
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status in ("completed", "failed", "cancelled", "expired"):
            return run
        if time.time() - t0 > timeout_s:
            raise TimeoutError("Run timed out")
        time.sleep(0.7)

def _latest_text(thread_id: str) -> str:
    msgs = client.beta.threads.messages.list(thread_id=thread_id, order="desc", limit=1)
    if msgs.data and msgs.data[0].content:
        first = msgs.data[0].content[0]
        if getattr(first, "type", None) == "text":
            return first.text.value
    return ""

def _try_extract_json(text: str) -> Optional[str]:
    """
    Be forgiving: strip code fences, then pick the longest {...} block.
    """
    if not text:
        return None
    # strip ```json … ```
    if "```" in text:
        text = text.replace("```json", "```").replace("```JSON", "```")
        parts = text.split("```")
        # prefer inside the first fenced block
        for p in parts:
            if "{" in p and "}" in p:
                s = p[p.find("{") : p.rfind("}") + 1]
                if s:
                    return s
    # fallback: find outermost braces
    if "{" in text and "}" in text:
        s = text[text.find("{") : text.rfind("}") + 1]
        return s
    return None

def _parse_json_or_none(text: str):
    try:
        return json.loads(text)
    except Exception:
        pass
    blob = _try_extract_json(text or "")
    if blob:
        try:
            return json.loads(blob)
        except Exception:
            return None
    return None

# -------- Research triggers --------
LOCATION_KEYWORDS = [
    "move to", "expand to", "open in", "relocate", "relocation", "new office",
    "austin", "dallas", "houston", "san antonio", "phoenix", "miami", "tampa",
    "orlando", "chicago", "nyc", "new york", "denver", "seattle", "los angeles",
    "la", "san diego", "boston", "atlanta", "nashville", "charlotte", "vegas",
]
MARKET_KEYWORDS = [
    "market", "demand", "competition", "competitors", "labor", "wages", "regulation",
    "permit", "license", "seasonality", "supplier", "materials", "input costs",
    "benchmark", "peers", "median",
]

def _needs_research(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in LOCATION_KEYWORDS) or any(k in low for k in MARKET_KEYWORDS)

# -------- Finance triggers --------
FINANCE_KEYWORDS = [
    "buy", "purchase", "lease", "truck", "van", "vehicle", "fleet", "equipment",
    "hire", "hiring", "headcount", "raise price", "price increase", "pricing",
    "marketing", "refi", "refinance", "loan", "debt", "line of credit", "loc",
    "expand", "expansion", "cash flow", "runway",
]

def _needs_finance(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in FINANCE_KEYWORDS)

def _guess_scope(text: str) -> Dict[str, Any]:
    low = text.lower()
    city = None
    for token in [
        "austin","dallas","houston","san antonio","phoenix","miami","tampa","orlando",
        "chicago","nyc","new york","denver","seattle","los angeles","la","san diego",
        "boston","atlanta","nashville","charlotte","vegas"
    ]:
        if token in low:
            city = "Los Angeles" if token == "la" else ("New York" if token in ["nyc","new york"] else token.title())
            break
    return {
        "company_id": "demo",
        "industry": "HVAC",
        "location": {"city": city} if city else None,
        "timeframe": "last 12 months",
    }

# -------- Assistant runners --------
def _run_assistant(assistant_id: str, user_content: str) -> str:
    thread = client.beta.threads.create(messages=[{"role": "user", "content": user_content}])
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
    _wait_for_run(thread.id, run.id)
    return _latest_text(thread.id)

def _run_research_assistant(query: str) -> Optional[dict]:
    if not RESEARCH_ID:
        return None
    scope = _guess_scope(query)
    text = _run_assistant(
        RESEARCH_ID,
        f"Research request for scenario: {query}\n\n"
        f"Please follow your JSON output contract. Scope hint: {json.dumps(scope)}"
    )
    return _parse_json_or_none(text)

def _run_finance_assistant(prompt: str) -> Optional[dict]:
    if not FINANCE_ID:
        return None
    text = _run_assistant(
        FINANCE_ID,
        "Financial scenario analysis request:\n"
        f"{prompt}\n\n"
        "Return JSON with KPIs, ratios, cashflow impact, and verdict per your output contract."
    )
    return _parse_json_or_none(text)

# -------- Routes --------
@app.get("/health")
def health():
    ok = bool(ORCHESTRATOR_ID)
    return {"ok": ok, "orchestrator_set": ok}

@app.get("/ai/openapi.yaml")
def openapi_yaml():
    here = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(here, "ai", "openapi.yaml")
    if os.path.exists(yaml_path):
        return FileResponse(yaml_path, media_type="text/yaml")
    return PlainTextResponse("openapi.yaml not found", status_code=404)

@app.post("/api/orchestrator")
def orchestrator(req: PromptRequest):
    """One-shot prompt to the orchestrator (no prior chat)."""
    try:
        if not ORCHESTRATOR_ID:
            return JSONResponse({"error": "ORCHESTRATOR_ID not set"}, status_code=500)

        user_content = f"scenario_chat: {req.prompt} (company_id=demo)"
        msgs: List[Dict[str, str]] = [{"role": "user", "content": user_content}]

        if _needs_research(req.prompt):
            digest = _run_research_assistant(req.prompt)
            if digest:
                msgs.insert(0, {"role": "assistant", "content": "RESEARCH_DIGEST_JSON:\n" + json.dumps(digest)})
        if _needs_finance(req.prompt):
            fin = _run_finance_assistant(req.prompt)
            if fin:
                msgs.insert(0, {"role": "assistant", "content": "FINANCIAL_DIGEST_JSON:\n" + json.dumps(fin)})

        thread = client.beta.threads.create(messages=msgs)
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ORCHESTRATOR_ID)
        _wait_for_run(thread.id, run.id)
        text = _latest_text(thread.id)
        parsed = _parse_json_or_none(text)

        return JSONResponse({"assistant_id": ORCHESTRATOR_ID, "result": text if not parsed else parsed})
    except Exception as e:
        return JSONResponse({"error": f"{e}"}, status_code=500)

@app.post("/api/orchestrator_chat")
def orchestrator_chat(req: ChatRequest):
    """
    Multi-turn chat with the Orchestrator.
    - Ensures last user msg is tagged as scenario_chat and has a default company_id.
    - Auto-injects Research Scout and Finance Analyst digests when relevant.
    """
    try:
        if not ORCHESTRATOR_ID:
            return JSONResponse({"error": "ORCHESTRATOR_ID not set"}, status_code=500)

        msgs: List[Dict[str, str]] = [m.dict() for m in req.messages]

        if msgs and msgs[-1]["role"] == "user":
            user_text = msgs[-1]["content"]
            if "scenario_chat:" not in user_text:
                msgs[-1]["content"] = f"scenario_chat: {user_text} (company_id=demo)"

            if _needs_research(user_text):
                digest = _run_research_assistant(user_text)
                if digest:
                    msgs.insert(
                        max(0, len(msgs) - 1),
                        {"role": "assistant", "content": "RESEARCH_DIGEST_JSON:\n" + json.dumps(digest)},
                    )

            if _needs_finance(user_text):
                fin = _run_finance_assistant(user_text)
                if fin:
                    msgs.insert(
                        max(0, len(msgs) - 1),
                        {"role": "assistant", "content": "FINANCIAL_DIGEST_JSON:\n" + json.dumps(fin)},
                    )

        thread = client.beta.threads.create(messages=msgs)
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ORCHESTRATOR_ID)
        _wait_for_run(thread.id, run.id)
        text = _latest_text(thread.id)
        parsed = _parse_json_or_none(text)

        return JSONResponse(
            {
                "message": {"role": "assistant", "content": text},
                "parsed": parsed
            }
        )
    except Exception as e:
        return JSONResponse({"error": f"{e}"}, status_code=500)
