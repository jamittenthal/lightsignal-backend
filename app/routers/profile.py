from fastapi import APIRouter, HTTPException
from typing import Any
from fastapi import Body
from ..schemas import (
    ProfileFullRequest,
    ProfileFullResponse,
    SaveOK,
    IndustryBlock,
    NAICSSearchRequest,
    NAICSSearchResponse,
    UploadListRequest,
    UploadUploadRequest,
    UploadExtractRequest,
    CompletenessRecalcRequest,
    ExportRequest,
)
from ..services import profile_engine
from ..utils_demo import is_demo, meta
from ..demo_seed import DEMO_PROFILE_FULL

router = APIRouter()


@router.post("/api/ai/profile/full", response_model=ProfileFullResponse)
def profile_full(req: ProfileFullRequest):
    # Demo mode check
    if is_demo(req.company_id):
        response = DEMO_PROFILE_FULL.copy()
        return meta(response)
    
    # Non-demo: existing logic
    res = profile_engine.get_full(
        req.company_id,
        include_financial_summary=req.include_financial_summary,
        include_assets=req.include_assets,
        include_benchmarks=req.include_benchmarks,
        include_uploads=req.include_uploads,
        include_integrations=req.include_integrations,
    )
    return res


@router.post("/api/ai/profile/general/save", response_model=SaveOK)
def save_general(payload: dict = Body(...)):
    # payload should contain company_id and general
    company_id = payload.get("company_id")
    general = payload.get("general")
    if not company_id or not general:
        raise HTTPException(400, "missing")
    profile_engine.save_general(company_id, general)
    return {"ok": True, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/industry/save", response_model=SaveOK)
def save_industry(payload: dict = Body(...)):
    company_id = payload.get("company_id")
    industry = payload.get("industry")
    if not company_id or not industry:
        raise HTTPException(400, "missing")
    profile_engine.save_industry(company_id, industry)
    return {"ok": True, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/industry/naics/search", response_model=NAICSSearchResponse)
def naics_search(req: NAICSSearchRequest = Body(...)):
    results = profile_engine.naics_search(req.q, req.limit)
    return {"results": results, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/operations/save", response_model=SaveOK)
def operations_save(payload: dict = Body(...)):
    company_id = payload.get("company_id")
    ops = payload.get("operations")
    if not company_id or ops is None:
        raise HTTPException(400, "missing")
    profile_engine.save_operations(company_id, ops)
    return {"ok": True, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/financial/save", response_model=SaveOK)
def financial_save(payload: dict = Body(...)):
    company_id = payload.get("company_id")
    fin = payload.get("financial")
    if not company_id or fin is None:
        raise HTTPException(400, "missing")
    profile_engine.save_generic(company_id, "financial", fin)
    return {"ok": True, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/assets/save", response_model=SaveOK)
def assets_save(payload: dict = Body(...)):
    company_id = payload.get("company_id")
    assets = payload.get("assets")
    if not company_id or assets is None:
        raise HTTPException(400, "missing")
    # support single or bulk
    if isinstance(assets, list):
        for a in assets:
            profile_engine.upsert_asset(company_id, a)
    else:
        profile_engine.upsert_asset(company_id, assets)
    return {"ok": True, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/assets/delete", response_model=SaveOK)
def assets_delete(payload: dict = Body(...)):
    company_id = payload.get("company_id")
    asset_id = payload.get("id")
    if not company_id or not asset_id:
        raise HTTPException(400, "missing")
    profile_engine.delete_asset(company_id, asset_id)
    return {"ok": True, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/customers/save", response_model=SaveOK)
def customers_save(payload: dict = Body(...)):
    company_id = payload.get("company_id")
    customers = payload.get("customers")
    if not company_id or customers is None:
        raise HTTPException(400, "missing")
    profile_engine.save_generic(company_id, "customers", customers)
    return {"ok": True, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/risk/save", response_model=SaveOK)
def risk_save(payload: dict = Body(...)):
    company_id = payload.get("company_id")
    risk = payload.get("risk")
    if not company_id or risk is None:
        raise HTTPException(400, "missing")
    profile_engine.save_generic(company_id, "risk", risk)
    return {"ok": True, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/objectives/save", response_model=SaveOK)
def objectives_save(payload: dict = Body(...)):
    company_id = payload.get("company_id")
    obj = payload.get("objectives")
    if not company_id or obj is None:
        raise HTTPException(400, "missing")
    profile_engine.save_generic(company_id, "objectives", obj)
    return {"ok": True, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/uploads/list")
def uploads_list(payload: UploadListRequest = Body(...)):
    up = profile_engine.list_uploads(payload.company_id)
    return {"uploads": up, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/uploads/upload")
def uploads_upload(payload: UploadUploadRequest = Body(...)):
    item = profile_engine.upload_file(payload.company_id, payload.file_name, payload.category, payload.upload_id)
    return {"ok": True, "upload": item, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/uploads/extract")
def uploads_extract(payload: UploadExtractRequest = Body(...)):
    try:
        item = profile_engine.extract_upload(payload.company_id, payload.id)
    except KeyError:
        raise HTTPException(404, "not found")
    return {"ok": True, "upload": item, "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/completeness/recalc")
def completeness_recalc(payload: CompletenessRecalcRequest = Body(...)):
    comp = profile_engine.recalc_completeness(payload.company_id)
    return {"percent": comp.get("percent"), "missing": comp.get("missing"), "_meta": profile_engine.make_meta()}


@router.post("/api/ai/profile/export")
def profile_export(payload: ExportRequest = Body(...)):
    url = profile_engine.export_profile(payload.company_id, payload.format)
    return {"url": url, "_meta": profile_engine.make_meta()}
