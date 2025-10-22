from fastapi import APIRouter, HTTPException
from ..schemas import DebtFullRequest, DebtFullResponse, DebtScenarioRequest, DebtScenarioResponse, DebtAskRequest, ConnectorRequest, ConnectorResponse, DebtAccount
from ..services.debt_engine import build_full, simulate_scenario, load_demo
import json

router = APIRouter()


@router.post("/api/ai/debt/full", response_model=DebtFullResponse)
async def debt_full(req: DebtFullRequest):
    if req.company_id == "demo":
        res = build_full(req.company_id, range=req.range, include_market_rates=req.include_market_rates, include_credit_score=req.include_credit_score)
        return res
    else:
        raise HTTPException(status_code=400, detail="Only demo supported in this implementation")


@router.post("/api/ai/debt/optimize")
async def debt_optimize(payload: dict):
    # minimal: return options from build_full optimization
    company_id = payload.get("company_id","demo")
    data = build_full(company_id)
    return {"options": data.get("optimization",[]), "_meta": data.get("_meta")}


@router.post("/api/ai/debt/simulate", response_model=DebtScenarioResponse)
async def debt_simulate(req: DebtScenarioRequest):
    res = simulate_scenario(req.company_id, req.scenario, req.inputs)
    return res


@router.post("/api/ai/debt/ask")
async def debt_ask(req: DebtAskRequest):
    # naive answer using optimize results
    data = build_full(req.company_id)
    opt = data.get("optimization",[])[:2]
    answer = "Review refinance options for high-rate loans and prioritize paying high-rate cards."
    actions = []
    if opt:
        actions.append({"type":"simulate","payload":{"scenario":"refinance","inputs":{"account_id": opt[0].get("id","" )}}})
    return {"answer": answer, "links": [{"type":"section","ref":"optimization"}], "actions": actions, "_meta": data.get("_meta")}


@router.post("/api/ai/debt/integrations/connect", response_model=ConnectorResponse)
async def debt_connect(req: ConnectorRequest):
    # demo: persist a flag to demo data file (do not write tokens)
    # just echo connected
    meta = {"source":"lightsignal.orchestrator","confidence":"low","latency_ms":1, "provenance": {"baseline_source":"manual","sources":[req.provider],"notes":["Connector stubbed for demo; no tokens stored."],"confidence":"low","used_priors": False, "prior_weight":0.0}}
    return {"ok": True, "status": "connected", "_meta": meta}


@router.post("/api/ai/debt/accounts/add")
async def debt_accounts_add(payload: dict):
    company_id = payload.get("company_id","demo")
    account = payload.get("account")
    if company_id != "demo":
        raise HTTPException(status_code=400, detail="Only demo company supported")
    # append to demo file
    path = "data/demo/debt.json"
    try:
        with open(path, "r+") as f:
            data = json.load(f)
            accounts = data.get("accounts", [])
            accounts.append(account)
            data["accounts"] = accounts
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    except Exception:
        raise HTTPException(status_code=500, detail="could not persist demo account")
    meta = {"source":"lightsignal.orchestrator","confidence":"low","latency_ms":2, "provenance": {"baseline_source":"manual","sources":["Manual"],"notes":["Account added to demo store"],"confidence":"low","used_priors": False, "prior_weight":0.0}}
    return {"ok": True, "account_id": account.get("account_id"), "_meta": meta}


@router.post("/api/ai/debt/alerts/refresh")
async def debt_alerts_refresh(payload: dict):
    company_id = payload.get("company_id","demo")
    data = load_demo(company_id)
    res = build_full(company_id)
    return {"alerts": res.get("risk", {}).get("alerts", []), "_meta": res.get("_meta")}


@router.post("/api/ai/debt/export")
async def debt_export(payload: dict):
    # return signed URL stub
    fmt = payload.get("format","pdf")
    variant = payload.get("variant","summary")
    url = f"signed://{payload.get('company_id','demo')}-debt-{variant}.{fmt}"
    meta = {"source":"lightsignal.orchestrator","confidence":"low","latency_ms":1}
    return {"url": url, "_meta": meta}


@router.post("/api/ai/debt/credit/score")
async def debt_credit_score(payload: dict):
    company_id = payload.get("company_id","demo")
    data = load_demo(company_id)
    return {"score": data.get("credit_score", {}).get("score", 60), "factors": data.get("credit_score", {}).get("factors", []), "_meta": {"source":"lightsignal.orchestrator"}}
