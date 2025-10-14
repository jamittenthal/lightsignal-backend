# app/agents.py
import os
from typing import Any, Dict, Optional
from openai import OpenAI

# Accept both new and legacy env var names
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT = os.getenv("OPENAI_PROJECT")  # optional
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")  # <- configurable model (default gpt-4.1)

ASST_ORCH = os.getenv("ASST_ORCHESTRATOR_ID") or os.getenv("ORCHESTRATOR_ID")
ASST_ANALYST = os.getenv("ASST_FINANCE_ANALYST_ID") or os.getenv("FINANCE_ANALYST_ID")
ASST_SCOUT = os.getenv("ASST_RESEARCH_SCOUT_ID") or os.getenv("RESEARCH_SCOUT_ID")

def _build_client() -> Optional[OpenAI]:
    if not OPENAI_API_KEY:
        return None
    kwargs: Dict[str, Any] = {"api_key": OPENAI_API_KEY}
    if OPENAI_PROJECT:
        kwargs["project"] = OPENAI_PROJECT
    return OpenAI(**kwargs)

client: Optional[OpenAI] = _build_client()

def _run_assistant(assistant_id: Optional[str], user_text: str) -> str:
    if not client:
        return '{"error":"OPENAI_API_KEY not configured on server."}'
    if not assistant_id:
        return '{"error":"Assistant ID missing (ASST_ORCHESTRATOR_ID / FINANCE_ANALYST_ID / RESEARCH_SCOUT_ID)."}'
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Return JSON only. No prose."},
                {"role": "user", "content": user_text},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or "{}"
    except Exception as e:
        return f'{{"error":"{type(e).__name__}: {str(e).replace(chr(34), chr(39))}"}}'

def call_orchestrator(user_text: str) -> str:
    aid = ASST_ORCH or ASST_ANALYST or ASST_SCOUT
    return _run_assistant(aid, user_text)

def call_analyst(user_text: str) -> str:
    aid = ASST_ANALYST or ASST_ORCH
    return _run_assistant(aid, user_text)

def call_scout(user_text: str) -> str:
    aid = ASST_SCOUT or ASST_ORCH
    return _run_assistant(aid, user_text)
