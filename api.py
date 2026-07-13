"""
Regulatory Compliance AI — REST API
===================================

    uvicorn api:app --reload --port 8000
    OpenAPI spec:  http://localhost:8000/docs
    Machine spec:  http://localhost:8000/openapi.json   <-- give this to the React team

WHY THIS FILE EXISTS
--------------------
The Streamlit app has NO API layer. The page scripts call the agent functions directly, in-process.
That is fine for a Streamlit prototype and useless for anything else — you cannot build a React
frontend against a function call.

So porting to Topaz (React) is not a UI rewrite. It is an architectural split:

    Streamlit today                          Topaz tomorrow
    ---------------                          --------------
    pages/1_*.py calls run_regulatory_        React component -> POST /api/monitor/run
    monitor() directly, in-process            -> FastAPI -> the SAME Python function

THE AGENTS DO NOT CHANGE. Not one line. Every graph, every prompt, the provenance verifier and the
domain packs transfer unchanged. This file is the missing seam — the contract that should have
existed all along, and without which the React team is guessing.

Hand the React team `/openapi.json`. That is a machine-readable contract they can generate a typed
client from. It is worth more than any amount of prose in a blueprint.

WHAT THIS IS NOT
----------------
There is no auth, no rate limiting, no persistence and no async job queue here. WF-01 costs 2N+1 LLM
calls and takes minutes — in production it must be a background job with polling or SSE, not a
blocking POST. That is called out at the endpoint. Shipping this as-is behind a public route would be
a mistake, and pretending otherwise would be exactly the overclaim this product exists to prevent.
"""

from __future__ import annotations

import os
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.domains import DOMAIN_PACKS, get_domain, set_active_domain

app = FastAPI(
    title="Regulatory Compliance AI",
    version="0.2.0",
    description=(
        "Seven agents turn dense regulation into testable obligations — each with a citation "
        "verified in CODE against the source text — score their impact, and assemble audit-ready "
        "evidence packages. A human always signs off; this API determines nothing."
    ),
)

# Topaz/React will run on a different origin. Lock this down before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RuntimeError)
def _runtime_error(request, exc: RuntimeError):
    """Never leak a stack trace to a client.

    A misconfigured LLM key was returning a raw 500 with a full traceback. A React team coding
    against that has no idea whether the server is broken or simply unconfigured, and a stack trace
    in an HTTP response is an information leak besides. Fail with a diagnosis, not a dump.
    """
    from fastapi.responses import JSONResponse
    msg = str(exc)
    if "credentials" in msg.lower() or "api_key" in msg.lower():
        return JSONResponse(
            status_code=503,
            content={
                "error": "llm_not_configured",
                "detail": "No LLM credentials configured on the server.",
                "fix": "Set OPENAI_API_KEY (and optionally ANTHROPIC_API_KEY for automatic "
                       "failover) in the environment or a .env file, then restart.",
                "hint": "GET /api/health reports llm_configured — check it before calling any "
                        "agent endpoint.",
            },
        )
    return JSONResponse(status_code=500,
                        content={"error": "agent_failure", "detail": msg[:500]})


# ==========================================================================================
# Shared models
# ==========================================================================================

class ReviewGate(BaseModel):
    """Attached to every agent response. The API is decision support, never a determination."""
    review_status: Literal["PENDING_HUMAN_REVIEW"] = "PENDING_HUMAN_REVIEW"
    disclaimer: str = (
        "AI-generated decision support. Not a compliance determination. Every obligation, gap and "
        "drafted response requires review and sign-off by qualified personnel before use, and no "
        "content may be submitted to a regulator without that sign-off."
    )


class Provenance(BaseModel):
    """Citation health for a run. The React UI MUST surface this — it is the trust story."""
    total: int
    verified: int
    unverified: int
    verified_pct: int


class Obligation(BaseModel):
    obligation_id: str
    description: str
    responsible_entity: str | None = None
    deadline: str | None = Field(None, description="or the literal string 'not stated in source'")
    measurement: str | None = None
    penalty: str | None = None
    category: str | None = None
    source_regulation: str | None = None
    source_body: str | None = None
    source_url: str | None = None
    severity: str | None = None
    # --- the provenance contract. React must render these differently. ---
    source_quote: str | None = Field(None, description="VERBATIM span copied from the regulation")
    source_section: str | None = None
    confidence: Literal["high", "medium", "low"] | None = None
    inferred: bool | None = None
    citation_verified: bool | None = Field(
        None,
        description=(
            "TRUE only if the quote was FOUND in the source text by core provenance verification. "
            "FALSE means the model may have paraphrased or fabricated it. The UI must show these "
            "with a warning badge and MUST NOT present them as equivalent to verified obligations."
        ),
    )


# ==========================================================================================
# Domain packs — the React app needs these to render its selectors
# ==========================================================================================

class Regulator(BaseModel):
    code: str
    name: str
    scope: str


class DomainSummary(BaseModel):
    key: str
    label: str
    vertical: str
    company: str
    company_full: str
    financial_hook: str
    regulators: list[Regulator]
    departments: list[str]
    categories: list[str]
    regulation_count: int
    case_count: int
    evidence_count: int
    audit_types: list[str]


