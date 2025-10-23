# app/demo_seed.py
"""
Deterministic demo data seeds for all tabs.
These are returned when company_id='demo' to provide a consistent frontend experience
without calling external APIs or OpenAI.
"""

# -----------------------------------------------------------------------------
# FINANCIAL OVERVIEW (for /api/intent with intent='financial_overview')
# -----------------------------------------------------------------------------
DEMO_FINANCIAL_OVERVIEW = {
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
            "You're up 6.8% MoM; 2.4% above your forecast.",
            "Industry avg gross margin for HVAC services = 33%.",
        ],
        "pricing": {
            "avg_price": 8400,
            "regional_avg": 9200,
            "suggestion": "Consider a 5% increase — estimated profit lift: +$16k per quarter."
        },
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
        "dso_days": 36.0,
        "dpo_days": 42.0,
        "inventory_turns": 6.2,
        "ccc_days": 0.0,  # computed: dso + days_inventory - dpo
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

# -----------------------------------------------------------------------------
# SCENARIOS (for /api/ai/scenarios/full)
# -----------------------------------------------------------------------------
DEMO_SCENARIOS_FULL = {
    "kpis": {
        "scenarios_count": 3,
        "avg_roi_pct": 12.4,
        "best_scenario_id": "sc-hire-2",
        "runway_delta_best": 2.3,
    },
    "insights": [
        "Hiring 2 technicians with 5% price increase yields highest ROI of 18%.",
        "Equipment purchase scenario extends runway by 1.2 months if financed at <7%.",
        "Doing nothing keeps runway at 7.2 months; consider proactive expansion.",
    ],
    "scenarios": [
        {
            "id": "sc-hire-2",
            "name": "Hire 2 Technicians",
            "description": "Add capacity to handle more jobs",
            "inputs": {"headcount_delta": 2, "price_change_pct": 5},
            "results": {
                "revenue_delta_pct": 18.0,
                "net_income_delta": 12000,
                "margin_pct": 0.14,
                "runway_months": 9.5,
                "roi_pct": 18.2,
            },
        },
        {
            "id": "sc-equip",
            "name": "Purchase Equipment",
            "description": "Buy $50k HVAC diagnostic tools",
            "inputs": {"capex_amount": 50000, "loan_amount": 40000, "interest_rate": 6.5},
            "results": {
                "revenue_delta_pct": 8.0,
                "net_income_delta": 4200,
                "margin_pct": 0.13,
                "runway_months": 8.4,
                "roi_pct": 10.5,
            },
        },
        {
            "id": "sc-baseline",
            "name": "Baseline (No Change)",
            "description": "Current trajectory",
            "inputs": {},
            "results": {
                "revenue_delta_pct": 0.0,
                "net_income_delta": 0,
                "margin_pct": 0.12,
                "runway_months": 7.2,
                "roi_pct": 0.0,
            },
        },
    ],
    "visuals": [
        {
            "type": "bar",
            "title": "ROI by Scenario",
            "labels": ["Hire 2", "Equipment", "Baseline"],
            "values": [18.2, 10.5, 0.0],
        }
    ],
}

