import os
import time
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    project=os.getenv("OPENAI_PROJECT")
)

@app.get("/health")
def health():
    return {"ok": True, "project": os.getenv("OPENAI_PROJECT")}

def run_assistant(assistant_id: str, prompt: str) -> str:
    """Create thread, run assistant, wait for completion, return raw text value."""
    thread = client.beta.threads.create(messages=[{"role": "user", "content": prompt}])
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
    while True:
        status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if status.status == "completed":
            break
        if status.status in ["failed", "cancelled"]:
            raise Exception(f"Run failed: {status.status}")
        time.sleep(1)
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value  # raw JSON string

def parse_json_or_bust(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to strip code fences or stray text if any
        cleaned = raw.strip().strip("`")
        try:
            return json.loads(cleaned)
        except Exception:
            # Last resort: wrap raw string so caller can inspect
            raise

@app.post("/api/orchestrator")
async def orchestrator(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "render_financial_overview for company_id=demo")
    try:
        asst_id = os.getenv("ORCHESTRATOR_ID")
        raw = run_assistant(asst_id, prompt)
        parsed = parse_json_or_bust(raw)
        return JSONResponse(content=parsed)  # <-- return proper JSON object
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/finance")
async def finance(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "analyze company financials")
    try:
        asst_id = os.getenv("FINANCE_ANALYST_ID")
        raw = run_assistant(asst_id, prompt)
        parsed = parse_json_or_bust(raw)
        return JSONResponse(content=parsed)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/research")
async def research(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "latest SMB signals")
    try:
        asst_id = os.getenv("RESEARCH_SCOUT_ID")
        raw = run_assistant(asst_id, prompt)
        parsed = parse_json_or_bust(raw)
        return JSONResponse(content=parsed)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Debug: list assistants visible to this key/project
@app.get("/api/debug/assistants")
def debug_assistants():
    try:
        listing = client.beta.assistants.list(limit=10)
        visible = [{"id": a.id, "name": a.name} for a in listing.data]
        return {"project": os.getenv("OPENAI_PROJECT"), "assistants": visible}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
