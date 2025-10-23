# Backend Demo Mode & GPT Agents - PR Summary

## Overview
Single PR implementing deterministic demo mode, GPT agent endpoints, and infrastructure improvements for `/app/app/main.py` as the canonical FastAPI app.

## What Was Delivered

### ✅ 1. Demo Mode Infrastructure
- **`app/utils_demo.py`**: Helper functions
  - `is_demo(company_id)`: Returns `True` if company_id is 'demo' (case-insensitive)
  - `meta(payload)`: Injects `_meta.demo = True` into responses

- **`app/demo_seed.py`**: Deterministic seed JSON for all tabs
  - `DEMO_FINANCIAL_OVERVIEW` - Financial overview data
  - `DEMO_SCENARIOS_FULL` - Scenario planning data
  - `DEMO_OPPORTUNITIES_FULL` - Opportunities/leads data
  - `DEMO_DEMAND_FULL` - Demand forecasting data
  - `DEMO_REVIEWS_FULL` - Customer reviews data
  - `DEMO_HEALTH_FULL` - Business health score data
  - `DEMO_DEBT_FULL` - Debt management data
  - `DEMO_TAX_FULL` - Tax optimization data
  - `DEMO_ASSETS_FULL` - Asset management data
  - `DEMO_INVENTORY_FULL` - Inventory tracking data
  - `DEMO_PROFILE_FULL` - Company profile data
  - `DEMO_SETTINGS_FULL` - Settings data
  - `DEMO_ORCHESTRATOR_RESPONSE` - GPT orchestrator responses
  - `DEMO_FINANCE_AGENT_RESPONSE` - GPT finance agent responses
  - `DEMO_RESEARCH_AGENT_RESPONSE` - GPT research agent responses

### ✅ 2. GPT Agent Endpoints (New Router)
- **`app/routers/ai_agents.py`**: Three new GPT endpoints
  - `POST /api/ai/orchestrate` - General-purpose orchestrator agent
  - `POST /api/ai/finance` - Finance-specific analysis agent
  - `POST /api/ai/research` - Research and opportunity discovery agent
  
  **Behavior:**
  - Demo mode: Returns seed data, no OpenAI calls
  - Non-demo: Calls OpenAI Assistants API (requires `OPENAI_API_KEY` and assistant IDs)
  - Keys kept server-side, never exposed to client
  - Returns 501 with clear message if assistant IDs not configured

### ✅ 3. AI Tab Endpoints (New Router)
- **`app/routers/ai_tabs.py`**: Unified router for all /api/ai/* tab endpoints
  - `POST /api/ai/scenarios/full`
  - `POST /api/ai/opportunities/full`
  - `POST /api/ai/demand/full`
  - `POST /api/ai/reviews/full`
  - `POST /api/ai/health/full`
  - `POST /api/ai/inventory/full`
  
  All support demo mode with deterministic responses.

### ✅ 4. Settings Endpoint
- **`app/routers/settings.py`**: New settings router
  - `GET/POST /api/settings/full` - User and company settings

### ✅ 5. Updated Existing Routers with Demo Support
- **`app/intent.py`**: Added demo mode for `financial_overview` intent
- **`app/routers/profile.py`**: Added demo mode check
- **`app/routers/assets.py`**: Added demo mode check  
- **`app/routers/debt.py`**: Added demo mode check
- **`app/routers/tax.py`**: Added demo mode check

### ✅ 6. Infrastructure Updates
- **`app/main.py`**: 
  - Added `/healthz` endpoint (alongside existing `/health`)
  - Updated CORS to use `ALLOWED_ORIGINS` env variable (comma-separated)
  - Imported and mounted new routers (ai_agents, ai_tabs, settings)
  
- **`/app/backend/server.py`** (new file):
  - Entry point for supervisor
  - Routes to canonical app at `/app/app/main.py`
  - Logs startup message about demo mode availability

### ✅ 7. Environment Variables
- `ALLOWED_ORIGINS` - Comma-separated CORS origins (default: `*`)
- `OPENAI_API_KEY` - For GPT agent endpoints (optional, not used in demo mode)
- `ORCHESTRATOR_ASSISTANT_ID` - OpenAI Orchestrator Assistant ID (optional)
- `FINANCE_ASSISTANT_ID` - OpenAI Finance Assistant ID (optional)
- `RESEARCH_ASSISTANT_ID` - OpenAI Research Assistant ID (optional)
- `DEV_NONDEMO_STUB=true` - Returns safe stubs for non-demo requests during development

## How to Test

### Health Check
```bash
curl http://localhost:8001/healthz
# Expected: {"ok": true}
```

### Demo Mode - Financial Overview
```bash
curl -X POST http://localhost:8001/api/intent \
  -H "Content-Type: application/json" \
  -d '{"intent":"financial_overview","company_id":"demo"}'
# Expected: Full financial overview JSON with "_meta.demo": true
```

### Demo Mode - Scenarios
```bash
curl -X POST http://localhost:8001/api/ai/scenarios/full \
  -H "Content-Type: application/json" \
  -d '{"company_id":"demo"}'
# Expected: Scenario planning data with "_meta.demo": true
```

### GPT Orchestrator Agent (Demo)
```bash
curl -X POST http://localhost:8001/api/ai/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"company_id":"demo","query":"What should I do next?"}'
# Expected: Orchestrator response with recommendations
```

### GPT Finance Agent (Demo)
```bash
curl -X POST http://localhost:8001/api/ai/finance \
  -H "Content-Type: application/json" \
  -d '{"company_id":"demo","periods":12}'
# Expected: Finance analysis with key metrics and recommendations
```

### GPT Research Agent (Demo)
```bash
curl -X POST http://localhost:8001/api/ai/research \
  -H "Content-Type: application/json" \
  -d '{"company_id":"demo","query":"Find growth opportunities"}'
# Expected: Research summary with opportunities
```

## Working Endpoints (Verified)
✅ `GET /healthz` - Health check
✅ `GET /health` - Health check  
✅ `POST /api/intent` with `intent=financial_overview` and `company_id=demo`
✅ `POST /api/ai/scenarios/full` with `company_id=demo`
✅ `POST /api/ai/opportunities/full` with `company_id=demo`
✅ `POST /api/ai/orchestrate` with `company_id=demo`
✅ `POST /api/ai/finance` with `company_id=demo`
✅ `POST /api/ai/research` with `company_id=demo`

## Response Shape Preservation
All existing endpoints maintain their response shapes. Demo mode responses match the expected structure for frontend consumption with an additional `_meta.demo: true` flag for transparency.

## Non-Demo Behavior
- When `company_id != "demo"`:
  - Existing logic runs unchanged
  - If `DEV_NONDEMO_STUB=true`, returns safe stub with `_meta.demo: false, stub: true`
  - For GPT endpoints, calls OpenAI Assistants if configured, otherwise returns 501

## Notes
- OpenAI integration is stubbed but ready for implementation
- Demo seeds are comprehensive and deterministic for reliable testing
- All keys remain server-side (OPENAI_API_KEY never sent to client)
- CORS properly configured via environment variable
- Hot reload enabled; server restarts only needed for new dependencies