# -----------------------------------------------------------------------------
# OPPORTUNITIES (for /api/ai/opportunities/full)
# -----------------------------------------------------------------------------
DEMO_OPPORTUNITIES_FULL = {
    "kpis": {
        "active_count": 5,
        "potential_value": 320000,
        "avg_fit_score": 0.76,
        "event_readiness": 0.68,
        "historical_roi": 0.21,
    },
    "insights": [
        "Severe heat forecast expected near Austin may boost HVAC service demand in the next 10 days.",
        "Local utility efficiency rebates open for SMB retrofits; average award $3k–$12k.",
        "Two city RFPs closing within 14 days; consider partnering to improve award odds.",
    ],
    "items": [
        {
            "title": "City Facilities HVAC Preventive Contract",
            "category": "bid",
            "date": "2025-10-18",
            "deadline": "2025-10-25",
            "fit_score": 0.83,
            "roi_est": 0.34,
            "link": "https://example.gov/rfp/hvac-preventive",
        },
        {
            "title": "Austin Energy Small Business Efficiency Rebate",
            "category": "grant",
            "deadline": "2025-11-05",
            "fit_score": 0.71,
            "roi_est": 0.28,
            "link": "https://austinenergy.com/rebates/smb",
        },
        {
            "title": "Regional Contractor Networking Night",
            "category": "event",
            "date": "2025-10-22",
            "fit_score": 0.62,
            "roi_est": 0.12,
            "link": "https://example.com/events/regional-contractors",
        },
        {
            "title": "Supplier Bulk Filter Promo (Q4)",
            "category": "partner",
            "deadline": "2025-10-30",
            "fit_score": 0.66,
            "roi_est": 0.17,
            "link": "https://supplier.example.com/promos/q4-filters",
        },
        {
            "title": "Hot Weather Alert — Load Spike",
            "category": "weather",
            "date": "2025-10-20",
            "fit_score": 0.80,
            "roi_est": 0.10,
            "weather": "Heat index >100°F",
        },
    ],
    "visuals": [
        {
            "type": "bar",
            "title": "Potential Value by Category",
            "labels": ["bid", "grant", "event", "partner", "weather"],
            "values": [180000, 65000, 10000, 45000, 20000],
        }
    ],
}

# -----------------------------------------------------------------------------
# DEMAND (for /api/ai/demand/full)
# -----------------------------------------------------------------------------
DEMO_DEMAND_FULL = {
    "kpis": {
        "forecast_next_month": 92000,
        "confidence": 0.82,
        "peak_day": "2025-11-15",
        "seasonal_index": 1.08,
    },
    "insights": [
        "Demand forecast for November: $92k revenue (+9% vs Oct) driven by heating season onset.",
        "Peak demand expected around Nov 15; ensure adequate technician coverage.",
        "Weather patterns suggest 8% higher emergency call volume next month.",
    ],
    "forecast": [
        {"month": "2025-11", "best": 98000, "base": 92000, "worst": 85000},
        {"month": "2025-12", "best": 105000, "base": 96000, "worst": 88000},
        {"month": "2026-01", "best": 110000, "base": 102000, "worst": 92000},
    ],
    "drivers": [
        {"name": "Seasonal heating demand", "impact_pct": 15.2},
        {"name": "Marketing campaign lift", "impact_pct": 5.8},
        {"name": "Weather volatility", "impact_pct": 8.1},
    ],
    "visuals": [
        {
            "type": "line",
            "title": "Revenue Forecast (3 months)",
            "labels": ["Nov", "Dec", "Jan"],
            "datasets": [
                {"name": "Best", "values": [98000, 105000, 110000]},
                {"name": "Base", "values": [92000, 96000, 102000]},
                {"name": "Worst", "values": [85000, 88000, 92000]},
            ],
        }
    ],
}

# -----------------------------------------------------------------------------
# REVIEWS (for /api/ai/reviews/full)
# -----------------------------------------------------------------------------
DEMO_REVIEWS_FULL = {
    "kpis": {
        "avg_rating": 4.6,
        "total_reviews": 142,
        "response_rate": 0.89,
        "sentiment_score": 0.78,
    },
    "insights": [
        "Overall sentiment is positive; 'professionalism' and 'quick response' are top themes.",
        "3 recent reviews mention pricing concerns — consider bundling services for perceived value.",
        "Response rate of 89% is strong; aim to respond to all reviews within 24 hours.",
    ],
    "recent": [
        {
            "id": "rev-001",
            "date": "2025-10-18",
            "rating": 5,
            "text": "Excellent service! Technician was professional and fixed our AC in under an hour.",
            "sentiment": "positive",
            "themes": ["professionalism", "speed"],
        },
        {
            "id": "rev-002",
            "date": "2025-10-16",
            "rating": 4,
            "text": "Good work, but pricing seemed a bit high compared to competitors.",
            "sentiment": "mixed",
            "themes": ["pricing", "quality"],
        },
        {
            "id": "rev-003",
            "date": "2025-10-14",
            "rating": 5,
            "text": "Always reliable. Been using them for 3 years and never disappointed.",
            "sentiment": "positive",
            "themes": ["reliability", "loyalty"],
        },
    ],
    "themes": [
        {"name": "professionalism", "count": 38, "sentiment": 0.92},
        {"name": "speed", "count": 29, "sentiment": 0.88},
        {"name": "pricing", "count": 18, "sentiment": 0.42},
        {"name": "quality", "count": 45, "sentiment": 0.85},
        {"name": "reliability", "count": 31, "sentiment": 0.91},
    ],
    "visuals": [
        {
            "type": "bar",
            "title": "Rating Distribution",
            "labels": ["1 star", "2 star", "3 star", "4 star", "5 star"],
            "values": [2, 5, 12, 48, 75],
        }
    ],
}

