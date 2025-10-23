# app/routers/ai_agents.py
"""
GPT agent endpoints for orchestration, finance analysis, and research.
Keys are kept server-side. Demo mode returns seeds without calling OpenAI.
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ..utils_demo import is_demo, meta
from ..demo_seed import (
    DEMO_ORCHESTRATOR_RESPONSE,
    DEMO_FINANCE_AGENT_RESPONSE,
    DEMO_RESEARCH_AGENT_RESPONSE,
)

router = APIRouter()

# Environment variables for OpenAI and Assistant IDs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ORCHESTRATOR_ASSISTANT_ID = os.getenv("ORCHESTRATOR_ASSISTANT_ID", "")
FINANCE_ASSISTANT_ID = os.getenv("FINANCE_ASSISTANT_ID", "")
RESEARCH_ASSISTANT_ID = os.getenv("RESEARCH_ASSISTANT_ID", "")
DEV_NONDEMO_STUB = os.getenv("DEV_NONDEMO_STUB", "false").lower() == "true"


# -----------------------------------------------------------------------------
# Request Models
# -----------------------------------------------------------------------------
class OrchestratorRequest(BaseModel):
    company_id: Optional[str] = "demo"
    query: str
    context: Optional[Dict[str, Any]] = None


class FinanceRequest(BaseModel):
    company_id: Optional[str] = "demo"
    periods: Optional[int] = 12
    focus: Optional[str] = None  # e.g., "cashflow", "profitability"


class ResearchRequest(BaseModel):
    company_id: Optional[str] = "demo"
    query: str
    region: Optional[str] = None


# -----------------------------------------------------------------------------
# Helper: Call OpenAI Assistant (placeholder for real implementation)
# -----------------------------------------------------------------------------
def call_openai_assistant(assistant_id: str, messages: list) -> dict:
    """
    Calls OpenAI Assistants API with given messages.
    In production, this would use the OpenAI SDK to create a thread,
    send messages, wait for run completion, and extract the response.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    if not assistant_id:
        raise HTTPException(status_code=501, detail="Assistant ID not configured")
    
    # TODO: Implement actual OpenAI Assistants API call
    # from openai import OpenAI
    # client = OpenAI(api_key=OPENAI_API_KEY)
    # thread = client.beta.threads.create(messages=messages)
    # run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
    # ... wait for completion ...
    # response_messages = client.beta.threads.messages.list(thread_id=thread.id)
    # return parse response
    
    raise HTTPException(
        status_code=501,
        detail="OpenAI Assistants integration not yet implemented. Use demo mode or set DEV_NONDEMO_STUB=true for testing."
    )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@router.post("/api/ai/orchestrate")
async def orchestrate(req: OrchestratorRequest):
    """
    General-purpose orchestrator agent for multi-domain queries.
    Demo mode: returns seed data.
    Non-demo: calls OpenAI Orchestrator Assistant.
    """
    if is_demo(req.company_id):
        # Return demo seed
        response = DEMO_ORCHESTRATOR_RESPONSE.copy()
        response["query"] = req.query
        response["company_id"] = req.company_id
        return meta(response)
    
    # Non-demo mode
    if DEV_NONDEMO_STUB:
        # Development stub
        return {
            "query": req.query,
            "company_id": req.company_id,
            "answer": "Non-demo stub response (DEV_NONDEMO_STUB=true)",
            "insights": [],
            "actions": [],
            "_meta": {"demo": False, "stub": True},
        }
    
    # Real OpenAI call
    try:
        messages = [
            {
                "role": "user",
                "content": f"Query: {req.query}\nContext: {req.context or {}}",
            }
        ]
        response = call_openai_assistant(ORCHESTRATOR_ASSISTANT_ID, messages)
        response["_meta"] = {"demo": False}
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestrator error: {str(e)}")


@router.post("/api/ai/finance")
async def finance_analyst(req: FinanceRequest):
    """
    Finance-specific analysis agent.
    Demo mode: returns seed data.
    Non-demo: calls OpenAI Finance Analyst Assistant.
    """
    if is_demo(req.company_id):
        # Return demo seed
        response = DEMO_FINANCE_AGENT_RESPONSE.copy()
        response["company_id"] = req.company_id
        response["periods"] = req.periods
        return meta(response)
    
    # Non-demo mode
    if DEV_NONDEMO_STUB:
        # Development stub
        return {
            "company_id": req.company_id,
            "summary": "Non-demo stub response (DEV_NONDEMO_STUB=true)",
            "key_metrics": [],
            "recommendations": [],
            "_meta": {"demo": False, "stub": True},
        }
    
    # Real OpenAI call
    try:
        messages = [
            {
                "role": "user",
                "content": f"Analyze financials for company_id={req.company_id}, periods={req.periods}, focus={req.focus}",
            }
        ]
        response = call_openai_assistant(FINANCE_ASSISTANT_ID, messages)
        response["_meta"] = {"demo": False}
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Finance analyst error: {str(e)}")


@router.post("/api/ai/research")
async def research_scout(req: ResearchRequest):
    """
    Research and opportunity discovery agent.
    Demo mode: returns seed data.
    Non-demo: calls OpenAI Research Scout Assistant.
    """
    if is_demo(req.company_id):
        # Return demo seed
        response = DEMO_RESEARCH_AGENT_RESPONSE.copy()
        response["company_id"] = req.company_id
        response["query"] = req.query
        return meta(response)
    
    # Non-demo mode
    if DEV_NONDEMO_STUB:
        # Development stub
        return {
            "company_id": req.company_id,
            "query": req.query,
            "summary": "Non-demo stub response (DEV_NONDEMO_STUB=true)",
            "opportunities": [],
            "market_insights": [],
            "_meta": {"demo": False, "stub": True},
        }
    
    # Real OpenAI call
    try:
        messages = [
            {
                "role": "user",
                "content": f"Research query: {req.query}\nRegion: {req.region or 'Not specified'}",
            }
        ]
        response = call_openai_assistant(RESEARCH_ASSISTANT_ID, messages)
        response["_meta"] = {"demo": False}
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research scout error: {str(e)}")