@app.get("/api/domains", response_model=list[DomainSummary], tags=["domains"])
def list_domains():
    """All industry packs. Switching the pack re-targets all 7 agents — no agent code changes."""
    out = []
    for key in DOMAIN_PACKS:
        d = get_domain(key)
        out.append(DomainSummary(
            key=d["key"], label=d["label"], vertical=d["vertical"],
            company=d["company"], company_full=d["company_full"],
            financial_hook=d["financial_hook"],
            regulators=[Regulator(**r) for r in d["regulators"]],
            departments=d["departments"], categories=d["categories"],
            regulation_count=len(d["regulations"]),
            case_count=len(d["cases"]),
            evidence_count=sum(len(v) for v in d["evidence"].values()),
            audit_types=list(d["audit_types"]),
        ))
    return out


class RegulationSummary(BaseModel):
    index: int
    source: str
    title: str
    published_date: str
    url: str | None = None
    text: str


@app.get("/api/domains/{domain}/regulations", response_model=list[RegulationSummary],
         tags=["domains"])
def list_regulations(domain: str):
    if domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{domain}'")
    return [RegulationSummary(index=i, **{k: v for k, v in r.items()
                                          if k in {"source", "title", "published_date", "url", "text"}})
            for i, r in enumerate(get_domain(domain)["regulations"])]


@app.get("/api/domains/{domain}/audit-types", tags=["domains"])
def list_audit_types(domain: str) -> dict[str, list[dict]]:
    """Audit type -> the obligations that audit tests. Drives the Audit Prep screen."""
    if domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{domain}'")
    return get_domain(domain)["audit_types"]


@app.get("/api/domains/{domain}/cases", tags=["domains"])
def list_cases(domain: str) -> list[dict]:
    if domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{domain}'")
    return get_domain(domain)["cases"]


# ==========================================================================================
# WF-01 — Regulatory Monitor
# ==========================================================================================

class MonitorRequest(BaseModel):
    domain: str = "energy_utilities"
    source_filter: str = Field("all", description="Regulator code (e.g. 'OEIS', 'CPUC') or 'all'")


class Alert(BaseModel):
    alert_id: str
    source: str
    title: str
    severity: Literal["critical", "high", "medium", "low"] | str
    change_type: str | None = None
    summary: str | None = None
    key_deadlines: list[str] = []
    penalty_info: str | None = None
    obligation_count: int = 0
    obligations: list[Obligation] = []
    affected_departments: list[str] = []
    impact_mappings: list[dict[str, Any]] = []


class MonitorResponse(ReviewGate):
    alerts: list[Alert]
    obligations: list[Obligation]
    provenance: Provenance
    regulations_scanned: int


@app.post("/api/monitor/run", response_model=MonitorResponse, tags=["WF-01 Regulatory Monitor"])
def run_monitor(req: MonitorRequest):
    """Fetch → Classify → Extract (+VERIFY CITATION) → Map to departments → Alert.

    ⚠️ COST + LATENCY: this is `2N + 1` LLM calls for N regulations. For the full Energy pack that
    is 23 calls and takes minutes. **In production this MUST be a background job** with polling or
    SSE — a blocking POST will time out behind any real gateway. It is synchronous here so the
    contract is legible; do not ship it this way.
    """
    if req.domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{req.domain}'")
    set_active_domain(req.domain)

    from agents.regulatory_monitor.graph import run_regulatory_monitor
    result = run_regulatory_monitor(source_filter=req.source_filter)

    obligations = result.get("extracted_obligations", []) or []
    verified = sum(1 for o in obligations if o.get("citation_verified"))
    total = len(obligations)

    return MonitorResponse(
        alerts=[Alert(**a) for a in result.get("alerts", [])],
        obligations=[Obligation(**o) for o in obligations],
        provenance=Provenance(
            total=total, verified=verified, unverified=total - verified,
            verified_pct=round(100 * verified / total) if total else 0,
        ),
        regulations_scanned=len(result.get("raw_updates", []) or []),
    )


# ==========================================================================================
# WF-02 — Obligation Impact
# ==========================================================================================

class ImpactRequest(BaseModel):
    domain: str = "energy_utilities"
    regulation_index: int | None = Field(
        None, description="Index into GET /api/domains/{domain}/regulations")
    regulation_text: str | None = Field(None, description="Or paste raw regulatory text")
    regulation_source: str = "Unknown"


class ImpactResponse(ReviewGate):
    atomic_obligations: list[dict[str, Any]]
    cross_references: list[dict[str, Any]]
    impact_scores: list[dict[str, Any]]
    report: dict[str, Any] = Field(
        ..., description="executive_summary, cost range, earliest_deadline, key_risks, "
                         "recommended_actions[], board_attention_items[], regulatory_strategy")


