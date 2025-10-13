import os
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/health")
def health():
    return {"ok": True}

# === ASSISTANT CALLER UTILITY ===
def run_assistant(assistant_id: str, prompt: str):
    """Create a thread, run the assistant, and return the text output."""
    thread = client.beta.threads.create(messages=[{"role": "user", "content": prompt}])
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)

    # Wait for the run to complete
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run_status.status == "completed":
            break
        elif run_status.status in ["failed", "cancelled"]:
            raise Exception(f"Run failed: {run_status.status}")
        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    # Return only the text value
    return messages.data[0].content[0].text.value

# === ROUTES ===

@app.post("/api/orchestrator")
async def orchestrator(request: Request):
    """Call the Orchestrator Assistant"""
    data = await request.json()
    prompt = data.get("prompt", "render_financial_overview for company_id=demo")
    try:
        response = run_assistant(os.getenv("ORCHESTRATOR_ID"), prompt)
        return JSONResponse(content={"result": response})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/finance")
async def finance(request: Request):
    """Call the Finance Analyst Assistant"""
    data = await request.json()
    prompt = data.get("prompt", "analyze company financials")
    try:
        response = run_assistant(os.getenv("FINANCE_ANALYST_ID"), prompt)
        return JSONResponse(content={"result": response})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/research")
async def research(request: Request):
    """Call the Research Scout Assistant"""
    data = await request.json()
    prompt = data.get("prompt", "latest industry signals for small businesses")
    try:
        response = run_assistant(os.getenv("RESEARCH_SCOUT_ID"), prompt)
        return JSONResponse(content={"result": response})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
