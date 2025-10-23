from fastapi import APIRouter, HTTPException
from ..schemas import (
    AssetsFullRequest, AssetsFullResponse, AssetsSearchRequest, AssetsSearchResponse,
    ImportRequest, ImportResponse, ReplaceVsRepairRequest, ReplaceVsRepairResponse,
    WorkOrderCreateRequest, WorkOrderCreateResponse, MaintenanceScheduleRequest,
    MaintenanceScheduleResponse, TelemetryIngestRequest, TelemetryIngestResponse,
    DocumentExtractRequest, DocumentExtractResponse
)
from ..services.assets_engine import full_overview, search_registry, create_work_order, schedule_maintenance, replace_vs_repair_calc, import_rows, ingest_telemetry
from ..utils_demo import is_demo, meta
from ..demo_seed import DEMO_ASSETS_FULL

router = APIRouter()


@router.post("/api/ai/assets/full", response_model=AssetsFullResponse)
async def assets_full(req: AssetsFullRequest):
    # Demo mode check
    if is_demo(req.company_id):
        response = DEMO_ASSETS_FULL.copy()
        return meta(response)
    
    # Non-demo: existing logic
    res = full_overview(req.model_dump())
    return res


@router.post("/api/ai/assets/search", response_model=AssetsSearchResponse)
async def assets_search(req: AssetsSearchRequest):
    out = search_registry(req.company_id, req.query, req.filters)
    return out


@router.post("/api/ai/assets/workorders/create", response_model=WorkOrderCreateResponse)
async def assets_create_wo(req: WorkOrderCreateRequest):
    wo = create_work_order(req.company_id, req.asset_id, req.priority, req.summary, req.sla_hours)
    from ..services.assets_engine import meta_top
    return {"wo_id": wo.get("wo_id"), "status": wo.get("status"), "_meta": meta_top()}


@router.post("/api/ai/assets/maintenance/schedule", response_model=MaintenanceScheduleResponse)
async def assets_schedule(req: MaintenanceScheduleRequest):
    ok = schedule_maintenance(req.company_id, req.asset_id, req.plan)
    from ..services.assets_engine import meta_top
    return {"ok": ok, "_meta": meta_top()}


@router.post("/api/ai/assets/replace-vs-repair", response_model=ReplaceVsRepairResponse)
async def assets_replace_vs_repair(req: ReplaceVsRepairRequest):
    data = replace_vs_repair_calc(req.model_dump(), {})
    return data


@router.post("/api/ai/assets/import", response_model=ImportResponse)
async def assets_import(req: ImportRequest):
    out = import_rows(req.company_id, req.rows)
    return out


@router.post("/api/ai/assets/telemetry/ingest", response_model=TelemetryIngestResponse)
async def assets_telemetry(req: TelemetryIngestRequest):
    result = ingest_telemetry(req.company_id, req.asset_id, req.samples)
    return result


@router.post("/api/ai/assets/documents/extract-dates", response_model=DocumentExtractResponse)
async def assets_extract_dates(req: DocumentExtractRequest):
    from ..services.assets_engine import extract_document_dates
    result = extract_document_dates(req.company_id, req.docs or [])
    return result
