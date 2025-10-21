from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
from datetime import date, timedelta

router = APIRouter(prefix="/api", tags=["intent"])

class IntentRequest(BaseModel):
  intent: str
  input: Optional[Dict[str, Any]] = None
  company_id: Optional[str] = None

@router.post("/intent")
def handle_intent(req: IntentRequest):
  intent = (req.intent or "").lower()
  payload = req.input or {}
  company_id = req.company_id or "demo"

  if intent == "dashboard":
    return handle_dashboard(payload, company_id)
  if intent == "financial_overview":
    return handle_financial_overview(payload, company_id)

  raise HTTPException(status_code=400, detail="unknown_intent")

def handle_dashboard(input: Dict[str, Any], company_id: str) -> Dict[str, Any]:
  # Sub-actions (all stay under /api/intent)
  action = (input.get("action") or "").lower()

  if action == "quick_forecast":
    horizon = int(input.get("horizon_days", 30))
    start_cash = 100000
    out = []
    for d in range(1, horizon + 1):
      # toy projection
      out.append({"day": d, "cash": start_cash + 500 * d - 350 * (d // 3)})
    return {"ok": True, "forecast": out}

  if action == "ask_advisor":
    q = input.get("question", "")
    return {"ok": True, "reply": f"Based on your question: '{q}', you can likely proceed if cash stays positive for 90 days. Try a small pilot first."}

  if action == "update_reminder":
    # fake success (your UI just needs an ack)
    return {"ok": True}

  # Default dashboard payload (safe demo data)
  return {
    "kpis": {
      "revenue_mtd": {"label": "Revenue (MTD)", "value": 84250, "delta_pct": 0.072},
      "net_profit_margin": {"label": "Net Profit / Margin %", "value": 0.28},
      "cash_flow_mtd": {"label": "Cash Flow (MTD)", "in": 120000, "out": 103500, "net": 16500},
      "runway_months": {"label": "Runway (Months)", "value": 7.2},
      "ai_health_score": {"label": "AI Health Score", "value": 88},
    },
    "snapshot": "Revenue up 7.2% vs last month · Expenses flat · Profit margin improved to 28%.",
    "alerts": [
      {"level": "red", "text": "Low cash alert: runway < 3 months", "code": "low_runway", "active": False},
      {"level": "yellow", "text": "Spending spike detected", "code": "spend_spike", "active": False},
      {"level": "green", "text": "Ahead of target", "code": "ahead_target", "active": True},
    ],
    "insights": [
      {"text": "Profit margin improved, but cash conversion slowed — consider faster invoice collection.", "confidence": 0.81},
      {"text": "Labor costs trending 11% above peers.", "confidence": 0.77},
      {"text": "You could safely increase marketing by ~5% to maintain margin and growth.", "confidence": 0.7},
    ],
    "reminders": [
      {"id": "tax-q", "text": "Quarterly tax payment due in 6 days.", "due": str(date.today() + timedelta(days=6)), "status": "open"},
      {"id": "insurance-renewal", "text": "Renew business insurance next week.", "due": str(date.today() + timedelta(days=7)), "status": "open"},
      {"id": "payroll", "text": "Payroll approval pending.", "due": str(date.today() + timedelta(days=2)), "status": "open"},
      {"id": "invoice-followup", "text": "Invoice follow-up: 3 clients overdue.", "due": str(date.today() + timedelta(days=1)), "status": "open"},
    ],
    "summary": "Cash healthy · Margins strong · No critical risks detected.",
  }

def handle_financial_overview(input: Dict[str, Any], company_id: str) -> Dict[str, Any]:
  # Default FO payload (safe demo data)
  return {
    "kpis": {
      "total_revenue": {"mtd": 84250, "qtd": 242300, "ytd": 1840300, "industry_percentile": 60},
      "gross_margin": {"value": 0.38},
      "opex_ratio": {"value": 0.28},
      "net_margin": {"value": 0.12, "industry": 0.09},
      "cash_flow_mtd": {"net": 16500, "status": "positive"},
      "runway_months": {"value": 7.2},
      "ai_confidence": {"value": 0.9},
    },
    "revenue": {
      "trend": [
        {"date": str(date.today().replace(day=1)), "value": 2500},
        {"date": str(date.today().replace(day=2)), "value": 3100},
      ],
      "target": [
        {"date": str(date.today().replace(day=1)), "value": 2400},
        {"date": str(date.today().replace(day=2)), "value": 3000},
      ],
      "notes": ["You’re up 6.8% MoM; 2.4% above your forecast."],
    },
    "profit_waterfall": [
      {"step": "Revenue", "value": 100000},
      {"step": "COGS", "value": -62000},
      {"step": "OpEx", "value": -20000},
      {"step": "EBITDA", "value": 18000},
      {"step": "Taxes", "value": -6000},
      {"step": "Net Profit", "value": 12000},
    ],
    "expense": {
      "top_categories": [
        {"name": "Payroll", "value": 48000},
        {"name": "Marketing", "value": 12000},
        {"name": "Rent", "value": 8000},
        {"name": "Utilities", "value": 3000},
        {"name": "Other", "value": 4000},
      ],
      "ratio": 0.28,
      "operating_margin": 0.18,
    },
    "liquidity": {
      "current_ratio": 1.8,
      "quick_ratio": 1.4,
      "debt_to_equity": 0.8,
      "interest_coverage": 3.4,
    },
    "efficiency": {
      "dso_days": 35,
      "dpo_days": 42,
      "inventory_turns": 6.2,
      "ccc_days": 29,
    },
    "cashflow": {
      "burn_rate": 32000,
      "runway_months": 7.2,
      "forecast": [
        {"month": "2025-11", "base": 8000, "best": 16000, "worst": -5000},
        {"month": "2025-12", "base": 7000, "best": 15000, "worst": -6000},
      ],
      "net_3mo": [10000, -5000, 3000],
    },
    "variance": {
      "rows": [
        {"metric": "Revenue", "actual": 100000, "forecast": 98000, "error_pct": -0.02},
        {"metric": "COGS", "actual": 62000, "forecast": 61000, "error_pct": -0.016},
      ],
      "forecast_accuracy": 0.89,
    },
    "risks": [
      {"text": "Profit margin dropped 4% due to overtime costs.", "mitigation": "Adjust staffing mix", "confidence": 0.7, "industry_percentile": 40},
      {"text": "Cash flow risk flagged for February: projected -$18k.", "mitigation": "Tighten AR collections", "confidence": 0.65, "industry_percentile": 35},
    ],
  }
