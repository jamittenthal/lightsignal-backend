# app/routes_scenario_lab.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from .schemas import (
    ScenarioLabRequest, ScenarioLabResponse, ScenarioLabKPIs,
    MonteCarloResult, StressTestResult, PeerBenchmark
)
from .services.qbo_adapter import get_financials
from .services.scenario_planning import compute_scenario_lab_analysis

router = APIRouter()


@router.post("/api/scenario-lab/analyze", response_model=ScenarioLabResponse)
async def analyze_scenario(request: ScenarioLabRequest):
    """
    Main endpoint for Scenario Planning Lab analysis.
    
    This endpoint:
    - Retrieves baseline financials from QuickBooks or demo data
    - Applies scenario inputs (price changes, headcount, loans, capex)
    - Computes base vs scenario comparison
    - Optionally runs Monte Carlo simulations
    - Optionally runs stress tests
    - Provides peer benchmarks
    - Generates AI-style recommendations and risk warnings
    - Returns provenance metadata for transparency
    
    Example request:
    ```json
    {
      "company_id": "demo-hvac-co",
      "scenario_name": "Purchase New Truck",
      "description": "Evaluate financing a $45k service truck",
      "inputs": {
        "price_change_pct": 0,
        "headcount_delta": 0,
        "loan_amount": 36000,
        "interest_rate": 7.5,
        "capex_amount": 45000
      },
      "horizon_months": 12,
      "run_monte_carlo": true,
      "run_stress_test": true
    }
    ```
    """
    try:
        # Get baseline financials
        financials = await get_financials(request.company_id, 12)
        
        # Perform scenario analysis
        analysis = compute_scenario_lab_analysis(financials, request)
        
        # Return structured response
        return ScenarioLabResponse(**analysis)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario analysis failed: {str(e)}")


class ScenarioCompareRequest(BaseModel):
    company_id: str
    scenarios: List[ScenarioLabRequest]


class ScenarioComparison(BaseModel):
    scenario_name: str
    revenue: float
    net_income: float
    margin_pct: float
    runway_months: float
    roi_pct: Optional[float] = None


@router.post("/api/scenario-lab/compare")
async def compare_scenarios(request: ScenarioCompareRequest):
    """
    Compare multiple scenarios side-by-side.
    
    Useful for evaluating different strategic options:
    - Option A: Hire 2 people
    - Option B: Buy equipment
    - Option C: Take loan + expand
    
    Returns a comparison table with key metrics for each scenario.
    """
    try:
        financials = await get_financials(request.company_id, 12)
        
        comparisons = []
        for scenario_req in request.scenarios:
            analysis = compute_scenario_lab_analysis(financials, scenario_req)
            scenario_block = analysis['scenario']
            kpis = analysis['kpis']
            
            comparisons.append(ScenarioComparison(
                scenario_name=scenario_req.scenario_name,
                revenue=scenario_block.revenue,
                net_income=scenario_block.net_income,
                margin_pct=scenario_block.margin_pct,
                runway_months=scenario_block.runway_months,
                roi_pct=kpis.roi_pct
            ))
        
        return {
            'company_id': request.company_id,
            'scenarios': comparisons,
            'baseline_source': financials.provenance.get('source', 'demo')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scenario comparison failed: {str(e)}")


class QuickScenarioRequest(BaseModel):
    company_id: str
    question: str  # Natural language, e.g., "Can I afford a $200k tractor?"


@router.post("/api/scenario-lab/quick")
async def quick_scenario(request: QuickScenarioRequest):
    """
    Quick scenario analysis from natural language question.
    
    This is a simplified endpoint that maps common questions to scenario parameters.
    In production, this would use LLM to parse the question and extract parameters.
    
    For now, it returns a template response suggesting how to structure the full request.
    """
    # In production: use OpenAI to parse question into ScenarioLabRequest
    # For demo: return helpful template
    
    templates = {
        'hire': {
            'description': 'To analyze hiring, use the /analyze endpoint with headcount_delta',
            'example': {
                'scenario_name': 'Hire 2 Technicians',
                'inputs': {
                    'headcount_delta': 2,
                    'price_change_pct': 5  # Assume revenue increase from capacity
                }
            }
        },
        'equipment': {
            'description': 'To analyze equipment purchase, use capex_amount and optionally loan_amount',
            'example': {
                'scenario_name': 'Purchase Equipment',
                'inputs': {
                    'capex_amount': 50000,
                    'loan_amount': 40000,
                    'interest_rate': 6.5
                }
            }
        },
        'price': {
            'description': 'To analyze price changes, use price_change_pct',
            'example': {
                'scenario_name': 'Raise Prices 5%',
                'inputs': {
                    'price_change_pct': 5
                }
            }
        }
    }
    
    # Simple keyword matching (in production, use LLM)
    question_lower = request.question.lower()
    
    if 'hire' in question_lower or 'employee' in question_lower:
        template = templates['hire']
    elif 'equipment' in question_lower or 'buy' in question_lower or 'purchase' in question_lower:
        template = templates['equipment']
    elif 'price' in question_lower or 'raise' in question_lower:
        template = templates['price']
    else:
        template = {
            'description': 'Use /api/scenario-lab/analyze endpoint with specific parameters',
            'example': templates['equipment']['example']
        }
    
    return {
        'question': request.question,
        'suggestion': template['description'],
        'template': template['example'],
        'endpoint': '/api/scenario-lab/analyze'
    }


@router.get("/api/scenario-lab/templates")
async def get_scenario_templates():
    """
    Returns common scenario templates that users can customize.
    
    Helps users get started quickly with pre-configured scenarios.
    """
    return {
        'templates': [
            {
                'name': 'Hire Staff',
                'description': 'Evaluate impact of adding employees',
                'inputs': {
                    'headcount_delta': 1,
                    'price_change_pct': 0
                }
            },
            {
                'name': 'Raise Prices',
                'description': 'Model revenue impact of price increase',
                'inputs': {
                    'price_change_pct': 5,
                    'headcount_delta': 0
                }
            },
            {
                'name': 'Equipment Purchase - Cash',
                'description': 'Buy equipment with cash',
                'inputs': {
                    'capex_amount': 50000,
                    'loan_amount': 0
                }
            },
            {
                'name': 'Equipment Purchase - Financed',
                'description': 'Finance equipment purchase',
                'inputs': {
                    'capex_amount': 50000,
                    'loan_amount': 40000,
                    'interest_rate': 7.0
                }
            },
            {
                'name': 'Expand Operations',
                'description': 'Hire staff and invest in equipment',
                'inputs': {
                    'headcount_delta': 2,
                    'capex_amount': 30000,
                    'price_change_pct': 3
                }
            }
        ]
    }
