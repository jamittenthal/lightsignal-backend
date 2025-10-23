from fastapi import APIRouter, HTTPException
from ..schemas import (
    TaxFullRequest, TaxFullResponse, TaxAskRequest, TaxAskResponse, TaxFullResponse as TF,
    PrioritiesSaveRequest, QuarterlyPlanResponse, PrioritiesSaveRequest as PSR, PrioritiesSaveRequest,
    QuarterlyPlanResponse as QPR, EntityAnalysisResponse, DepreciationPlanResponse, ExportRequest
)
from ..services.tax_engine import (
    tax_full, meta_top, compute_opportunities, compute_quarterly_plan, analyze_entity, plan_depreciation, save_priorities
)
from ..utils_demo import is_demo, meta
from ..demo_seed import DEMO_TAX_FULL

router = APIRouter()


@router.post("/api/ai/tax/full", response_model=TaxFullResponse)
async def tax_full_endpoint(req: TaxFullRequest):
    # Demo mode check
    if is_demo(req.company_id):
        response = DEMO_TAX_FULL.copy()
        return meta(response)
    
    # Non-demo: existing logic
    res = tax_full(req.company_id, req.year, include_peers=req.include_peers, include_assets=req.include_assets, include_entity_analysis=req.include_entity_analysis, range=req.range)
    # Attach provenance from services
    # match schema: quarterly_plan and others expect _meta inside - ensure it's present
    # map nested meta keys to 'meta' alias expected by Pydantic
    res_quarterly = res.get("quarterly_plan", {})
    if "_meta" in res_quarterly:
        res_quarterly["meta"] = res_quarterly.pop("_meta")
    res_entity = res.get("entity_analysis", {})
    if "_meta" in res_entity:
        res_entity["meta"] = res_entity.pop("_meta")
    res_dep = res.get("depreciation", {})
    if "_meta" in res_dep:
        res_dep["meta"] = res_dep.pop("_meta")

    # top-level meta
    if "_meta" in res:
        res["meta"] = res.pop("_meta")
        res["meta"]["provenance"]["notes"].append("Estimates only — confirm with licensed tax advisor.")

    return res


@router.post("/api/ai/tax/ask", response_model=TaxAskResponse)
async def tax_ask(req: TaxAskRequest):
    # Demo: simple rule-based answer
    answer = "Estimated Sec. 179 deduction up to $60k subject to limits; projected Q4 liability down ~$2.4k."
    assumptions = {"entity": "LLC-SP", "marginal_rate_pct": 24}
    links = [{"type": "section", "ref": "depreciation"}, {"type": "section", "ref": "quarterly_plan"}]
    actions = [{"type": "priority_add", "payload": {"id": "p-sec179", "deadline": f"{req.year}-12-31"}}]
    return {"answer": answer, "assumptions": assumptions, "links": links, "actions": actions, "_meta": meta_top(confidence="low")}


@router.post("/api/ai/tax/opportunities")
async def tax_opportunities(req: dict):
    company_id = req.get("company_id")
    year = req.get("year")
    max_items = req.get("max", 25)
    ops = compute_opportunities({"company_id": company_id, "ytd": {}, "assets_map_path": "data/demo/assets.json"}, max_items=max_items)
    return {"opportunities": ops, "_meta": meta_top(confidence="low")}


@router.post("/api/ai/tax/quarterly/plan", response_model=QuarterlyPlanResponse)
async def tax_quarterly_plan(req: dict):
    company_id = req.get("company_id")
    year = req.get("year")
    scenarios = req.get("scenarios", [])
    out = compute_quarterly_plan(company_id, year, scenarios)
    # map to response model
    return {
        "next_due_date": out.get("next_due_date"),
        "estimate_due": out.get("estimate_due"),
        "set_aside_weekly": out.get("set_aside_weekly"),
        "scenarios": out.get("scenarios"),
        "_meta": out.get("_meta"),
    }


@router.post("/api/ai/tax/entity/analyze", response_model=EntityAnalysisResponse)
async def tax_entity_analyze(req: dict):
    company_id = req.get("company_id")
    owner_salary = req.get("owner_salary", 65000)
    owner_draws = req.get("owner_draws", 55000)
    current_entity = req.get("current_entity", "llc_sp")
    out = analyze_entity(company_id, owner_salary, owner_draws, current_entity)
    return out


@router.post("/api/ai/tax/depreciation/plan", response_model=DepreciationPlanResponse)
async def tax_depreciation_plan(req: dict):
    company_id = req.get("company_id")
    assets = req.get("assets", [])
    year = req.get("year")
    out = plan_depreciation(company_id, assets, year)
    return out


@router.post("/api/ai/tax/priorities/save")
async def tax_priorities_save(req: PrioritiesSaveRequest):
    out = save_priorities(req.company_id, [i.model_dump() for i in req.items])
    return out


@router.post("/api/ai/tax/export")
async def tax_export(req: dict):
    # Demo: return placeholder signed URL
    company_id = req.get("company_id")
    fmt = req.get("format", "pdf")
    variant = req.get("variant", "optimization")
    url = f"signed://{company_id}-tax-{variant}.{fmt}"
    return {"url": url, "_meta": meta_top(confidence="high")}
