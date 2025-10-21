from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal
from datetime import datetime, timedelta
import random

app = FastAPI(title="LightSignal Backend", version="0.1.0")

# Add CORS middleware with permissive settings (to be locked down later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: later restrict to Vercel preview + prod domains
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"ok": True}

class IntentRequest(BaseModel):
    intent: Literal["dashboard", "financial_overview"]
    input: Optional[Dict[str, Any]] = {}
    company_id: Optional[str] = "demo"

@app.post("/api/intent")
async def intent_endpoint(req: IntentRequest):
    if req.intent == "dashboard":
        # Handle sub-actions for dashboard
        if req.input and req.input.get("action"):
            if req.input["action"] == "quick_forecast" and "horizon_days" in req.input:
                days = min(90, int(req.input["horizon_days"]))
                forecast = []
                base = 100000
                for i in range(days):
                    forecast.append({
                        "day": i + 1,
                        "cash": base + random.randint(-5000, 5000)
                    })
                return {"ok": True, "forecast": forecast}
            elif req.input["action"] == "ask_advisor" and "question" in req.input:
                return {
                    "ok": True,
                    "reply": "Based on your current metrics, I recommend focusing on improving cash conversion cycle. Consider negotiating better payment terms with suppliers."
                }
            elif req.input["action"] == "update_reminder" and "id" in req.input and "op" in req.input:
                return {"ok": True}
        
        return await handle_dashboard(req.input or {}, req.company_id or "demo")
    
    if req.intent == "financial_overview":
        return await handle_financial_overview(req.input or {}, req.company_id or "demo")
    
    raise HTTPException(status_code=400, detail="unknown intent")

async def handle_dashboard(input: Dict[str, Any], company_id: str):
    return {
        "kpis": {
            "revenue_mtd": {"label": "Revenue (MTD)", "value": 84250, "delta_pct": 0.072},
            "net_profit_margin": {"label": "Net Profit / Margin %", "value": 0.28},
            "cash_flow_mtd": {"label": "Cash Flow (MTD)", "in": 120000, "out": 103500, "net": 16500},
            "runway_months": {"label": "Runway (Months)", "value": 7.2},
            "ai_health_score": {"label": "AI Health Score", "value": 88}
        },
        "snapshot": "Revenue up 7.2% vs last month · Expenses flat · Profit margin improved to 28%.",
        "alerts": [
            {"level": "red", "text": "Low cash alert: runway < 3 months", "code": "low_runway", "active": False},
            {"level": "yellow", "text": "Spending spike detected", "code": "spend_spike", "active": False},
            {"level": "green", "text": "Ahead of target", "code": "ahead_target", "active": True}
        ],
        "insights": [
            {"text": "Profit margin improved, but cash conversion slowed — consider faster invoice collection.", "confidence": 0.81},
            {"text": "Labor costs trending 11% above peers.", "confidence": 0.77},
            {"text": "You could safely increase marketing by ~5% to maintain margin and growth.", "confidence": 0.7}
        ],
        "reminders": [
            {"id": "tax-q", "text": "Quarterly tax payment due in 6 days.", "due": "2025-11-15", "status": "open"},
            {"id": "insurance-renewal", "text": "Renew business insurance next week.", "due": "2025-10-28", "status": "open"},
            {"id": "payroll", "text": "Payroll approval pending.", "due": "2025-10-22", "status": "open"},
            {"id": "invoice-followup", "text": "Invoice follow-up: 3 clients overdue.", "due": "2025-10-21", "status": "open"}
        ],
        "summary": "Cash healthy · Margins strong · No critical risks detected."
    }

async def handle_financial_overview(input: Dict[str, Any], company_id: str):
    return {
        "kpis": {
            "total_revenue": {"mtd": 84250, "qtd": 242300, "ytd": 1840300, "industry_percentile": 60},
            "gross_margin": {"value": 0.38},
            "opex_ratio": {"value": 0.28},
            "net_margin": {"value": 0.12, "industry": 0.09},
            "cash_flow_mtd": {"net": 16500, "status": "positive"},
            "runway_months": {"value": 7.2},
            "ai_confidence": {"value": 0.9}
        },
        "revenue": {
            "trend": [
                {"date": "2025-10-01", "value": 2500},
                {"date": "2025-10-02", "value": 3100}
            ],
            "target": [
                {"date": "2025-10-01", "value": 2400},
                {"date": "2025-10-02", "value": 3000}
            ],
            "notes": ["You're up 6.8% MoM; 2.4% above your forecast."]
        },
        "profit_waterfall": [
            {"step": "Revenue", "value": 100000},
            {"step": "COGS", "value": -62000},
            {"step": "OpEx", "value": -20000},
            {"step": "EBITDA", "value": 18000},
            {"step": "Taxes", "value": -6000},
            {"step": "Net Profit", "value": 12000}
        ],
        "expense": {
            "top_categories": [
                {"name": "Payroll", "value": 48000},
                {"name": "Marketing", "value": 12000},
                {"name": "Rent", "value": 8000},
                {"name": "Utilities", "value": 3000},
                {"name": "Other", "value": 4000}
            ],
            "ratio": 0.28,
            "operating_margin": 0.18
        },
        "liquidity": {
            "current_ratio": 1.8,
            "quick_ratio": 1.4,
            "debt_to_equity": 0.8,
            "interest_coverage": 3.4
        },
        "efficiency": {
            "dso_days": 35,
            "dpo_days": 42,
            "inventory_turns": 6.2,
            "ccc_days": 29
        },
        "cashflow": {
            "burn_rate": 32000,
            "runway_months": 7.2,
            "forecast": [
                {"month": "2025-11", "base": 8000, "best": 16000, "worst": -5000},
                {"month": "2025-12", "base": 7000, "best": 15000, "worst": -6000}
            ],
            "net_3mo": [10000, -5000, 3000]
        },
        "variance": {
            "rows": [
                {"metric": "Revenue", "actual": 100000, "forecast": 98000, "error_pct": -0.02},
                {"metric": "COGS", "actual": 62000, "forecast": 61000, "error_pct": -0.016}
            ],
            "forecast_accuracy": 0.89
        },
        "risks": [
            {"text": "Profit margin dropped 4% due to overtime costs.", "mitigation": "Adjust staffing mix", "confidence": 0.7, "industry_percentile": 40},
            {"text": "Cash flow risk flagged for February: projected -$18k.", "mitigation": "Tighten AR collections", "confidence": 0.65, "industry_percentile": 35}
        ]
    }