from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pathlib import Path
import json

app = FastAPI(title="LightSignal API", version="1.0.0")

# --- CORS setup ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can tighten this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DEMO ENDPOINTS ---

@app.post("/api/overview")
async def fetch_overview(request: Request):
    """
    Returns demo KPIs, benchmarks, and insights.
    In production this would call the Orchestrator or Finance Analyst agent.
    """
    body = await request.json()
    company_id = body.get("company_id", "demo")

    response = {
        "financials": {
            "profile": {
                "company_id": company_id,
                "name": "Demo Manufacturing Co",
                "naics": "332710",
                "size": "small",
                "region": "Midwest",
                "mode": "demo",
            },
            "provenance": {
                "source": "quickbooks_demo",
                "confidence": 0.8,
            },
        },
        "kpis": {
            "revenue_mtd": 31666.67,
            "net_income_mtd": -3166.67,
            "margin_pct": -10.0,
            "cash_available": 125000.00,
            "runway_months": 9.2,
            "confidence": 0.8,
        },
        "benchmarks": [
            {"metric": "Gross Margin %", "value": 38.5, "peer_percentile": 0.45},
            {"metric": "Revenue Growth YoY", "value": 6.1, "peer_percentile": 0.53},
            {"metric": "DSO (days)", "value": 42, "peer_percentile": 0.62},
        ],
        "insights": [
            "Margins are down 10% month-over-month, mainly due to rising COGS.",
            "Cash runway remains healthy at 9.2 months.",
            "Revenue growth slightly outperforms industry peers.",
        ],
    }

    return JSONResponse(content=response)


@app.post("/api/scenario")
async def run_scenario(request: Request):
    """
    Minimal local simulation for Scenario Lab.
    """
    body = await request.json()
    inputs = body.get("inputs", {})

    price_change_pct = float(inputs.get("price_change_pct", 0))
    headcount_delta = float(inputs.get("headcount_delta", 0))

    base = {"revenue": 31666.67, "net_income": -3166.67, "margin_pct": -10.0, "runway_months": 9.2}
    scenario = {
        "revenue": base["revenue"] * (1 + price_change_pct / 100),
        "net_income": base["net_income"] + (headcount_delta * -3500),
        "margin_pct": base["margin_pct"] + (price_change_pct * 0.5),
        "runway_months": max(0, base["runway_months"] - (headcount_delta * 0.3)),
    }

    visuals = [
        {
            "name": "Revenue vs Net Income",
            "points": [
                {"metric": "Revenue", "Base": base["revenue"], "Scenario": scenario["revenue"]},
                {"metric": "Net Income", "Base": base["net_income"], "Scenario": scenario["net_income"]},
            ],
        }
    ]

    insights = [
        f"Revenue adjusted by {price_change_pct}%.",
        f"Headcount change of {headcount_delta} impacts runway.",
    ]

    response = {"base": base, "scenario": scenario, "visuals": visuals, "insights": insights}
    return JSONResponse(content=response)


# --- Health check endpoint ---
@app.get("/health")
async def health():
    return {"ok": True}


# --- NEW: Expose OpenAPI spec for GPT Actions ---
@app.get("/ai/openapi.yaml", include_in_schema=False)
async def openapi_file():
    """
    Serves the OpenAPI spec for GPT Actions.
    """
    p = Path(__file__).parent / "openapi.yaml"
    return Response(p.read_text(encoding="utf-8"), media_type="text/yaml")

