# app/openai_client.py
import os
import json
import asyncio
from typing import Any, Dict, Optional
from openai import AsyncOpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ASST_ORCHESTRATOR_ID = os.getenv("ASST_ORCHESTRATOR_ID", "")
ASST_FINANCE_ANALYST_ID = os.getenv("ASST_FINANCE_ANALYST_ID", "")
ASST_RESEARCH_SCOUT_ID = os.getenv("ASST_RESEARCH_SCOUT_ID", "")

_client: Optional[AsyncOpenAI] = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set")
        _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client

async def _run_assistant(assistant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls a persisted Assistant (Threads/Runs) and returns parsed JSON from the latest message.
    All assistants should be configured to return STRICT JSON.
    """
    client = get_client()
    # 1) create a thread with the payload as user's message
    thread = await client.beta.threads.create(
        messages=[{"role": "user", "content": json.dumps(payload)}]
    )
    # 2) run the assistant
    run = await client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )
    # 3) poll until complete
    while run.status in ("queued", "in_progress", "cancelling"):
        await asyncio.sleep(0.7)
        run = await client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    if run.status != "completed":
        # fetch messages for debugging
        msgs = await client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
        last_txt = ""
        if msgs.data and msgs.data[0].content:
            parts = msgs.data[0].content
            if parts and parts[0].type == "text":
                last_txt = parts[0].text.value
        raise RuntimeError(f"Assistant run failed: {run.status} {run.last_error or ''} {last_txt}")

    # 4) read the last message (assistant output)
    messages = await client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
    if not messages.data:
        raise RuntimeError("No assistant messages returned")
    msg = messages.data[0]
    if not msg.content or msg.content[0].type != "text":
        raise RuntimeError("Assistant returned non-text content")
    text = msg.content[0].text.value

    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Assistant returned non-object JSON")
        return data
    except Exception as e:
        raise RuntimeError(f"Assistant returned invalid JSON: {e}\nRaw: {text[:500]}")

# ---------- Public helpers for each assistant ----------

async def call_orchestrator(intent: str, company_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    if not ASST_ORCHESTRATOR_ID:
        raise RuntimeError("ASST_ORCHESTRATOR_ID not set")
    payload = {
        "intent": intent,
        "company_id": company_id,
        "input": input_data,
        # Optional contract for your assistants:
        "expected_schema": {
            "kpis": "object",
            "insights": "array",
            "items": "array",
            "visuals": "array",
            "assumptions": "object"
        }
    }
    return await _run_assistant(ASST_ORCHESTRATOR_ID, payload)

async def call_finance_analyst(company_id: str, periods: int = 12) -> Dict[str, Any]:
    if not ASST_FINANCE_ANALYST_ID:
        raise RuntimeError("ASST_FINANCE_ANALYST_ID not set")
    payload = {
        "task": "financial_overview",
        "company_id": company_id,
        "periods": periods,
        "expected_schema": {
            "kpis": "object",
            "benchmarks": "array",
            "insights": "array",
            "visuals": "array"
        }
    }
    return await _run_assistant(ASST_FINANCE_ANALYST_ID, payload)

async def call_research_scout(query: str, company_id: str, region: Optional[str] = None) -> Dict[str, Any]:
    if not ASST_RESEARCH_SCOUT_ID:
        raise RuntimeError("ASST_RESEARCH_SCOUT_ID not set")
    payload = {
        "task": "research",
        "company_id": company_id,
        "query": query,
        "region": region,
        "expected_schema": {
            "bullets": "array",
            "so_what": "string",
            "sources": "array"
        }
    }
    return await _run_assistant(ASST_RESEARCH_SCOUT_ID, payload)
