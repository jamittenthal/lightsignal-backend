# app/agents.py
import os
from typing import Any, Dict
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT = os.getenv("OPENAI_PROJECT")  # optional
ASST_ORCH = os.getenv("ASST_ORCHESTRATOR_ID")       # e.g., asst_...
ASST_ANALYST = os.getenv("ASST_FINANCE_ANALYST_ID") # e.g., asst_...
ASST_SCOUT = os.getenv("ASST_RESEARCH_SCOUT_ID")    # e.g., asst_...

client_kwargs = {"api_key": OPENAI_API_KEY}
if OPENAI_PROJECT:
    client_kwargs["project"] = OPENAI_PROJECT
client = OpenAI(**client_kwargs)

def _run_assistant(assistant_id: str, user_text: str) -> str:
    # You can switch to Responses API if you prefer; this is simple and works.
    run = client.chat.completions.create(
        model="gpt-5.1-mini",
        messages=[
            {"role": "system", "content": "Return JSON only. No prose."},
            {"role": "user", "content": user_text},
        ],
        temperature=0.2,
    )
    return run.choices[0].message.content or "{}"

def call_orchestrator(user_text: str) -> str:
    if ASST_ORCH:
        return _run_assistant(ASST_ORCH, user_text)
    # Fallback if no Orchestrator set
    return _run_assistant(ASST_ANALYST or ASST_SCOUT, user_text)

def call_analyst(user_text: str) -> str:
    aid = ASST_ANALYST or ASST_ORCH
    return _run_assistant(aid, user_text)

def call_scout(user_text: str) -> str:
    aid = ASST_SCOUT or ASST_ORCH
    return _run_assistant(aid, user_text)
