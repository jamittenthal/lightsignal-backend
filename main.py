# /main.py
import os, json, re
from pathlib import Path
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from backend.assistants import run_assistant

BASE_DIR = Path(__file__).resolve().parent
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
ASSISTANT_ID_ORCH = os.environ.get("ASSISTANT_ORCHESTRATOR_ID") or os.environ.get("ASSISTANT_ID_ORCH")
ASSISTANT_ID_FINANCE = os.environ.get("ASSISTANT_FINANCE_ID")
ASSISTANT_ID_RESEARCH = os.environ.get("ASSISTANT_RESEARCH_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AI_TABS_DIR = BASE_DIR / "ai" / "tabs"
def get_tab_spec(intent: str) -> dict:
    p = AI_TABS_DIR / f"{intent}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())

def list_intents() -> list:
    return [f.stem for f in AI_TABS_DIR.glob("*.json")]

PROFILE_DIR = BASE_DIR / "backend" / "profiles"
def get_profile(company_id: str) -> dict:
    p = PROFILE_DIR / f"{company_id}.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())

FINANCIALS_DIR = BASE_DIR / "backend" / "financials"
def get_financials(company_id: str) -> dict:
    p = FINANCIALS_DIR / f"{company_id}.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())

def call_orchestrator(tab_spec: dict, context: dict) -> dict:
    thread = client.beta.threads.create(
        messages=[{"role":"user","content":json.dumps({"tab_spec": tab_spec, "context": context})}]
    )
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID_ORCH)
    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    msgs = client.beta.threads.messages.list(thread_id=thread.id)
    content = msgs.data[0].content[0].text.value
    return json.loads(content)


def get_scenario_baseline(company_id: str) -> dict:
    """
    Load baseline assumptions from profile + KPIs.
    Falls back to safe defaults for demo.
    """
    profile = get_profile(company_id)
    financials = get_financials(company_id)
    
    # Build baseline from available data
    return {
        "company_id": company_id,
        "profile": {
            "industry": profile.get("industry", {}).get("naics_title", "Coffee Shops"),
            "employees": profile.get("operations", {}).get("total_employees", 20),
            "avg_job_value": financials.get("financial_overview", {}).get("revenue_mtd", 142000) / 30,
            "price_level": 0.95,
            "cash_on_hand": financials.get("financial_overview", {}).get("cash_available", 185000),
            "ar_days": 18,
            "ap_days": 22,
            "inventory_turns": 24
        },
        "kpis": {
            "revenue_mtd": financials.get("financial_overview", {}).get("revenue_mtd", 142000),
            "net_margin_pct": 0.22,
            "cash_flow_mtd": 28500,
            "runway_months": 5.9
        }
    }

def create_simple_projection(baseline: dict, deltas: list, horizon_days: int) -> dict:
    """Create a simple scenario projection based on deltas."""
    revenue_mtd = baseline.get("kpis", {}).get("revenue_mtd", 120000)
    margin_pct = baseline.get("kpis", {}).get("net_margin_pct", 0.2)
    
    # Apply deltas
    revenue_impact = 1.0
    margin_impact = 0.0
    
    for delta in deltas:
        lever = delta.get("lever", "").lower()
        delta_pct = delta.get("delta_pct", 0) / 100.0 if delta.get("delta_pct") else 0
        delta_abs = delta.get("delta_abs", 0)
        
        if lever in ["price", "pricing"]:
            revenue_impact *= (1 + delta_pct)
            margin_impact += delta_pct * 0.8
        elif lever in ["headcount", "employees", "hiring"]:
            cost_increase = delta_abs * 4000
            revenue_boost = delta_abs * 8000
            revenue_impact *= (1 + revenue_boost / revenue_mtd)
            margin_impact -= (cost_increase / revenue_mtd)
        elif lever == "marketing":
            revenue_impact *= (1 + delta_pct * 1.5)
            margin_impact -= delta_pct * 0.3
    
    # Calculate projections
    months = horizon_days / 30
    new_revenue = revenue_mtd * revenue_impact
    new_margin = max(0, margin_pct + margin_impact)
    
    delta_desc = ", ".join([f"{d.get('lever')} {d.get('delta_pct', d.get('delta_abs', 0))}" for d in deltas])
    
    return {
        "summary": f"Projection with {delta_desc}: Revenue {((revenue_impact - 1) * 100):.1f}% change, Margin {(margin_impact * 100):.1f}pp change over {int(months)} months.",
        "charts": [{
            "label": "Projected Revenue",
            "series": [
                {"t": "Today", "v": revenue_mtd},
                {"t": f"Month 1", "v": revenue_mtd * (1 + (revenue_impact - 1) * 0.33)},
                {"t": f"Month 2", "v": revenue_mtd * (1 + (revenue_impact - 1) * 0.66)},
                {"t": "Month 3", "v": new_revenue},
            ]
        }],
        "table": [
            {"metric": "Revenue Change", "value": f"{((revenue_impact - 1) * 100):.1f}%"},
            {"metric": "Margin Change", "value": f"{(margin_impact * 100):.1f} pp"},
            {"metric": "Net Impact", "value": f"+${int(new_revenue * new_margin - revenue_mtd * margin_pct)}"}
        ]
    }