@app.post("/api/impact/run", response_model=ImpactResponse, tags=["WF-02 Obligation Impact"])
def run_impact(req: ImpactRequest):
    """Decompose → Cross-reference → Score (cost/ops/timeline/penalty) → Executive report.

    Exactly 4 LLM calls. Predictable and cheap.
    """
    if req.domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{req.domain}'")
    set_active_domain(req.domain)

    text, source = req.regulation_text, req.regulation_source
    if req.regulation_index is not None:
        regs = get_domain(req.domain)["regulations"]
        if not 0 <= req.regulation_index < len(regs):
            raise HTTPException(400, f"regulation_index out of range (0..{len(regs) - 1})")
        r = regs[req.regulation_index]
        text, source = r["text"], f"{r['source']}: {r['title']}"
    if not text:
        raise HTTPException(400, "supply regulation_index or regulation_text")

    from agents.obligation_impact.graph import run_obligation_impact
    result = run_obligation_impact(regulation_text=text, regulation_source=source)

    return ImpactResponse(
        atomic_obligations=result.get("atomic_obligations", []),
        cross_references=result.get("cross_references", []),
        impact_scores=result.get("impact_scores", []),
        report=result.get("report", {}),
    )


# ==========================================================================================
# WF-03 — Audit Preparation  (THE FLAGSHIP)
# ==========================================================================================

class AuditRequest(BaseModel):
    domain: str = "energy_utilities"
    audit_scope: str = Field(..., description="An audit type from GET .../audit-types")
    regulations: list[str] = Field(default_factory=list, description="Regulations in scope")


class SupervisorReview(BaseModel):
    overall_readiness: str | None = None
    readiness_score: int | float | None = Field(None, description="0-100. The headline number.")
    executive_summary: str | None = None
    critical_items: list[str] = []
    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendations: list[str] = []
    timeline_assessment: str | None = None


class AuditResponse(ReviewGate):
    audit_plan: dict[str, Any]
    evidence_inventory: list[dict[str, Any]]
    gap_analysis: list[dict[str, Any]] = Field(
        ..., description="THE PRODUCT. Each gap: severity, audit_risk, remediation{action,owner,"
                         "effort,deadline}, interim_mitigation")
    draft_responses: list[dict[str, Any]]
    supervisor_review: SupervisorReview


@app.post("/api/audit/run", response_model=AuditResponse, tags=["WF-03 Audit Prep (FLAGSHIP)"])
def run_audit(req: AuditRequest):
    """Supervisor plans → Evidence Collector → Gap Analyzer → Response Drafter → Supervisor reviews.

    Produces the traceable chain a regulator asks for when it says "show me":

        regulation → obligation → evidence doc → gap → owner + date → drafted response

    terminating in a 0–100 readiness score. 5 LLM calls.
    """
    if req.domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{req.domain}'")
    set_active_domain(req.domain)

    audit_types = get_domain(req.domain)["audit_types"]
    if req.audit_scope not in audit_types:
        raise HTTPException(400, f"unknown audit_scope. Known: {list(audit_types)}")

    from agents.audit_prep.graph import run_audit_preparation
    result = run_audit_preparation(
        audit_scope=req.audit_scope,
        regulations=req.regulations,
        obligations=audit_types[req.audit_scope],
    )

    return AuditResponse(
        audit_plan=result.get("audit_plan", {}),
        evidence_inventory=result.get("evidence_inventory", []),
        gap_analysis=result.get("gap_analysis", []),
        draft_responses=result.get("draft_responses", []),
        supervisor_review=SupervisorReview(**(result.get("supervisor_review", {}) or {})),
    )


# ==========================================================================================
# WF-04 — Case Analytics
# ==========================================================================================

class CaseRequest(BaseModel):
    domain: str = "energy_utilities"
    query: str
    analysis_type: Literal["precedent", "trend", "risk", "summary"] = "precedent"


@app.post("/api/cases/analyze", tags=["WF-04 Case Analytics"])
def analyze_cases(req: CaseRequest) -> dict[str, Any]:
    """RAG over the enforcement corpus. 1 LLM call."""
    if req.domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{req.domain}'")
    set_active_domain(req.domain)

    from agents.case_analytics.chain import run_case_analytics, load_sample_cases
    load_sample_cases()
    return run_case_analytics(query=req.query, analysis_type=req.analysis_type)


@app.get("/api/cases/stats", tags=["WF-04 Case Analytics"])
def case_stats(domain: str = "energy_utilities") -> dict[str, Any]:
    """Aggregate stats + penalty timeline. NO LLM CALL — the dashboard renders free."""
    if domain not in DOMAIN_PACKS:
        raise HTTPException(404, f"unknown domain '{domain}'")
    set_active_domain(domain)
    from agents.case_analytics.chain import get_case_stats
    d = get_domain(domain)
    return {"stats": get_case_stats(), "penalty_timeline": d["penalty_timeline"]}


# ==========================================================================================
# Health
# ==========================================================================================

@app.get("/api/health", tags=["ops"])
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "llm_configured": bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")),
        "domains": list(DOMAIN_PACKS),
        "data_provenance": (
            "All corpora are ILLUSTRATIVE — realistic in structure, not verified records of real "
            "regulations or enforcement actions. Replace before any client engagement."
        ),
    }
