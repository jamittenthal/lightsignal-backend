# app/openai_client.py
import os
import json
import re
import asyncio
from typing import Any, Dict, Optional, List
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

# ---------- JSON extraction utilities ----------

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)

def _strip_code_fences(s: str) -> str:
    return _CODE_FENCE_RE.sub("", s)

def _normalize_quotes(s: str) -> str:
    # replace smart quotes with ascii quotes
    return s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")

def _extract_first_json_object(s: str) -> str:
    """
    Find the first well-balanced {...} JSON object in the string and return it.
    Raises ValueError if not found.
    """
    s = _strip_code_fences(_normalize_quotes(s))
    start = s.find("{")
    if start == -1:
        raise ValueError("No '{' found in assistant output")
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start:i+1]
    raise ValueError("Braces never balanced in assistant output")

def _join_text_parts(message_content: List[Any]) -> str:
    """
    Join all text segments from an assistant message into a single string.
    """
    chunks: List[str] = []
    for part in message_content or []:
        if getattr(part, "type", None) == "text":
            val = getattr(part, "text", None)
            if val and getattr(val, "value", None):
                chunks.append(val.value)
        elif isinstance(part, dict) and part.get("type") == "text":
            # defensive for dict-like parts
            t = part.get("text", {})
            v = t.get("value") if isinstance(t, dict) else None
            if isinstance(v, str):
                chunks.append(v)
    return "\n".join(chunks).strip()

# ---------- Core assistant runner (Threads/Runs) ----------

async def _run_assistant(assistant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls a persisted Assistant (Threads/Runs) and returns parsed JSON from the latest message.
    We allow extra prose/code fences and aggressively extract the first JSON object.
    """
    client = get_client()

    thread = await client.beta.threads.create(
        messages=[{"role": "user", "content": json.dumps(payload)}]
    )

    run = await client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
        # If your Assistant supports response_format, you can add:
        # response_format={"type": "json_object"},
    )

    # poll until complete
    while run.status in ("queued", "in_progress", "cancelling"):
        await asyncio.sleep(0.7)
        run = await client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    if run.status != "completed":
        msgs = await client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
        last_txt = ""
        if msgs.data and msgs.data[0].content:
            last_txt = _join_text_parts(msgs.data[0].content)
        raise RuntimeError(f"Assistant run failed: {run.status} {run.last_error or ''} {last_txt[:500]}")

    # read latest message (assistant output)
    messages = await client.beta.threads.messages.list(thread_id=thread.id, order="desc", limit=1)
    if not messages.data:
        raise RuntimeError("No assistant messages returned")

    msg = messages.data[0]
    text_all = _join_text_parts(msg.content)
    if not text_all:
        raise RuntimeError("Assistant returned empty text")

    # Try strict JSON first, else extract first {...}
    try:
        data = json.loads(text_all)
        if not isinstance(data, dict):
            raise ValueError("Assistant returned non-object JSON")
        return data
    except Exception:
        try:
            json_str = _extract_first_json_object(text_all)
            data = json.loads(json_str)
            if not isinstance(data, dict):
                raise ValueError("Assistant returned non-object JSON after extraction")
            return data
        except Exception as e:
            raise RuntimeError(f"Assistant returned invalid JSON: {e}\nRaw: {text_all[:1000]}")

# ---------- Public helpers for each assistant ----------

async def call_orchestrator(intent: str, company_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    if not ASST_ORCHESTRATOR_ID:
        raise RuntimeError("ASST_ORCHESTRATOR_ID not set")
    payload = {
        "intent": intent,
        "company_id": company_id,
        "input": input_data,
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