# -----------------------------------------------------------------------------
# HEALTH (for /api/ai/health/full)
# -----------------------------------------------------------------------------
DEMO_HEALTH_FULL = {
    "kpis": {
        "overall_score": 88,
        "financial_health": 85,
        "operational_health": 90,
        "market_health": 86,
    },
    "insights": [
        "Overall health score of 88 indicates strong performance across all dimensions.",
        "Cash runway of 7.2 months is adequate but could be improved with better collections.",
        "Operational efficiency is excellent; consider scaling up capacity.",
    ],
    "dimensions": [
        {
            "name": "Financial",
            "score": 85,
            "factors": [
                {"metric": "Cash Runway", "value": 7.2, "benchmark": 6.0, "status": "good"},
                {"metric": "Profit Margin", "value": 0.12, "benchmark": 0.09, "status": "good"},
                {"metric": "Debt/Equity", "value": 0.9, "benchmark": 1.2, "status": "good"},
            ],
        },
        {
            "name": "Operational",
            "score": 90,
            "factors": [
                {"metric": "Utilization", "value": 0.82, "benchmark": 0.75, "status": "excellent"},
                {"metric": "Response Time", "value": 2.1, "benchmark": 3.0, "status": "excellent"},
            ],
        },
        {
            "name": "Market",
            "score": 86,
            "factors": [
                {"metric": "Market Share", "value": 0.08, "benchmark": 0.06, "status": "good"},
                {"metric": "Customer Retention", "value": 0.91, "benchmark": 0.85, "status": "excellent"},
            ],
        },
    ],
    "alerts": [
        {"level": "yellow", "text": "Cash conversion cycle increased by 4 days last month", "priority": "medium"},
        {"level": "green", "text": "All operational metrics above industry benchmarks", "priority": "low"},
    ],
}

# -----------------------------------------------------------------------------
# DEBT (for /api/ai/debt/full)
# -----------------------------------------------------------------------------
DEMO_DEBT_FULL = {
    "kpis": {
        "total_debt": 185000,
        "monthly_payment": 4200,
        "avg_interest_rate": 0.068,
        "debt_to_income": 0.42,
        "credit_utilization": 0.35,
    },
    "insights": [
        "Total debt of $185k with avg interest rate 6.8% is manageable given current revenue.",
        "Consider refinancing the equipment loan at 8.5% to a lower rate — potential savings $800/year.",
        "Credit utilization at 35% is healthy; maintain below 40% for best credit terms.",
    ],
    "accounts": [
        {
            "id": "debt-001",
            "type": "term_loan",
            "lender": "Regional Bank",
            "balance": 120000,
            "rate": 0.065,
            "monthly_payment": 2800,
            "remaining_months": 48,
        },
        {
            "id": "debt-002",
            "type": "equipment_loan",
            "lender": "Equipment Finance Co",
            "balance": 45000,
            "rate": 0.085,
            "monthly_payment": 1100,
            "remaining_months": 42,
        },
        {
            "id": "debt-003",
            "type": "credit_card",
            "lender": "Business Credit Card",
            "balance": 20000,
            "rate": 0.189,
            "monthly_payment": 300,
            "credit_limit": 50000,
        },
    ],
    "optimization": [
        {
            "type": "refinance",
            "account_id": "debt-002",
            "current_rate": 0.085,
            "suggested_rate": 0.065,
            "annual_savings": 900,
            "confidence": 0.72,
        },
        {
            "type": "paydown",
            "account_id": "debt-003",
            "reason": "High interest rate",
            "monthly_extra": 500,
            "months_saved": 18,
            "interest_saved": 4200,
        },
    ],
    "visuals": [
        {
            "type": "pie",
            "title": "Debt by Type",
            "labels": ["Term Loan", "Equipment", "Credit Card"],
            "values": [120000, 45000, 20000],
        }
    ],
}

