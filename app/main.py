import os
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize OpenAI client using your project + key
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    project=os.getenv("OPENAI_PROJECT")  # ensures it uses the correct project
)

@app.get("/health")
def health():
    """Simple health check."""
    return {"ok": True, "project": os.getenv("OPENAI_PROJECT")}

def run_assistant(assistant_id: str, prompt: str):
    """Create thread, run assistant, wait for completion, return text output."""
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
    return messages.data[0].content[0].text.value

@app.post("/api/orchestrator")
async def orchestrator(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "render_financial_overview for company_id=demo")
    try:
        asst_id = os.getenv("ORCHESTRATOR_ID")
        output = run_assistant(asst_id, prompt)
        return JSONResponse(content={"assistant_id": asst_id, "result": output})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/finance")
async def finance(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "analyze company financials")
    try:
        asst_id = os.getenv("FINANCE_ANALYST_ID")
        output = run_assistant(asst_id, prompt)
        return JSONResponse(content={"assistant_id": asst_id, "result": output})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/research")
async def research(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "latest SMB signals")
    try:
        asst_id = os.getenv("RESEARCH_SCOUT_ID")
        output = run_assistant(asst_id, prompt)
        return JSONResponse(content={"assistant_id": asst_id, "result": output})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/debug/assistants")
def debug_assistants():
    """List assistants visible to this project/key for debugging."""
    try:
        listing = client.beta.assistants.list(limit=10)
        visible = [{"id": a.id, "name": a.name} for a in listing.data]
        return {"project": os.getenv("OPENAI_PROJECT"), "assistants": visible}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