def orchestrate_scenario_chat(question: str, baseline: dict) -> dict:
    """
    Orchestrate scenario chat using Finance, Research, and Orchestrator assistants.
    """
    try:
        # Compact baseline JSON for prompts
        baseline_json = json.dumps(baseline, indent=None)
        
        # Initialize response parts
        finance_summary = None
        research_notes = None
        
        # Route to appropriate assistants based on question keywords
        question_lower = question.lower()
        
        # Finance keywords
        finance_keywords = ["price", "pric", "hire", "hiring", "headcount", "employee", "margin", "runway", 
                          "cash", "forecast", "revenue", "expense", "cost", "salary", "budget"]
        needs_finance = any(kw in question_lower for kw in finance_keywords)
        
        # Research keywords
        research_keywords = ["market", "competitor", "competition", "demand", "industry", "trend", 
                           "customer", "consumer", "sector"]
        needs_research = any(kw in question_lower for kw in research_keywords)
        
        # Call Finance Assistant if needed
        if needs_finance and ASSISTANT_ID_FINANCE:
            finance_prompt = f"""Role: Finance Specialist for SMBs. Use the baseline (JSON) below.\nTask: In <=5 lines, quantify impact and propose 0–3 deltas array (JSON) for levers like price, headcount, marketing, AR/AP terms. Be specific with numbers.\nQuestion: {question}\nBaseline: {baseline_json}\nOutput: A short paragraph first, then a JSON line with "deltas": [...]"""
            finance_summary = run_assistant(ASSISTANT_ID_FINANCE, finance_prompt)
        
        # Call Research Assistant if needed
        if needs_research and ASSISTANT_ID_RESEARCH:
            industry = baseline.get("profile", {}).get("industry", "Unknown")
            research_prompt = f"""Role: Research Scout. In 2–3 one-liners, provide current market signals relevant to the question. Avoid fluff. If not needed, say "No external signals needed."\nQuestion: {question}\nBaseline industry: {industry}"""
            research_notes = run_assistant(ASSISTANT_ID_RESEARCH, research_prompt)
        
        # Build Orchestrator context
        materials = []
        if finance_summary:
            materials.append(f"Finance Analysis:\n{finance_summary}")
        if research_notes:
            materials.append(f"Market Research:\n{research_notes}")
        
        materials_text = "\n\n".join(materials) if materials else "No specialist input."
        
        orchestrator_prompt = f"""Orchestrate a concise answer using the materials below. Auto-assume baseline. Do NOT ask for confirmations unless a critical input is unknown.\n\nUser Question: {question}\n\nBusiness Baseline:\n{baseline_json}\n\nSpecialist Materials:\n{materials_text}\n\nStrict instruction: Return JSON ONLY with keys:\n- message (string, under 120 words, actionable answer)\n- propose_deltas (array of objects with lever, delta_pct or delta_abs. Use [] if no changes recommended)\n- horizon_days (number, typically 30, 60, or 90)\n\nExample: {{"message": "...", "propose_deltas": [{{"lever":"price","delta_pct":5}}], "horizon_days": 90}}"""
        
        # Call Orchestrator
        if not ASSISTANT_ID_ORCH:
            return {
                "message": f"Based on your baseline: {finance_summary or research_notes or 'Unable to analyze without assistant configuration.'}",
                "assumptions_used": baseline
            }
        
        orchestrator_response = run_assistant(ASSISTANT_ID_ORCH, orchestrator_prompt)
        
        # Parse JSON from orchestrator (handle code fences)
        orchestrator_text = orchestrator_response.strip()
        
        # Strip markdown code fences if present
        if orchestrator_text.startswith("```"):
            lines = orchestrator_text.split("\n")
            orchestrator_text = "\n".join(lines[1:-1]) if len(lines) > 2 else orchestrator_text
        
        # Try to parse JSON
        try:
            orchestrator_data = json.loads(orchestrator_text)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            json_match = re.search(r'\{.*\}', orchestrator_text, re.DOTALL)
            if json_match:
                orchestrator_data = json.loads(json_match.group())
            else:
                return {
                    "message": orchestrator_text[:500],
                    "assumptions_used": baseline
                }
        
        message = orchestrator_data.get("message", "No response")
        propose_deltas = orchestrator_data.get("propose_deltas", [])
        horizon_days = orchestrator_data.get("horizon_days", 90)
        
        # If deltas proposed, run simulation
        simulation = None
        if propose_deltas and len(propose_deltas) > 0:
            simulation = create_simple_projection(baseline, propose_deltas, horizon_days)
        
        return {
            "message": message,
            "simulation": simulation,
            "assumptions_used": baseline
        }
    
    except Exception as e:
        print(f"Orchestration error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "message": f"I encountered an issue analyzing your question. Based on your baseline: revenue ${baseline.get('kpis', {}).get('revenue_mtd', 0)}, {baseline.get('profile', {}).get('employees', 0)} employees. Please try rephrasing.",
            "assumptions_used": baseline
        }


router = APIRouter()

@router.post("/api/intent")
def api_intent(payload: dict):
    intent      = payload.get("intent")
    company_id  = payload.get("company_id", "demo")
    user_input  = payload.get("input", {})

    # Handle scenario_chat specially
    if intent == "scenario_chat":
        baseline = get_scenario_baseline(company_id)
        question = user_input.get("question", "")
        
        if not question:
            return {
                "message": "Please ask a scenario question.",
                "assumptions_used": baseline
            }
        
        return orchestrate_scenario_chat(question, baseline)
    
    # Handle other intents via ai_registry
    tab_spec = get_tab_spec(intent)
    if not tab_spec:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Unknown intent: {intent}", "available_intents": list_intents()}
        )

    profile    = get_profile(company_id)
    financials = get_financials(company_id)

    context = {
        "company_id": company_id,
        "intent": intent,
        "input": user_input,
        "profile": profile,
        "financials": financials,
        "spec_dir": str(AI_TABS_DIR)
    }
    return call_orchestrator(tab_spec, context)

app.include_router(router)