# -----------------------------------------------------------------------------
# TAX (for /api/ai/tax/full)
# -----------------------------------------------------------------------------
DEMO_TAX_FULL = {
    "kpis": {
        "ytd_liability": 28500,
        "effective_rate": 0.21,
        "estimated_annual": 38000,
        "next_payment_due": "2025-11-15",
        "optimization_potential": 6200,
    },
    "insights": [
        "YTD tax liability of $28.5k at effective rate 21% is on track for $38k annual.",
        "Section 179 depreciation on recent equipment purchase could save $6.2k this year.",
        "Consider quarterly estimated payments to avoid penalties; next due Nov 15.",
    ],
    "quarterly_plan": {
        "q1": {"due": "2025-04-15", "estimate": 9000, "paid": 9000, "status": "paid"},
        "q2": {"due": "2025-06-15", "estimate": 9500, "paid": 9500, "status": "paid"},
        "q3": {"due": "2025-09-15", "estimate": 10000, "paid": 10000, "status": "paid"},
        "q4": {"due": "2025-12-15", "estimate": 10500, "paid": 0, "status": "pending"},
    },
    "opportunities": [
        {
            "id": "opp-179",
            "type": "deduction",
            "description": "Section 179 depreciation on $50k equipment",
            "potential_savings": 6200,
            "confidence": 0.85,
            "deadline": "2025-12-31",
        },
        {
            "id": "opp-qbi",
            "type": "deduction",
            "description": "Qualified Business Income deduction optimization",
            "potential_savings": 2800,
            "confidence": 0.68,
            "deadline": "2025-12-31",
        },
    ],
    "depreciation": {
        "total_basis": 150000,
        "ytd_depreciation": 18000,
        "remaining": 132000,
        "schedule": [
            {"asset": "Service Truck #1", "method": "MACRS-5", "annual": 8000},
            {"asset": "HVAC Tools", "method": "Section 179", "annual": 10000},
        ],
    },
    "entity_analysis": {
        "current": "LLC-SP",
        "alternatives": [
            {"entity": "S-Corp", "tax_savings": 4200, "complexity": "medium"},
            {"entity": "C-Corp", "tax_savings": -1200, "complexity": "high"},
        ],
    },
}

# -----------------------------------------------------------------------------
# ASSETS (for /api/ai/assets/full)
# -----------------------------------------------------------------------------
DEMO_ASSETS_FULL = {
    "kpis": {
        "total_assets": 12,
        "total_value": 285000,
        "maintenance_due": 3,
        "utilization_avg": 0.78,
        "downtime_hours": 18,
    },
    "insights": [
        "12 assets with total value $285k; 3 require maintenance within 30 days.",
        "Average utilization of 78% is strong; consider adding capacity if demand grows.",
        "Downtime of 18 hours last month was primarily due to scheduled maintenance.",
    ],
    "registry": [
        {
            "id": "asset-001",
            "name": "Service Truck #1",
            "type": "vehicle",
            "value": 45000,
            "purchase_date": "2023-06-15",
            "status": "active",
            "utilization": 0.82,
            "next_maintenance": "2025-11-01",
        },
        {
            "id": "asset-002",
            "name": "HVAC Diagnostic Kit",
            "type": "equipment",
            "value": 12000,
            "purchase_date": "2024-03-10",
            "status": "active",
            "utilization": 0.91,
            "next_maintenance": "2026-03-10",
        },
        {
            "id": "asset-003",
            "name": "Service Truck #2",
            "type": "vehicle",
            "value": 48000,
            "purchase_date": "2024-01-20",
            "status": "active",
            "utilization": 0.75,
            "next_maintenance": "2025-10-28",
        },
    ],
    "maintenance": [
        {
            "asset_id": "asset-001",
            "type": "scheduled",
            "due_date": "2025-11-01",
            "description": "Oil change and tire rotation",
            "cost_estimate": 250,
        },
        {
            "asset_id": "asset-003",
            "type": "scheduled",
            "due_date": "2025-10-28",
            "description": "Brake inspection and fluid check",
            "cost_estimate": 180,
        },
    ],
    "alerts": [
        {"level": "yellow", "text": "Truck #1 maintenance due in 12 days", "asset_id": "asset-001"},
        {"level": "yellow", "text": "Truck #2 maintenance overdue by 2 days", "asset_id": "asset-003"},
    ],
}

