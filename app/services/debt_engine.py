from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import math, json

DATA_PATH = "data/demo/debt.json"


def load_demo(company_id: str) -> Dict[str, Any]:
    if company_id != "demo":
        return {"accounts": [], "market_rate_cache": {}, "credit_score": {}}
    try:
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"accounts": [], "market_rate_cache": {}, "credit_score": {}}


def weighted_avg_rate(accounts: List[Dict[str, Any]]) -> float:
    total_bal = 0.0
    numer = 0.0
    for a in accounts:
        bal = max(0.0, float(a.get("balance", 0.0)))
        rate = float(a.get("rate_pct", 0.0))
        if bal > 0:
            total_bal += bal
            numer += bal * rate
    return (numer / total_bal) if total_bal > 0 else 0.0


def monthly_payments_sum(accounts: List[Dict[str, Any]]) -> float:
    s = 0.0
    for a in accounts:
        s += float(a.get("monthly_payment") or 0.0)
    return s


def total_revolving(accounts: List[Dict[str, Any]]) -> Dict[str, float]:
    bal = 0.0
    limit = 0.0
    for a in accounts:
        if a.get("type") == "credit_card" or a.get("type") == "loc":
            bal += float(a.get("balance", 0.0))
            limit += float(a.get("limit") or 0.0)
    return {"balance": bal, "limit": limit}


def compute_dti(total_monthly_debt: float, monthly_net_income: float) -> Optional[float]:
    if monthly_net_income <= 0:
        return None
    return total_monthly_debt / monthly_net_income


def compute_dscr(operating_cash_flow: float, total_debt_service: float) -> Optional[float]:
    if total_debt_service <= 0:
        return None
    return operating_cash_flow / total_debt_service


def amortization_schedule(balance: float, rate_pct: float, term_months: int) -> List[Dict[str, Any]]:
    # monthly rate
    r = rate_pct / 100.0 / 12.0
    n = term_months
    if n <= 0 or balance <= 0:
        return []
    if r == 0:
        monthly = balance / n
    else:
        monthly = r * balance / (1 - (1 + r) ** (-n))
    schedule = []
    bal = balance
    for i in range(1, n + 1):
        interest = bal * r
        principal = min(bal, monthly - interest) if monthly > interest else 0.0
        bal -= principal
        schedule.append({"month": i, "payment": monthly, "principal": principal, "interest": interest, "balance": max(0.0, bal)})
        if bal <= 0:
            break
    return schedule


def biweekly_effect(balance: float, rate_pct: float, monthly_payment: float) -> Dict[str, Any]:
    # approximate: 26 half-payments = 13 full payments/year vs 12 => 1 extra payment/year
    if monthly_payment <= 0:
        return {"months_earlier": 0, "interest_saved": 0.0}
    annual_payment = monthly_payment * 12
    extra = monthly_payment  # approx one extra monthly per year
    # crude estimate: interest_saved ~ extra * years_remaining * avg_rate
    # need term estimate via amortization if possible
    return {"months_earlier": 6, "interest_saved": round(balance * (rate_pct / 100.0) * 0.05, 2)}


def refinance_savings(balance: float, old_rate: float, new_rate: float, term_months: int, fee_pct: float = 0.0) -> Dict[str, Any]:
    # compare interest paid over remaining term
    old_schedule = amortization_schedule(balance, old_rate, term_months)
    new_schedule = amortization_schedule(balance, new_rate, term_months)
    old_interest = sum([p.get("interest", 0.0) for p in old_schedule])
    new_interest = sum([p.get("interest", 0.0) for p in new_schedule])
    fees = balance * fee_pct / 100.0
    return {"interest_saved": round(old_interest - new_interest - fees, 2), "fees": fees}


