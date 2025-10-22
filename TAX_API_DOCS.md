# Tax Optimization API Documentation

## Overview
The Tax Optimization module provides comprehensive tax planning and analysis capabilities for businesses. It includes effective tax rate monitoring, opportunity mining, quarterly planning, entity structure analysis, and depreciation optimization.

## Endpoints

### POST /api/ai/tax/full
**Purpose**: Aggregate tax overview with KPIs, opportunities, benchmarks, and planning tools.

**Request**:
```json
{
  "company_id": "demo",
  "year": 2025,
  "include_peers": true,
  "include_assets": true,
  "include_entity_analysis": true,
  "range": "YTD"
}
```

**Response**: Returns comprehensive tax data including:
- `kpis`: Key tax metrics (ETR, taxable income, estimated liability)
- `opportunities`: Ranked tax-saving opportunities
- `quarterly_plan`: Next due dates, estimates, set-aside recommendations
- `entity_analysis`: Entity structure comparison (LLC vs S-Corp vs C-Corp)
- `depreciation`: Asset depreciation scheduling and optimization
- `priority_actions`: Saved priority items and deadlines

### POST /api/ai/tax/ask
**Purpose**: AI Tax Coach for contextual tax advice.

**Request**:
```json
{
  "company_id": "demo",
  "query": "If I buy a $60k truck this quarter, what's the tax impact?",
  "year": 2025
}
```

**Response**:
```json
{
  "answer": "Estimated Sec. 179 deduction up to $60k subject to limits; projected Q4 liability down ~$2.4k.",
  "assumptions": {"entity": "LLC-SP", "marginal_rate_pct": 24},
  "links": [{"type": "section", "ref": "depreciation"}],
  "actions": [{"type": "priority_add", "payload": {"id": "p-sec179", "deadline": "2025-12-31"}}]
}
```

### POST /api/ai/tax/opportunities
**Purpose**: Mine tax deductions and credits from company data.

**Request**:
```json
{
  "company_id": "demo",
  "year": 2025,
  "max": 25
}
```

**Response**: Returns ranked list of tax opportunities with estimated savings.

### POST /api/ai/tax/quarterly/plan
**Purpose**: Quarterly tax planning with scenarios.

**Request**:
```json
{
  "company_id": "demo",
  "year": 2025,
  "scenarios": [
    {"name": "buy_equipment_now", "capex": 32000, "method": "sec179"},
    {"name": "defer_to_next_q", "capex": 32000, "method": "bonus", "defer": true}
  ]
}
```

**Response**: Due dates, estimated payments, weekly set-aside amounts, and scenario impact analysis.

### POST /api/ai/tax/entity/analyze
**Purpose**: Compare current entity structure vs alternatives.

**Request**:
```json
{
  "company_id": "demo",
  "owner_salary": 65000,
  "owner_draws": 55000,
  "current_entity": "llc_sp"
}
```

**Response**: Current entity and alternative options with estimated annual savings.

### POST /api/ai/tax/depreciation/plan
**Purpose**: Optimize asset depreciation timing (Section 179 vs Bonus vs MACRS).

**Request**:
```json
{
  "company_id": "demo",
  "assets": ["TRK-102", "COFF-12"],
  "year": 2025
}
```

**Response**: Depreciation timeline and optimization notes.

### POST /api/ai/tax/priorities/save
**Purpose**: Save or update priority tax actions.

**Request**:
```json
{
  "company_id": "demo",
  "items": [
    {
      "id": "p-sec179",
      "text": "Maximize Section 179",
      "deadline": "2025-12-31",
      "assignee": "accountant"
    }
  ]
}
```

### POST /api/ai/tax/export
**Purpose**: Generate tax optimization reports.

**Request**:
```json
{
  "company_id": "demo",
  "format": "pdf",
  "variant": "optimization"
}
```

**Response**: Signed URL for downloading the generated report.

## Demo Mode
All endpoints support demo mode with `company_id: "demo"`. Demo data includes:
- Synthesized YTD P&L with $900k revenue, $85k net income
- Demo asset registry for depreciation planning
- Industry benchmark data for peer comparisons
- Realistic tax calculations and opportunities

## Key Features
- **Effective Tax Rate (ETR) Monitoring**: Real-time ETR calculation with peer benchmarks
- **Opportunity Mining**: Automated detection of tax-saving opportunities
- **Quarterly Planning**: Due date tracking, payment estimates, scenario modeling
- **Entity Optimization**: Compare LLC, S-Corp, C-Corp structures
- **Depreciation Optimization**: Section 179 vs Bonus depreciation timing
- **Priority Management**: Track and assign tax-related action items
- **AI Coach**: Natural language tax advice with contextual responses

## Security & Disclaimers
- All responses include disclaimer: "Estimates only — confirm with licensed tax advisor"
- No sensitive data or full IRS publications returned
- Short code references only (e.g., "§179", "Pub 946")
- Confidence scoring for all calculations

## Testing
Comprehensive test suite covers:
- ETR calculations with edge cases (zero/negative income)
- Quarterly planner set-aside math
- Entity analysis savings bounds
- Depreciation schedule totals
- Priority persistence
- Full payload structure validation