# -----------------------------------------------------------------------------
# INVENTORY (for /api/ai/inventory/full)
# -----------------------------------------------------------------------------
DEMO_INVENTORY_FULL = {
    "kpis": {
        "total_items": 45,
        "total_value": 32000,
        "turnover_rate": 6.8,
        "stockout_risk_items": 3,
        "overstock_items": 2,
    },
    "insights": [
        "Inventory turnover of 6.8x is healthy for HVAC parts and supplies.",
        "3 items at risk of stockout; consider reordering R410A refrigerant and filters.",
        "2 items overstocked (condensate pumps, copper fittings); monitor usage trends.",
    ],
    "items": [
        {
            "id": "inv-001",
            "name": "R410A Refrigerant (25lb)",
            "category": "refrigerant",
            "quantity": 4,
            "reorder_point": 6,
            "unit_cost": 280,
            "status": "low",
        },
        {
            "id": "inv-002",
            "name": "HVAC Filters (20x25x1)",
            "category": "filters",
            "quantity": 18,
            "reorder_point": 20,
            "unit_cost": 12,
            "status": "low",
        },
        {
            "id": "inv-003",
            "name": "Condensate Pumps",
            "category": "parts",
            "quantity": 15,
            "reorder_point": 5,
            "unit_cost": 95,
            "status": "overstock",
        },
    ],
    "reorder_suggestions": [
        {"item_id": "inv-001", "suggested_qty": 8, "urgency": "high", "lead_time_days": 3},
        {"item_id": "inv-002", "suggested_qty": 30, "urgency": "medium", "lead_time_days": 5},
    ],
    "visuals": [
        {
            "type": "bar",
            "title": "Inventory Value by Category",
            "labels": ["Refrigerant", "Filters", "Parts", "Tools", "Other"],
            "values": [8400, 4200, 12000, 5200, 2200],
        }
    ],
}

# -----------------------------------------------------------------------------
# PROFILE (for /api/ai/profile/full or GET /api/profile/full)
# -----------------------------------------------------------------------------
DEMO_PROFILE_FULL = {
    "company_id": "demo",
    "general": {
        "legal_name": "Demo HVAC Services LLC",
        "dba": "Demo HVAC",
        "ein": "XX-XXXXXXX",
        "entity_type": "LLC",
        "incorporation_date": "2020-05-15",
        "address": {
            "street": "123 Main St",
            "city": "Austin",
            "state": "TX",
            "zip": "78701",
        },
        "phone": "(512) 555-1234",
        "email": "contact@demohvac.example.com",
        "website": "https://demohvac.example.com",
    },
    "industry": {
        "naics": "238220",
        "description": "Plumbing, Heating, and Air-Conditioning Contractors",
        "region": "Austin, TX Metro",
        "size": "Small (10-50 employees)",
    },
    "operations": {
        "employees": 12,
        "service_area_radius_miles": 50,
        "avg_ticket_size": 850,
        "jobs_per_month": 95,
    },
    "financial_summary": {
        "revenue_ytd": 950000,
        "revenue_last_year": 1020000,
        "avg_monthly_revenue": 84000,
    },
    "assets": [
        {"id": "asset-001", "name": "Service Truck #1", "type": "vehicle", "value": 45000},
        {"id": "asset-002", "name": "HVAC Diagnostic Kit", "type": "equipment", "value": 12000},
    ],
    "benchmarks": {
        "revenue_percentile": 62,
        "margin_percentile": 58,
        "efficiency_percentile": 71,
    },
    "uploads": [],
    "integrations": [
        {"provider": "quickbooks", "status": "not_connected"},
        {"provider": "stripe", "status": "not_connected"},
    ],
}