def avalanche_vs_snowball(accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Simplified comparision: compute total interest for two payoff orders assuming min payments
    # For demo, assume payments equal monthly_payment and any extra goes to one strategy
    # We'll compute interest using current monthly payments until balances zero
    def simulate(order):
        accs = [{**a, "bal": float(a.get("balance", 0.0)), "rate": float(a.get("rate_pct", 0.0)), "min": float(a.get("monthly_payment") or 0.0)} for a in accounts]
        total_interest = 0.0
        months = 0
        while any(a["bal"] > 0.5 for a in accs) and months < 600:
            months += 1
            # pay min payments
            for a in accs:
                if a["bal"] <= 0: continue
                r = a["rate"]/100.0/12.0
                interest = a["bal"]*r
                pay = min(a["min"], a["bal"]+interest)
                principal = pay - interest
                a["bal"] = max(0.0, a["bal"] - principal)
                total_interest += interest
            # no extra allocation in this simplified model
        return {"interest": total_interest, "months": months}

    # avalanche: sort by rate desc
    by_avalanche = sorted(accounts, key=lambda a: float(a.get("rate_pct", 0.0)), reverse=True)
    by_snowball = sorted(accounts, key=lambda a: float(a.get("balance", 0.0)))
    r_av = simulate(by_avalanche)
    r_sn = simulate(by_snowball)
    return {"avalanche": r_av, "snowball": r_sn, "delta_interest": round(r_sn["interest"] - r_av["interest"], 2)}


def risk_alerts(accounts: List[Dict[str, Any]], market_rates: Dict[str, float], dscr: Optional[float], utilization_pct: Optional[float]) -> List[Dict[str, Any]]:
    alerts = []
    for a in accounts:
        balloon = a.get("balloon_due_months")
        if balloon is not None:
            if balloon <= 3:
                alerts.append({"id": f"balloon_{a['account_id']}", "title": "Balloon due soon", "severity": "critical", "description": f"{a['name']} has balloon in {balloon} months"})
            elif balloon <= 9:
                alerts.append({"id": f"balloon_{a['account_id']}", "title": "Balloon due", "severity": "warning", "description": f"{a['name']} has balloon in {balloon} months"})
        if a.get("variable_rate"):
            alerts.append({"id": f"reset_{a['account_id']}", "title": "Variable rate reset approaching", "severity": "warning", "description": f"{a['name']} is variable rate"})
        # market variance
        mrate = market_rates.get("term_refi", 0)
        if a.get("rate_pct", 0) > mrate + 5:
            alerts.append({"id": f"rate_{a['account_id']}", "title": "High rate compared to market", "severity": "info", "description": f"{a['name']} rate {a.get('rate_pct')}% vs market {mrate}%"})
    if dscr is not None:
        if dscr < 1.0:
            alerts.append({"id": "dscr_low", "title": "DSCR below 1.0", "severity": "critical", "description": "Debt service exceeds operating cash flow"})
        elif dscr < 1.25:
            alerts.append({"id": "dscr_warn", "title": "DSCR below 1.25", "severity": "warning", "description": "Consider deleveraging"})
    if utilization_pct is not None and utilization_pct >= 0.5:
        alerts.append({"id": "util_high", "title": "High utilization", "severity": "warning", "description": f"Utilization at {utilization_pct:.0%}"})
    return alerts


def build_full(company_id: str, range: str = "30d", include_market_rates: bool = True, include_credit_score: bool = True) -> Dict[str, Any]:
    data = load_demo(company_id)
    accounts = data.get("accounts", [])
    market = data.get("market_rate_cache", {}) if include_market_rates else {}
    credit = data.get("credit_score") if include_credit_score else None

    weighted = weighted_avg_rate(accounts)
    total_bal = sum([float(a.get("balance", 0.0)) for a in accounts])
    monthly = monthly_payments_sum(accounts)
    # demo financials - fabricate operating cash flow and net income
    operating_cash_flow = 5000.0
    monthly_net_income = 8000.0
    dti = compute_dti(monthly, monthly_net_income)
    dscr = compute_dscr(operating_cash_flow, monthly)
    rev = total_revolving(accounts)
    utilization_pct = (rev["balance"]/rev["limit"]) if rev.get("limit") and rev["limit"]>0 else None

    kpis = {"weighted_avg_rate_pct": round(weighted,2), "total_balance": total_bal, "monthly_payments": monthly, "dti": dti, "dscr": dscr, "utilization_pct": utilization_pct}

    charts = {"balance_trend": [], "payment_breakdown": []}
    opt = []
    # simple optimization example: refi equipment loan at term_refi
    for a in accounts:
        if a.get("type") in ["equipment_loan", "vehicle_loan"]:
            new_rate = market.get("term_refi", a.get("rate_pct"))
            term = a.get("term_months") or 36
            res = refinance_savings(float(a.get("balance",0)), float(a.get("rate_pct",0)), float(new_rate), int(term), fee_pct=0.5)
            opt.append({"id": f"refi_{a['account_id']}", "type": "refinance", "description": f"Refinance {a['name']} to {new_rate}%", "est_savings_annual": res["interest_saved"], "est_fee": res["fees"], "confidence": "medium"})

    scenarios = []
    # add baseline avalanche/snowball
    avs = avalanche_vs_snowball(accounts)
    scenarios.append({"name":"avalanche_vs_snowball","results":avs})

    alerts = risk_alerts(accounts, market, dscr, utilization_pct)

    meta = {"source":"lightsignal.orchestrator","confidence":"low","latency_ms":10,
            "provenance": {"baseline_source":"quickbooks_demo","sources":["QuickBooks","Plaid","Manual"],"notes":["Amortization computed locally; market rates cached."],"confidence":"medium","used_priors": True, "prior_weight":0.4}}

    return {"kpis": kpis, "accounts": accounts, "charts": charts, "utilization": {"revolving": rev}, "optimization": opt, "scenarios": scenarios, "risk": {"alerts": alerts}, "credit_score": credit, "recommendations": [], "export": {"pdf": True}, "_meta": meta}


def simulate_scenario(company_id: str, scenario: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    data = load_demo(company_id)
    accounts = data.get("accounts", [])
    # baseline monthly
    baseline_monthly = monthly_payments_sum(accounts)

    # default return
    per_account = []
    interest_saved = 0.0
    months_earlier = 0
    new_monthly = baseline_monthly
    new_payoff_date = None

    if scenario == "extra_payment":
        acct = inputs.get("account_id")
        extra = float(inputs.get("extra_monthly", 0.0))
        new_monthly = baseline_monthly + extra
        interest_saved = extra * 12 * 0.08  # rough
        months_earlier = 6
        per_account = [{"account_id": acct, "interest_saved": round(interest_saved,2)}]
    elif scenario == "biweekly":
        acct = inputs.get("account_id")
        a = next((x for x in accounts if x["account_id"]==acct), None)
        if a:
            res = biweekly_effect(float(a.get("balance",0)), float(a.get("rate_pct",0)), float(a.get("monthly_payment",0)))
            interest_saved = res["interest_saved"]
            months_earlier = res["months_earlier"]
            per_account = [{"account_id": acct, "interest_saved": interest_saved}]
            new_monthly = baseline_monthly
    elif scenario == "refinance":
        acct = inputs.get("account_id")
        new_rate = float(inputs.get("new_rate_pct", 0.0))
        a = next((x for x in accounts if x["account_id"]==acct), None)
        if a:
            term = a.get("term_months") or 36
            res = refinance_savings(float(a.get("balance",0)), float(a.get("rate_pct",0)), new_rate, int(term))
            interest_saved = res["interest_saved"]
            months_earlier = 0
            per_account = [{"account_id": acct, "interest_saved": interest_saved}]
    elif scenario == "balance_shift":
        shift = inputs.get("balance_shift", {})
        amt = float(shift.get("amount",0))
        frm = shift.get("from")
        to = shift.get("to")
        # simple: moving balance to lower rate saves interest
        f = next((x for x in accounts if x["account_id"]==frm), None)
        t = next((x for x in accounts if x["account_id"]==to), None)
        if f and t:
            delta_rate = float(f.get("rate_pct",0)) - float(t.get("rate_pct",0))
            interest_saved = amt * delta_rate/100.0 * 1.0
            per_account = [{"account_id": frm, "interest_saved": round(interest_saved,2)}]
    elif scenario == "rate_change":
        acct = inputs.get("account_id")
        new_rate = float(inputs.get("new_rate_pct",0.0))
        a = next((x for x in accounts if x["account_id"]==acct), None)
        if a:
            term = a.get("term_months") or 36
            res = refinance_savings(float(a.get("balance",0)), float(a.get("rate_pct",0)), new_rate, int(term))
            interest_saved = res["interest_saved"]
            per_account = [{"account_id": acct, "interest_saved": interest_saved}]

    meta = {"source":"lightsignal.orchestrator","confidence":"low","latency_ms":5, "provenance": {"baseline_source":"quickbooks_demo","sources":["Manual"],"notes":["Scenario simulated locally"],"confidence":"low","used_priors": False, "prior_weight":0.0}}

    return {"new_monthly": round(new_monthly,2), "interest_saved": round(interest_saved,2), "months_earlier": int(months_earlier), "new_payoff_date": new_payoff_date, "per_account_impacts": per_account, "_meta": meta}

