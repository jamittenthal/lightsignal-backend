from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal

app = FastAPI(title="LightSignal Backend", version="0.1.0")

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
        return await handle_dashboard(req.input or {}, req.company_id or "demo")
    if req.intent == "financial_overview":
        return await handle_financial_overview(req.input or {}, req.company_id or "demo")
    raise HTTPException(status_code=400, detail="unknown intent")

async def handle_dashboard(input: Dict[str, Any], company_id: str):
    return {
        "kpis": [
            {"key": "revenue_mtd", "label": "Revenue (MTD)", "value": 84200, "delta_pct": 7.2, "href": "/overview"},
            {"key": "net_margin", "label": "Net Profit / Margin %", "value": 0.28, "delta_pct": 1.3, "href": "/overview"},
            {"key": "cash_flow_mtd", "label": "Cash Flow (MTD)", "value": 15500, "delta_pct": -2.1, "href": "/overview"},
            {"key": "runway_months", "label": "Runway (Months)", "value": 7.2, "href": "/overview"},
            {"key": "ai_health", "label": "AI Health Score", "value": 88, "href": "/overview"},
        ],
        "snapshot": "Revenue up 7.2% vs last month · Expenses flat · Profit margin improved to 28%.",
        "alerts": [
            {"level": "red", "text": "Low cash alert if runway < 3 months", "active": False},
            {"level": "yellow", "text": "Spending spike detected", "active": True},
            {"level": "green", "text": "Ahead of target", "active": True},
        ],
        "insights": [
            "Your profit margin improved, but cash conversion slowed — consider faster invoice collection.",
            "Labor costs trending 11% above peers in your industry.",
            "You could safely increase marketing by 5% to maintain margin and growth.",
        ],
        "reminders": [
            {"id": "tax-q", "text": "Quarterly tax payment due in 6 days.", "due": "2025-11-01"},
            {"id": "ins-renew", "text": "Renew business insurance next week.", "due": "2025-10-27"},
            {"id": "payroll", "text": "Payroll approval pending.", "due": "2025-10-22"},
            {"id": "overdue-inv", "text": "Invoice follow-up: 3 clients overdue.", "due": None},
        ],
        "summary": "Cash healthy · Margins strong · No critical risks detected."
    }

async def handle_financial_overview(input: Dict[str, Any], company_id: str):
    dso_days, inventory_turns, dpo_days = 36.0, 6.2, 42.0
    days_inventory = 365.0 / inventory_turns if inventory_turns else 0.0
    ccc_days = round(dso_days + days_inventory - dpo_days, 1)
    return {
        "kpis": [
            {"key": "revenue_mtd", "label": "Total Revenue (MTD)", "value": 84200, "benchmark": "Top 40%"},
            {"key": "gross_margin", "label": "Gross Margin %", "value": 0.36},
            {"key": "opex_ratio", "label": "Operating Expenses", "value": 0.28, "comment": "Below industry avg"},
            {"key": "net_margin", "label": "Net Profit / Margin %", "value": 0.12, "comment": "Above sector 9%"},
            {"key": "cash_flow_mtd", "label": "Cash Flow (MTD)", "value": 15500},
            {"key": "runway", "label": "Runway (Months)", "value": 7.2},
            {"key": "ai_conf", "label": "AI Confidence Score", "value": 0.89},
        ],
        "revenue": {
            "trend": [
                {"month": "2025-08", "value": 78000},
                {"month": "2025-09", "value": 81000},
                {"month": "2025-10", "value": 84200},
            ],
            "cogs": 54000,
            "gross_margin_pct": 0.36,
            "notes": [
                "You’re up 6.8% MoM; 2.4% above your forecast.",
                "Industry avg gross margin for HVAC services = 33%.",
            ],
            "pricing": {"avg_price": 8400, "regional_avg": 9200,
                        "suggestion": "Consider a 5% increase — estimated profit lift: +$16k per quarter."},
        },
        "expenses": {
            "top5": [
                {"name": "Payroll", "value": 42000},
                {"name": "Marketing", "value": 12000},
                {"name": "Rent", "value": 6000},
                {"name": "Utilities", "value": 1200},
                {"name": "Other", "value": 3800},
            ],
            "expense_ratio": 0.28,
            "operating_margin": 0.18,
            "ai_flags": [
                "Marketing spend grew 14% faster than sales last quarter.",
                "Reducing admin costs by 5% extends your cash runway by 1.8 months.",
            ],
        },
        "liquidity": {
            "current_ratio": 1.7,
            "quick_ratio": 1.4,
            "debt_to_equity": 0.9,
            "interest_coverage": 3.4,
        },
        "efficiency": {
            "dso_days": dso_days,
            "dpo_days": dpo_days,
            "inventory_turns": inventory_turns,
            "ccc_days": ccc_days,
        },
        "cashflow": {
            "burn_rate": 32000,
            "runway_months": 7.2,
            "forecast": [
                {"month": "2025-11", "best": 18000, "base": 9000, "worst": -4000},
                {"month": "2025-12", "best": 22000, "base": 12000, "worst": -7000},
            ],
        },
        "variance": {
            "items": [
                {"metric": "Revenue", "actual": 84200, "forecast": 82000},
                {"metric": "COGS", "actual": 54000, "forecast": 56000},
                {"metric": "Expenses", "actual": 23000, "forecast": 22000},
                {"metric": "Profit", "actual": 7200, "forecast": 4000},
            ],
            "forecast_accuracy": 0.89,
        },
        "risks": [
            {"text": "Profit margin dropped 4% due to overtime costs.", "confidence": 0.73},
            {"text": "Cash flow risk flagged for February: projected negative $18k.", "confidence": 0.64},
            {"text": "Debt ratio increased faster than peers — consider refinancing.", "confidence": 0.52},
            {"text": "Fuel prices trending up 12% next quarter — potential COGS impact.", "confidence": 0.41},
        ],
    }
