# app/agents.py
import os
from typing import Any, Dict, Optional
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT = os.getenv("OPENAI_PROJECT")  # optional
ASST_ORCH = os.getenv("ASST_ORCHESTRATOR_ID")       # e.g., asst_...
ASST_ANALYST = os.getenv("ASST_FINANCE_ANALYST_ID") # e.g., asst_...
ASST_SCOUT = os.getenv("ASST_RESEARCH_SCOUT_ID")    # e.g., asst_...

client_kwargs: Dict[str, Any] = {}
if OPENAI_API_KEY:
    client_kwargs["api_key"] = OPENAI_API_KEY
if OPENAI_PROJECT:
    client_kwargs["project"] = OPENAI_PROJECT
client: Optional[OpenAI] = OpenAI(**client_kwargs) if client_kwargs else None

def _run_assistant(assistant_id: str, user_text: str) -> str:
    if not client:
        return '{"error":"OpenAI client not configured"}'
    # You can switch to Responses API; chat.completions is simple and fine here.
    resp = client.chat.completions.create(
        model="gpt-5.1-mini",
        messages=[
            {"role": "system", "content": "Return JSON only. No prose."},
            {"role": "user", "content": user_text},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content or "{}"

def call_orchestrator(user_text: str) -> str:
    aid = ASST_ORCH or ASST_ANALYST or ASST_SCOUT
    return _run_assistant(aid, user_text)

def call_analyst(user_text: str) -> str:
    aid = ASST_ANALYST or ASST_ORCH
    return _run_assistant(aid, user_text)

def call_scout(user_text: str) -> str:
    aid = ASST_SCOUT or ASST_ORCH
    return _run_assistant(aid, user_text)