# -----------------------------------------------------------------------------
# SETTINGS (for /api/settings/full)
# -----------------------------------------------------------------------------
DEMO_SETTINGS_FULL = {
    "user": {
        "name": "Demo User",
        "email": "demo@example.com",
        "role": "owner",
    },
    "company": {
        "company_id": "demo",
        "name": "Demo HVAC Services LLC",
        "timezone": "America/Chicago",
        "fiscal_year_end": "12-31",
    },
    "notifications": {
        "email_alerts": True,
        "sms_alerts": False,
        "weekly_digest": True,
    },
    "integrations": [
        {"provider": "quickbooks", "status": "not_connected"},
        {"provider": "stripe", "status": "not_connected"},
        {"provider": "google_calendar", "status": "not_connected"},
    ],
    "preferences": {
        "currency": "USD",
        "date_format": "MM/DD/YYYY",
        "number_format": "1,234.56",
    },
}

# -----------------------------------------------------------------------------
# ORCHESTRATOR AGENT DEMO (for /api/ai/orchestrate)
# -----------------------------------------------------------------------------
DEMO_ORCHESTRATOR_RESPONSE = {
    "intent": "general_query",
    "answer": "Based on your current financial health (score: 88) and runway of 7.2 months, you have a solid foundation. Consider the 'Hire 2 Technicians' scenario which projects 18% ROI and extends runway to 9.5 months.",
    "insights": [
        "Your operational efficiency (score: 90) suggests capacity for growth.",
        "Marketing spend increased 14% faster than sales — optimize allocation.",
    ],
    "actions": [
        {"type": "navigate", "target": "/scenarios"},
        {"type": "explore", "target": "/opportunities"},
    ],
}

# -----------------------------------------------------------------------------
# FINANCE AGENT DEMO (for /api/ai/finance)
# -----------------------------------------------------------------------------
DEMO_FINANCE_AGENT_RESPONSE = {
    "summary": "Revenue of $84.2k (MTD) is up 6.8% MoM. Gross margin of 36% exceeds industry average of 33%. Net profit margin of 12% is strong. Cash runway of 7.2 months is adequate but could be improved with better collections (DSO: 36 days).",
    "key_metrics": [
        {"metric": "Revenue (MTD)", "value": 84200, "vs_last_month": "+6.8%"},
        {"metric": "Gross Margin", "value": "36%", "vs_industry": "+3%"},
        {"metric": "Net Margin", "value": "12%", "vs_sector": "+3%"},
        {"metric": "Cash Runway", "value": "7.2 months", "status": "adequate"},
    ],
    "recommendations": [
        "Consider 5% price increase — estimated profit lift: +$16k/quarter.",
        "Reduce DSO from 36 to 30 days to improve cash conversion by ~$12k.",
        "Marketing ROI analysis suggests reallocation opportunity — review spend.",
    ],
}

# -----------------------------------------------------------------------------
# RESEARCH AGENT DEMO (for /api/ai/research)
# -----------------------------------------------------------------------------
DEMO_RESEARCH_AGENT_RESPONSE = {
    "summary": "5 active opportunities identified with total potential value of $320k. Top opportunity: City Facilities HVAC Preventive Contract (fit score: 83%, estimated ROI: 34%). Heat forecast for Austin area may boost emergency service demand in next 10 days.",
    "opportunities": [
        {
            "title": "City Facilities HVAC Preventive Contract",
            "fit_score": 0.83,
            "potential_value": 180000,
            "deadline": "2025-10-25",
        },
        {
            "title": "Austin Energy Small Business Efficiency Rebate",
            "fit_score": 0.71,
            "potential_value": 65000,
            "deadline": "2025-11-05",
        },
    ],
    "market_insights": [
        "HVAC industry growth forecast: 4.2% annually through 2028 in Texas.",
        "Residential HVAC replacement cycle averaging 12-15 years; aging housing stock in Austin area presents opportunity.",
    ],
}
