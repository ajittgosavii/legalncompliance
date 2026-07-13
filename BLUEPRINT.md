# Regulatory Compliance AI Platform — Solution Blueprint

> **Purpose of this document**: a complete, self-contained architectural and functional description of the
> `legalncompliance` application, structured for import into **Infosys Topaz Fabric** as an agentic solution
> asset. It describes the agent registry, orchestration graphs, prompts, data contracts, tools, models,
> guardrails, and the prototype→production delta.
>
> Source repository: `https://github.com/ajittgosavii/legalncompliance`
> Blueprint generated: 2026-07-11 · Against commit `d85d9f0`

---

## 1. Solution Metadata

```yaml
solution:
  id: regulatory-compliance-ai
  name: Regulatory Compliance AI Platform
  version: 0.1.0-prototype
  maturity: proof-of-concept / demo-ready
  domain: Legal, Risk & Compliance (LRC)
  sub_domain: Regulatory Change Management, Audit Readiness, Enforcement Analytics
  primary_industry: Energy & Utilities (electric + gas)
  transferable_to: [Financial Services, Healthcare/Life Sciences, Telecom, Pharma, any regulated industry]
  pattern: Multi-agent orchestration (LangGraph) + RAG
  interface: Web application (Streamlit multipage)
  language: Python 3.11+
  license: unspecified (internal demo asset)
  data_classification: synthetic / illustrative only — no real client or PII data
```

### One-line description

An agentic AI platform that continuously watches regulators, decomposes new rules into concrete testable
obligations, scores their business impact, assembles audit-ready evidence packages, and mines enforcement
history for precedent — moving compliance teams from *reacting* to regulatory change to *getting ahead* of it.

---

## 2. Business Problem & Value

### The problem

Regulated enterprises (the reference implementation models a large US electric + gas utility) must track a
continuous stream of rulemakings, orders, resolutions and emergency regulations across many federal and state
bodies. Today this is manual: analysts read hundreds of pages of dense legal text, hand-extract obligations
into spreadsheets, chase document owners for audit evidence, and rely on institutional memory for
enforcement precedent. The result is late detection, missed deadlines, evidence gaps discovered *during*
an audit, and avoidable penalty exposure.

### What the platform does

| # | Capability | Mechanism |
|---|-----------|-----------|
| 1 | Continuously monitors regulatory bodies for change | Agentic pipeline over regulator sources |
| 2 | Classifies each change by type and severity | LLM classification |
| 3 | Extracts specific, testable obligations (who / what / by when / how measured / penalty) | LLM extraction |
| 4 | Maps obligations to internal departments and assesses operational impact | LLM mapping against a department model |
| 5 | Scores multi-dimensional impact (cost, operations, timeline, penalty risk) | LLM scoring against an enterprise-context profile |
| 6 | Detects conflicts and overlaps with the existing obligation estate | LLM cross-reference against a known-obligations register |
| 7 | Assembles audit-ready evidence packages and identifies gaps | Supervisor + 3 specialist agents |
| 8 | Drafts professional, submission-grade regulatory responses | LLM drafting with evidence citations |
| 9 | Mines historical enforcement cases for precedent, trend and risk | RAG over a case knowledge base |

### Target personas

- Compliance and regulatory-affairs analysts and managers
- Legal counsel and risk management
- Internal audit and controls
- Operations leaders in regulated business units
- C-suite / board (consumers of the executive impact reports and readiness scores)

### Value hypothesis

- Reduces hours of manual rule-reading to minutes per regulation.
- Surfaces new obligations and deadlines early enough to plan, not react.
- Eliminates "audit-day surprises" by finding evidence gaps in advance, with remediation owners and dates.
- Grounds penalty-exposure conversations in actual enforcement precedent rather than intuition.

---

## 3. Reference Domain Model

The prototype is instantiated for a large US energy utility. **All entity names have been de-identified** —
the enterprise is referred to throughout the prompts and sample data as *"the Company"*. Any Topaz Fabric
import should treat this as a **configurable domain pack**, not as hard-coded logic.

### 3.1 Regulatory bodies monitored (7 active + 1 referenced)

| Code | Body | Scope |
|------|------|-------|
| CPUC | California Public Utilities Commission | Primary state regulator — wildfire, rates, privacy, EV |
| FERC | Federal Energy Regulatory Commission | Interstate transmission, planning, incentives |
| NERC | North American Electric Reliability Corp. (incl. NERC CIP) | Grid reliability, OT cybersecurity |
| CARB | California Air Resources Board | Emissions, cap-and-trade |
| EPA | Environmental Protection Agency | Air toxics (MATS/NESHAP), environmental |
| PHMSA | Pipeline & Hazardous Materials Safety Admin. | Gas pipeline safety, LDAR |
| Cal-OSHA | California Division of Occupational Safety & Health | Worker safety, heat/smoke exposure |
| CEC | California Energy Commission | Energy policy (appears in case history only) |

### 3.2 Department model (obligation routing targets)

Electric Operations · Gas Operations · Wildfire Safety · IT/Cybersecurity ·
Environmental & Sustainability · Regulatory Affairs · Legal & Compliance ·
Customer Operations · Generation · Corporate

### 3.3 Obligation taxonomy

- **Monitor categories**: `wildfire | grid_reliability | cybersecurity | environmental | reporting | safety | ai_governance | financial`
- **Impact categories**: `operational | reporting | financial | technical | governance`
- **Change types**: `rule_change | guidance | notice | enforcement | proposed_rule`
- **Severity**: `critical | high | medium | low`

### 3.4 Existing-obligation register (used for conflict/overlap detection)

CPUC GO 95 (overhead line construction) · CPUC GO 165 (inspection cycles) · CPUC Wildfire Mitigation Plan ·
FERC Form 714 · NERC CIP-002…CIP-014 · CARB MRR · Cal-OSHA Title 8 · CPUC Rule 20 · PHMSA 49 CFR 192

---

## 4. Solution Architecture

### 4.1 Layered view

```
┌──────────────────────────── PRESENTATION ─────────────────────────────────┐
│  Streamlit multipage UI (app.py + 4 pages)                                │
│  Dashboard │ Regulatory Monitor │ Obligation Impact │ Audit Prep │ Cases  │
│  Plotly visualisations · custom CSS design system (core/styles.py)        │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────────────┐
│                        ORCHESTRATION LAYER                                │
│  LangGraph StateGraph state machines + one LCEL-style RAG chain           │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐ ┌────────────────┐  │
│  │ WF-01       │ │ WF-02        │ │ WF-03          │ │ WF-04          │  │
│  │ Monitor     │ │ Impact       │ │ Audit Prep     │ │ Case Analytics │  │
│  │ 5 nodes     │ │ 4 nodes      │ │ Supervisor + 3 │ │ RAG chain      │  │
│  └─────────────┘ └──────────────┘ └────────────────┘ └────────────────┘  │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────────────┐
│                          AGENT / PROMPT LAYER                             │
│  7 specialised agent personas, prompts centralised in core/prompts.py     │
│  All inherit a shared SYSTEM_CONTEXT (domain grounding)                   │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────────────┐
│                       MODEL & RETRIEVAL LAYER                             │
│  core/llm.py  — GPT-4o primary, Claude Sonnet runtime fallback            │
│  core/vectorstore.py — in-memory TF-IDF retrieval (4 collections)         │
│  core/embeddings.py — pluggable (Voyage legal / OpenAI) — inactive        │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────────────┐
│                            DATA LAYER                                     │
│  SQLite (core/db.py) — 5-table schema, PostgreSQL-ready                   │
│  Embedded synthetic corpora: 11 regulations · 29 cases · 48 evidence docs │
│  ingestion/ — scraper + parser packages (stubs, not implemented)          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Repository map

| Path | Role |
|------|------|
| `app.py` | Dashboard, navigation, KPI row, getting-started guide, architecture tab |
| `pages/1_Regulatory_Monitor.py` | UI for WF-01 |
| `pages/2_Obligation_Impact.py` | UI for WF-02 |
| `pages/3_Audit_Prep.py` | UI for WF-03 |
| `pages/4_Case_Analytics.py` | UI for WF-04 (dashboard + AI search + case browser) |
| `agents/regulatory_monitor/graph.py` | WF-01 LangGraph state machine (5 nodes) |
| `agents/regulatory_monitor/tools.py` | 4 LangChain `@tool` functions + 11 sample regulations |
| `agents/obligation_impact/graph.py` | WF-02 LangGraph state machine (4 nodes) |
| `agents/audit_prep/graph.py` | WF-03 supervisor multi-agent graph (5 nodes) + 48-doc evidence repo |
| `agents/case_analytics/chain.py` | WF-04 RAG chain + 29 cases + 29-row penalty timeline |
| `core/llm.py` | Model factory, tiering, provider failover |
| `core/prompts.py` | All 7 agent system prompts + shared `SYSTEM_CONTEXT` |
| `core/vectorstore.py` | In-memory TF-IDF retriever, 4 named collections |
| `core/embeddings.py` | Pluggable embedding provider (currently returns `None`) |
| `core/db.py` | SQLite persistence, 5 tables |
| `core/styles.py` | Design system: hero, KPI, cards, pipeline viz, badges |
| `ingestion/scrapers/`, `ingestion/parsers/` | **Empty stub packages** — production ingestion goes here |

---

## 5. Agent Registry

Seven distinct agent personas, each with a dedicated system prompt in `core/prompts.py`. All prompts are
composed as `SYSTEM_CONTEXT + role_instructions`, which is the single point of domain grounding.

| ID | Agent | Workflow | Responsibility | Output contract |
|----|-------|----------|----------------|-----------------|
| AG-01 | **Regulatory Monitor Agent** | WF-01 (nodes: classify, extract, map) | Analyse regulatory text; classify change type & severity; extract obligations; map to departments | JSON object / array (see §7.1–7.3) |
| AG-02 | **Obligation Impact Agent** | WF-02 (all 4 nodes) | Decompose into atomic obligations; cross-reference existing estate; score 4 impact dimensions; write executive report | JSON array + report object (§7.4–7.6) |
| AG-03 | **Audit Supervisor Agent** | WF-03 (plan, review) | Plan the audit-prep approach; review package completeness; issue readiness score | JSON plan + review object (§7.7, §7.10) |
| AG-04 | **Evidence Collector Agent** | WF-03 (collect_evidence) | Map available evidence to each obligation; rate relevance & sufficiency; flag missing evidence | JSON array (§7.8) |
| AG-05 | **Gap Analyzer Agent** | WF-03 (analyze_gaps) | Identify compliance gaps; assess severity & audit risk; propose remediation with owner/effort/deadline | JSON array (§7.9) |
| AG-06 | **Response Drafter Agent** | WF-03 (draft_responses) | Draft submission-grade regulatory response narratives with evidence citations and corrective actions | JSON array |
| AG-07 | **Case Analytics Agent** | WF-04 | RAG over enforcement history; precedent / trend / risk / summary analysis | JSON analysis object (§7.11) |

### Shared system context (verbatim intent)

> "You are an AI compliance analyst specialised in U.S. energy utility regulations. You work for the Company,
> one of the largest utilities in the United States." — followed by the 8-regulator list and 7 stated
> compliance priorities (wildfire safety, grid reliability, rate cases, environmental/emissions,
> cybersecurity, pipeline safety, customer data privacy).

**Topaz note:** this shared context block is the single lever for re-targeting the solution to another
industry or client. Replace `SYSTEM_CONTEXT`, the department list in WF-01's `map_to_departments`, the
existing-obligation register in WF-02's `cross_reference`, and the enterprise profile in WF-02's
`score_impacts` — the graphs themselves are domain-agnostic.

---

## 6. Workflow Specifications

### WF-01 — Regulatory Change Monitor

**Pattern**: linear LangGraph `StateGraph`, 5 nodes, no branching, no cycles.
**Trigger**: user clicks "Run Monitor Agent" with an optional regulator filter.
**Entry**: `fetch` → **Exit**: `END`

```
fetch ──▶ classify ──▶ extract ──▶ map ──▶ notify ──▶ END
```

| Node | Type | Function | LLM calls |
|------|------|----------|-----------|
| `fetch` | Deterministic | Load regulatory updates from source, apply regulator filter | 0 |
| `classify` | LLM | Per update: change_type, severity, summary, key_deadlines, penalty_info | **1 per regulation** (N) |
| `extract` | LLM | Per update: array of atomic obligations with entity/deadline/measurement/penalty/category | **1 per regulation** (N) |
| `map` | LLM | Single batched call: map every obligation to primary + supporting departments, effort, capex flag, timeline risk | **1** |
| `notify` | Deterministic | Join classifications + obligations + mappings into alerts; sort by severity | 0 |

**State schema** (`MonitorState`):
```python
{ source_filter: str, raw_updates: list[dict], classified_updates: list[dict],
  extracted_obligations: list[dict], impact_mappings: list[dict], alerts: list[dict],
  current_step: str, error: str | None }
```

**Cost profile**: `2N + 1` LLM calls where N = number of regulations in scope (11 unfiltered → 23 calls).
This is the dominant cost driver in the solution and the first target for optimisation (batching,
map-reduce, or a cheaper model tier on `classify`).

---

### WF-02 — Obligation Impact Analysis

**Pattern**: linear LangGraph `StateGraph`, 4 nodes.
**Trigger**: user selects one regulation and clicks "Run Impact Analysis".

```
decompose ──▶ cross_ref ──▶ score ──▶ report ──▶ END
```

| Node | Function | LLM calls |
|------|----------|-----------|
| `decompose` | Break the regulation into atomic, independently testable, assignable obligations | 1 |
| `cross_ref` | Detect conflicts / overlaps / synergies against the existing-obligation register; propose resolution | 1 |
| `score` | Score each obligation on **cost** (score + $ range + capex/opex), **operational** (score + affected processes + workforce), **timeline risk** (score + feasibility + critical path), **penalty risk** (score + max penalty + enforcement likelihood); assign overall priority and recommended approach | 1 |
| `report` | Executive report: summary, obligation counts, total cost range, earliest deadline, key risks, recommended actions (with owner/priority/deadline), board attention items, regulatory strategy | 1 |

**State schema** (`ImpactState`):
```python
{ regulation_text: str, regulation_source: str, atomic_obligations: list[dict],
  cross_references: list[dict], impact_scores: list[dict], report: dict, current_step: str }
```

**Enterprise profile injected into scoring** (configurable): ~$24B annual revenue, ~28,000 employees,
active wildfire liabilities, under enhanced regulatory oversight, ~$7–8B annual capital programme.

**Cost profile**: exactly 4 LLM calls per regulation. Predictable and cheap.

---

### WF-03 — Audit Analysis & Preparation (multi-agent, supervisor pattern)

**Pattern**: LangGraph supervisor pattern — a Supervisor bookends three specialist agents.
**Trigger**: user selects an audit type + regulations in scope, clicks "Run Audit Prep Agent".

```
plan (Supervisor) ──▶ collect_evidence (Evidence Collector) ──▶ analyze_gaps (Gap Analyzer)
                  ──▶ draft_responses (Response Drafter) ──▶ supervisor_review (Supervisor) ──▶ END
```

| Node | Agent | Function |
|------|-------|----------|
| `plan` | AG-03 Supervisor | Produce audit areas, evidence-needed-per-area, priority order, effort estimate, key risks |
| `collect_evidence` | AG-04 Evidence Collector | For each obligation: matched evidence docs with relevance (`direct/supporting/partial`) and sufficiency (`sufficient/partial/insufficient`); evidence_status; missing evidence; recommended sources |
| `analyze_gaps` | AG-05 Gap Analyzer | Gaps typed as `missing_evidence / outdated_evidence / partial_compliance / process_gap / documentation_gap`, each with severity, audit risk, remediation (action/owner/effort/deadline), interim mitigation |
| `draft_responses` | AG-06 Response Drafter | Per audit area: 2–3 paragraph submission-grade narrative, evidence citations, compliance status (`full/substantial/partial/non_compliant`), corrective actions, risk mitigation |
| `supervisor_review` | AG-03 Supervisor | Overall readiness (`ready/mostly_ready/significant_gaps/not_ready`), **readiness score 0–100**, executive summary for audit committee, critical items, strengths, weaknesses, prioritised recommendations, timeline assessment |

**State schema** (`AuditState`):
```python
{ audit_scope: str, regulations: list[str], obligations: list[dict], evidence_inventory: list[dict],
  gap_analysis: list[dict], draft_responses: list[dict], supervisor_review: dict,
  final_package: dict, current_step: str, iteration: int }
```

**Final artefact** (`final_package`): audit_scope + evidence_inventory + gap_analysis + draft_responses +
supervisor_review — a complete, exportable audit-readiness package with a traceable chain from
**regulation → obligation → evidence → gap → response**.

**Cost profile**: 5 LLM calls per audit run (all batched, obligation count is passed in-prompt).

> ⚠️ **Known defect to fix on industrialisation**: the `plan` node invokes the Supervisor LLM but **discards
> the response** — it returns state unchanged rather than writing the plan into state. The plan therefore never
> reaches the downstream specialists. See §11.

> ⚠️ The `iteration` field exists in state but no cyclic/critique edge is wired. The supervisor pattern is
> currently **single-pass**; a supervisor→specialist feedback loop is the natural next iteration.

---

### WF-04 — Case Analytics (Generative AI + RAG)

**Pattern**: retrieval-augmented single-shot chain (not a LangGraph state machine).
**Trigger**: user asks a natural-language question and picks an analysis type.

```
query ──▶ TF-IDF retrieve (top-k=5 over case collection) ──▶ aggregate stats
      ──▶ compose prompt (retrieved cases + FULL case DB + stats) ──▶ LLM ──▶ JSON analysis
```

**Analysis types** (switches the instruction block):
- `precedent` — find the most relevant precedent cases and how they resolved
- `trend` — enforcement trends over time; are penalties rising; which violation types are growing
- `risk` — compliance risk assessment and penalty exposure by area
- `summary` — comprehensive summary, patterns, strategic implications

**Also renders** (no LLM required): interactive Plotly dashboard over the case corpus and penalty timeline,
plus a filterable case browser. This is the recommended zero-cost entry point for a demo.

**Cost profile**: 1 LLM call — but with a **large prompt**: it injects the retrieved cases *and* the entire
serialised case database *and* the aggregate statistics. Retrieval is effectively decorative at current
corpus size; at production scale the full-DB injection must be removed and retrieval must actually gate
what enters the context.

---

## 7. Data Contracts

All agents are prompted to return JSON and every call site parses defensively by slicing between the first
`{`/`[` and last `}`/`]`, with a hard-coded fallback object on parse failure. **These are prompt-level
contracts, not enforced schemas** — see §11 for the recommended move to structured/tool-call output.

### 7.1 Classification (WF-01 `classify`)
```json
{ "change_type": "rule_change|guidance|notice|enforcement|proposed_rule",
  "severity": "critical|high|medium|low",
  "summary": "2-3 sentence summary of the material change",
  "key_deadlines": ["deadline strings"],
  "penalty_info": "penalty details if mentioned" }
```

### 7.2 Extracted obligation (WF-01 `extract`)
```json
{ "obligation_id": "CPUC-WMP-001", "description": "...", "responsible_entity": "...",
  "deadline": "...", "measurement": "...", "penalty": "...",
  "category": "wildfire|grid_reliability|cybersecurity|environmental|reporting|safety|ai_governance|financial",
  "source_regulation": "<injected>", "source_body": "<injected>", "severity": "<injected>" }
```

### 7.3 Department mapping (WF-01 `map`)
```json
{ "obligation_id": "...", "primary_department": "...", "supporting_departments": ["..."],
  "operational_impact": "...", "estimated_effort": "low|medium|high|very_high",
  "requires_capex": true, "requires_new_systems": false,
  "timeline_risk": "on_track|tight|at_risk|critical" }
```

### 7.4 Alert (WF-01 `notify`, deterministic)
```json
{ "alert_id": "8-char uuid", "source": "CPUC", "title": "...", "severity": "...",
  "change_type": "...", "summary": "...", "key_deadlines": [], "penalty_info": "...",
  "obligation_count": 5, "obligations": [], "affected_departments": [], "impact_mappings": [] }
```

### 7.5 Atomic obligation (WF-02 `decompose`)
```json
{ "ob_id": "...", "parent_section": "...", "obligation": "...", "obligated_entity": "...",
  "condition": "...", "deadline": "...", "measurement_criteria": "...",
  "category": "operational|reporting|financial|technical|governance" }
```

### 7.6 Impact score (WF-02 `score`)
```json
{ "ob_id": "...",
  "cost_impact":        { "score": 1-10, "estimated_range_low": 0, "estimated_range_high": 0,
                          "cost_type": "capex|opex|both", "rationale": "..." },
  "operational_impact": { "score": 1-10, "affected_processes": [], "workforce_impact": "...", "rationale": "..." },
  "timeline_risk":      { "score": 1-10, "feasibility": "achievable|challenging|at_risk|unlikely",
                          "critical_path_items": [], "rationale": "..." },
  "penalty_risk":       { "score": 1-10, "max_penalty": 0,
                          "enforcement_likelihood": "low|medium|high", "rationale": "..." },
  "overall_priority": "critical|high|medium|low", "recommended_approach": "..." }
```

### 7.7 Executive impact report (WF-02 `report`)
```json
{ "executive_summary": "...", "total_obligations": 0, "critical_obligations": 0,
  "estimated_total_cost_low": 0, "estimated_total_cost_high": 0, "earliest_deadline": "...",
  "key_risks": [], "recommended_actions": [ { "action": "...", "owner": "...",
    "priority": "immediate|short_term|medium_term", "deadline": "..." } ],
  "board_attention_items": [], "regulatory_strategy": "..." }
```

### 7.8 Evidence mapping (WF-03 `collect_evidence`)
```json
{ "obligation_id": "...", "obligation_summary": "...",
  "evidence_found": [ { "doc_id": "...", "relevance": "direct|supporting|partial",
                        "sufficiency": "sufficient|partial|insufficient", "notes": "..." } ],
  "evidence_status": "complete|partial|missing",
  "missing_evidence": [], "recommended_sources": [] }
```

### 7.9 Gap (WF-03 `analyze_gaps`)
```json
{ "gap_id": "...", "obligation_id": "...",
  "gap_type": "missing_evidence|outdated_evidence|partial_compliance|process_gap|documentation_gap",
  "description": "...", "severity": "critical|high|medium|low", "audit_risk": "...",
  "remediation": { "action": "...", "owner": "...", "effort": "...", "deadline": "..." },
  "interim_mitigation": "..." }
```

### 7.10 Supervisor review (WF-03 `supervisor_review`)
```json
{ "overall_readiness": "ready|mostly_ready|significant_gaps|not_ready", "readiness_score": 0,
  "executive_summary": "...", "critical_items": [], "strengths": [], "weaknesses": [],
  "recommendations": [], "timeline_assessment": "..." }
```

### 7.11 Case analysis (WF-04)
```json
{ "analysis_type": "precedent|trend|risk|summary", "query": "...", "executive_summary": "...",
  "relevant_cases": [ { "case_number": "...", "relevance": "...", "key_takeaway": "..." } ],
  "patterns_identified": [],
  "risk_assessment": { "overall_risk": "low|medium|high|critical", "highest_risk_areas": [],
                       "estimated_penalty_exposure": "..." },
  "recommendations": [],
  "data_visualizations": { "penalties_by_year": {}, "cases_by_type": {}, "cases_by_regulator": {} },
  "stats": "<deterministic aggregate stats appended post-LLM>" }
```

---

## 8. Tools & Skills Catalogue

Four LangChain `@tool`-decorated functions exist in `agents/regulatory_monitor/tools.py`. **Note**: the
current WF-01 graph calls its data sources directly rather than binding these tools to a tool-calling agent —
they are registered and available but not yet wired into an agentic tool loop.

| Tool | Signature | Purpose | Status |
|------|-----------|---------|--------|
| `fetch_regulatory_updates` | `(source: str = "all") -> str` | List updates from monitored sources, filtered by regulator; returns previews | Defined; graph bypasses it |
| `get_regulatory_detail` | `(title: str) -> str` | Fetch the full text of one regulatory update by (partial) title | Defined; unused |
| `search_existing_obligations` | `(query: str) -> str` | Semantic search of the existing-obligation vector collection | Defined; unused |
| `store_regulatory_change` | `(change_data: str) -> str` | Persist a classified change to SQLite **and** index it in the vector store | Defined; unused — the only wired path to `core/db.py` |

**Topaz mapping**: these are the natural seams for Fabric tool/skill registration. In a Fabric deployment
they become governed, permissioned tools with their own audit trail, and WF-01 becomes a true
tool-calling agent rather than a hard-coded pipeline.

---

## 9. Model & Inference Configuration

`core/llm.py` implements a provider-abstracted model factory with **runtime failover**.

```yaml
models:
  primary:
    provider: OpenAI
    model_id: gpt-4o
    temperature: 0
    max_tokens: 4096
    rationale: cost-effective default for all agent nodes
  mini:
    provider: OpenAI
    model_id: gpt-4o-mini
    rationale: lightweight classification/summary tier (defined, not yet used by any node)
  advanced:
    provider: Anthropic
    model_id: claude-sonnet-4-6
    rationale: higher-accuracy tier for dense regulatory text
  opus:
    provider: Anthropic
    model_id: claude-opus-4-8
    max_tokens: 8192
    rationale: heavy-reasoning tier

failover:
  mechanism: LangChain `.with_fallbacks([...])`
  behaviour: >
    If OPENAI_API_KEY is present, GPT-4o is primary. If ANTHROPIC_API_KEY is ALSO present, every call
    automatically fails over to Claude Sonnet on any OpenAI exception (401 revoked key, 429 rate limit,
    provider outage). If only one provider key is present, that provider is used directly. With neither,
    a RuntimeError is raised at call time with a configuration message.
  tiering_api: core.llm.get_llm(tier="primary|mini|advanced|opus")
```

**Every agent node currently calls `get_openai_primary()`** — the `mini` / `advanced` / `opus` tiers are
built but unassigned. Tier assignment per node is a straightforward, high-leverage cost/quality lever
(e.g. `classify` → mini; `score` and `report` → advanced/opus).

**Determinism**: `temperature=0` throughout.

---

## 10. Knowledge Assets & Retrieval

### 10.1 Retrieval

`core/vectorstore.py` implements an **in-memory TF-IDF cosine-similarity retriever** — not a true embedding
vector store. It was deliberately chosen for Streamlit Cloud compatibility (ChromaDB/protobuf failure on
Python 3.14). It defines a LangChain-`Document`-compatible interface (`SimpleDocument`) so it can be swapped
for a real vector store with no call-site changes.

| Collection | Constant | Contents |
|-----------|----------|----------|
| `pwe_regulations` | `COLLECTION_REGULATIONS` | Indexed regulatory changes |
| `pwe_obligations` | `COLLECTION_OBLIGATIONS` | Obligation register |
| `pwe_cases` | `COLLECTION_CASES` | Enforcement case corpus (the only one actively populated, by `load_sample_cases()`) |
| `pwe_audit_evidence` | `COLLECTION_AUDIT` | Audit evidence documents |

`core/embeddings.py` already contains a **pluggable provider chain**: Voyage AI `voyage-law-2`
(legal-domain embeddings) → OpenAI `text-embedding-3-small` → `None` (TF-IDF prototype mode). Setting
`VOYAGE_API_KEY` is the intended production path for legal-domain semantic search.

### 10.2 Synthetic corpora shipped with the prototype

Ground-truth counts, measured directly from the source (note: several UI labels are stale — see §11):

| Asset | Location | Actual count | UI claims |
|-------|----------|--------------|-----------|
| Regulatory updates | `agents/regulatory_monitor/tools.py` | **11** (CPUC 4, FERC 2, NERC 1, CARB 1, EPA 1, PHMSA 1, Cal-OSHA 1) | 12 |
| Enforcement cases | `agents/case_analytics/chain.py` | **29** (CPUC 15, NERC/FERC 4, CARB 3, Cal-OSHA 3, PHMSA 2, FERC 1, CEC 1) | 28 |
| Total penalty value in corpus | derived | **$17.47B** | $19.8B |
| Case types | derived | enforcement 18, audit 3, investigation 2, application 2, rate_case 2, rulemaking 2 | — |
| Penalty timeline rows | `agents/case_analytics/chain.py` | **29** (2012–2025, by regulator) | — |
| Audit evidence documents | `agents/audit_prep/graph.py` | **48** across 8 categories | 45+ |
| Evidence categories | derived | wildfire 11, cybersecurity 9, environmental 6, pipeline_safety 6, worker_safety 5, grid_reliability 4, data_privacy 4, ai_governance 3 | 8 |

Each evidence document carries: `doc_id`, `title`, `type` (plan/report/tracker/procedure/inventory/policy/
audit/log/assessment/review/filing/registry/study/analysis), `status` (`current | draft | partial |
needs_update`), `location` (SharePoint path), `last_updated`, `owner` (department). The
`needs_update` / `partial` statuses are the seeded "gaps" the Gap Analyzer is meant to discover.

### 10.3 Structured persistence

`core/db.py` — SQLite, PostgreSQL-ready DDL. **Schema is defined but effectively unwired**: no graph node
persists to it, and `init_db()` is never called from application code.

| Table | Columns of note |
|-------|-----------------|
| `regulatory_changes` | source, title, summary, change_type, severity, url, published/detected date, affected_departments, obligations_json, status, reviewed_by, review_notes |
| `obligations` | regulation_id (FK), obligation_text, category, owner_department, deadline, compliance_status, impact_score, cost_estimate, last_assessed |
| `audit_items` | audit_name, audit_type, regulation_ref, obligation_id (FK), evidence_status, evidence_path, gap_description, remediation_plan, due_date |
| `cases` | case_number (unique), case_title, regulator, case_type, status, filing/resolution date, penalty_amount, summary, key_findings, precedent_tags |
| `agent_runs` | agent_name, run_id, status, input/output summary, **tokens_used, cost_estimate**, started_at, completed_at, **trace_json** |

The `agent_runs` table is a ready-made **observability / FinOps hook** — `log_agent_run()` and
`complete_agent_run()` exist but are never called. Wiring these is the cheapest path to per-run cost,
latency and trace capture.

---

## 11. Prototype → Production Delta (honest gap list)

This is the most important section for a Topaz Fabric import. The solution is a **well-architected
demo**, not a production system. The following must be closed.

### 11.1 Functional defects

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| D1 | The Audit Supervisor's `plan` node calls the LLM and **discards the result** — it returns state unchanged. The audit plan never reaches the specialist agents. | `agents/audit_prep/graph.py:plan_audit` | One wasted LLM call per run; the supervisor's planning is decorative |
| D2 | `iteration` exists in `AuditState` but no cycle/critique edge is wired — the "supervisor pattern" is single-pass | `agents/audit_prep/graph.py` | No self-correction loop |
| D3 | JSON parsing is brace-slicing with a silent fallback object; a malformed response degrades to `[]` or a "PARSE-ERR" record with no alert | all 4 workflows | Silent quality loss |
| D4 | WF-04 injects the **entire case database** into the prompt alongside RAG results — retrieval does not actually gate context | `agents/case_analytics/chain.py:run_case_analytics` | Will not scale past a few dozen cases |
| D5 | UI KPI labels are stale vs. the actual corpora (12 vs 11 regulations, 28 vs 29 cases, $19.8B vs $17.47B) | `app.py` | Cosmetic, but a credibility risk in a client demo |
| D6 | Residual de-identification artefacts in sample text, e.g. "the Company Company", "the Company shall deploy" | `agents/regulatory_monitor/tools.py` | Cosmetic; clean before client-facing use |
| D7 | Vector-store collection names still carry the legacy `pwe_` prefix | `core/vectorstore.py` | Cosmetic |

### 11.2 Architectural gaps

| # | Gap | Required for production |
|---|-----|------------------------|
| G1 | **No live ingestion.** `ingestion/scrapers/` and `ingestion/parsers/` are empty stubs. All 11 regulations are hard-coded Python dicts. | Real connectors to CPUC/FERC/NERC/CARB/EPA/PHMSA/Cal-OSHA publication feeds; PDF/HTML parsers; change-detection and de-duplication |
| G2 | **No real semantic retrieval.** TF-IDF keyword overlap, not embeddings. | Swap to a managed vector store + `voyage-law-2` (legal-domain) or equivalent embeddings — the seam already exists in `core/embeddings.py` |
| G3 | **No persistence of agent output.** Every run is ephemeral in Streamlit session state. | Wire `core/db.py`; migrate SQLite → PostgreSQL; persist obligations, gaps, alerts with lifecycle status |
| G4 | **No observability.** No tracing, token accounting, latency or cost capture. | Wire `log_agent_run`/`complete_agent_run`; add LangSmith/OTel tracing; the `agent_runs.trace_json` column is already there |
| G5 | **No authentication, authorisation or multi-tenancy.** | SSO, RBAC by department, tenant isolation of corpora |
| G6 | **No human-in-the-loop.** The system produces submission-grade regulatory responses with no review/approval gate. | Mandatory review + approval workflow with sign-off audit trail before any output is treated as authoritative |
| G7 | **No evaluation harness.** No golden set, no regression tests, no accuracy measurement on obligation extraction. | Ground-truth obligation set per regulation; precision/recall on extraction; LLM-as-judge on report quality |
| G8 | **No structured-output enforcement.** | Move from prompt-instructed JSON to tool-calling / structured output with schema validation and retry |
| G9 | **Unbounded LLM cost on WF-01** (`2N+1` calls). | Tier assignment, batching, caching, incremental processing of only *new* regulations |
| G10 | **No source citation back to primary text.** Obligations are extracted but not anchored to a span/section in the source document. | Span-level provenance — essential for legal defensibility |

### 11.3 Responsible AI / guardrail gaps

The solution currently has **no explicit guardrail layer**. For a legal & compliance use case this is the
highest-priority addition:

- **Hallucinated obligations or penalties** are the core risk — a fabricated deadline or a wrong penalty
  figure entering a compliance register is a material harm. Requires: span-level citation, confidence
  scoring, and mandatory human review before an obligation is committed.
- **Advice framing** — outputs read as legal/regulatory conclusions. Requires clear "AI-generated, requires
  qualified review" disclaiming and a professional-review gate.
- **Prompt injection via ingested regulatory documents** — once live scraping is enabled, untrusted document
  text flows straight into system-adjacent prompts. Requires input sanitisation and instruction/data separation.
- **PII / confidential evidence** — the evidence repository points at internal document stores. Requires
  access-scoped retrieval so agents can only see evidence the requesting user is entitled to.
- **Auditability** — every AI-influenced compliance decision needs a reproducible trace (prompt, model
  version, retrieved context, output, reviewer). The `agent_runs` schema anticipates this; nothing writes to it.

---

## 12. Deployment & Operations

### Current (prototype)

```yaml
runtime: Streamlit Cloud
entrypoint: app.py
python: ">=3.11"
state: in-process (session state + module-level in-memory vector store)
persistence: SQLite at ./data/pwe_compliance.db (ephemeral on Streamlit Cloud)
secrets: Streamlit Cloud Secrets -> promoted to os.environ at page load
scaling: single process, no horizontal scale, no queue, no background jobs
```

**Configuration** (`.env.example` / Streamlit Secrets):

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENAI_API_KEY` | Yes (or Anthropic) | Primary LLM |
| `ANTHROPIC_API_KEY` | Optional | Runtime failover + advanced/opus tiers |
| `VOYAGE_API_KEY` | Optional | Legal-domain embeddings (`voyage-law-2`) |
| `DATABASE_PATH` | Optional | SQLite path (default `./data/pwe_compliance.db`) |
| `CHROMA_PERSIST_DIR` | Optional | Legacy — ChromaDB not currently used |
| `OLLAMA_BASE_URL` | Optional | Legacy — local LLM not currently used |

### Dependencies

`streamlit` · `langchain` / `langchain-core` / `langchain-community` · `langgraph` ·
`openai` + `langchain-openai` · `anthropic` + `langchain-anthropic` · `plotly` · `pandas` · `python-dotenv`

### Target (Topaz Fabric)

| Concern | Prototype | Target |
|---------|-----------|--------|
| Orchestration | LangGraph in-process | Fabric-governed agent orchestration with per-agent policy |
| Agents | 7 prompt personas | 7 registered Fabric agents with declared I/O contracts |
| Tools | 4 `@tool` functions, unwired | Governed, permissioned Fabric tools with audit trail |
| Models | Hard-coded GPT-4o + Claude failover | Fabric model gateway; tier per node; policy-driven routing |
| Retrieval | In-memory TF-IDF | Managed vector store + legal-domain embeddings |
| Persistence | SQLite | PostgreSQL / enterprise data platform |
| Ingestion | Hard-coded samples | Scheduled connectors + change detection |
| UI | Streamlit | Fabric UX surface or embedded enterprise portal |
| Observability | None | Fabric tracing, token/cost accounting, eval dashboards |
| Guardrails | None | Fabric guardrail policies + mandatory HITL gate |

---

## 13. Industrialisation Roadmap

**Phase 0 — Demo hardening (days)**
Fix D1 (supervisor plan discarded), D5/D6/D7 (stale labels, de-identification artefacts). Assign model tiers
per node. Wire `agent_runs` logging for cost/latency visibility.

**Phase 1 — Make it real (weeks)**
Live ingestion connectors for 2–3 priority regulators with PDF/HTML parsing and change detection. Replace
TF-IDF with real embeddings + a managed vector store. Wire `core/db.py` (PostgreSQL) so obligations, gaps
and alerts persist with lifecycle status.

**Phase 2 — Make it trustworthy (weeks)**
Structured/tool-call output with schema validation. Span-level provenance from every obligation back to the
source text. Human-in-the-loop review and approval gate before any obligation or response is committed.
Guardrail layer. Evaluation harness with a golden obligation set.

**Phase 3 — Make it enterprise (weeks)**
SSO + RBAC + multi-tenancy. Access-scoped evidence retrieval. Full tracing and FinOps. Supervisor critique
loop (close D2). Horizontal scale + async job execution for the `2N+1` monitor workload.

**Phase 4 — Make it a product**
Domain packs: swap `SYSTEM_CONTEXT`, the department model, the obligation register and the enterprise profile
to re-target the identical graphs at Financial Services (Basel/MiFID/SEC), Healthcare (HIPAA/FDA), or Telecom.
The orchestration is already domain-agnostic — this is the reuse thesis.

---

## 14. Topaz Fabric Import Summary

```yaml
asset_type: agentic_solution
agents: 7          # AG-01..AG-07, see §5
workflows: 4       # WF-01 (5-node), WF-02 (4-node), WF-03 (supervisor + 3 specialists), WF-04 (RAG chain)
tools: 4           # defined; require wiring — see §8
knowledge_collections: 4
data_contracts: 11 # see §7
models: 2 providers / 4 tiers, with runtime failover
ui_surfaces: 5     # dashboard + 4 modules
loc: ~4,200 Python
external_dependencies: [OpenAI, Anthropic, (optional) Voyage AI]
pii: none (all data synthetic)
production_readiness: prototype — 7 known defects, 10 architectural gaps, no guardrail layer (§11)
reuse_vector: domain-agnostic graphs + swappable domain pack (§13 Phase 4)
```

### The core reusable IP

1. **The obligation-extraction contract** (§7.2, §7.5) — a well-shaped schema for turning dense legal prose
   into atomic, assignable, testable, measurable obligations. This is the heart of the asset.
2. **The four-dimension impact scoring model** (§7.6) — cost / operational / timeline / penalty risk, each
   with a score, quantified range, and rationale.
3. **The supervisor audit-prep pattern** (§6, WF-03) — a traceable chain from regulation → obligation →
   evidence → gap → response, terminating in a 0–100 readiness score for the audit committee.
4. **The provider-failover model factory** (§9) — clean, tiered, resilient; directly reusable.

Everything else — the regulators, the departments, the sample corpora — is a **domain pack** to be replaced
per client.

---

## Appendix A — Business Case: Pacific Gas and Electric Company (PG&E)

> **Status of this appendix**: a qualification and positioning case, not a validated ROI model. Every
> quantified figure below is an **assumption placeholder** that must be replaced with client-validated
> baselines before it is shown to PG&E. Public-record facts are marked as such and should still be
> re-verified against current filings — regulatory structure in California changes frequently.

### A.1 Why PG&E is the natural first client

This solution was evidently **built against PG&E and then de-identified** — the enterprise is referred to
throughout as "the Company," but the domain pack is PG&E's:

| Evidence in the codebase | PG&E fact it encodes |
|--------------------------|----------------------|
| Regulator set: CPUC, FERC, NERC, CARB, EPA, PHMSA, Cal-OSHA, CEC | PG&E's exact regulatory perimeter (electric + gas, state + federal) |
| Enterprise profile: ~$24B revenue, ~28,000 employees, ~$7–8B annual capex | PG&E's approximate scale |
| "Active wildfire liabilities"; "under enhanced CPUC oversight since 2019" | Ch. 11 (Jan 2019 → Jul 2020); CPUC Enhanced Oversight and Enforcement Process |
| Penalty timeline spikes: $1.6B (2017), $2.14B (2019) | San Bruno CPUC penalty; wildfire-era penalties |
| "10,000 Mile Undergrounding Program Tracker" in the evidence repo | PG&E's announced undergrounding commitment |
| CPUC Rule 20, GO 95, GO 165, WMP, Tier 2/3 HFTD, PSPS | PG&E's day-to-day compliance vocabulary |
| Residual string-replacement artefact: "the Company Company" | Incomplete de-identification of the original name |

**Implication**: this is not a generic asset being retrofitted to a prospect. It is a PG&E-shaped asset that
has been anonymised. That is an advantage in a qualification conversation — the domain fluency is real — but
it also means the demo must be **re-identified deliberately and cleaned** (see A.5), not shown as-is.

### A.2 The strongest value thesis: compliance evidence → safety certification → cost recovery

Most compliance-automation pitches lead with analyst hours saved. For PG&E that is the *weakest* argument
available, and leading with it undersells the asset. The stronger chain is financial:

Under California's post-2019 wildfire framework (AB 1054), an electrical corporation's **safety
certification** — and its ability to demonstrate reasonable conduct and compliance with its Wildfire
Mitigation Plan — materially affects the presumption applied to cost recovery and its access to the
wildfire fund. Separately, PG&E operates under sustained regulatory scrutiny in which *disallowance* of
claimed costs, not just penalties, is a live and recurring financial event.

The consequence: for PG&E, **the ability to evidence compliance on demand is not an administrative
nicety — it is an input to cost recovery.** An evidence gap is not merely an audit embarrassment; it is a
disallowance risk and, at the extreme, a safety-certification risk.

This platform's Module 3 (Audit Analysis & Preparation) is aimed exactly at that: it produces a traceable
chain from **regulation → obligation → evidence document → gap → remediation owner/date → drafted response**,
terminating in a 0–100 readiness score. That chain is the artefact a utility needs when a regulator asks
"show me."

> ⚠️ **Verify before use**: the appendix above describes the *shape* of the AB 1054 / safety-certification
> mechanism. The precise current legal effect, thresholds and prudency presumptions must be confirmed with
> qualified counsel and against current CPUC/OEIS decisions before any version of this argument is put in
> front of the client. Do not put a specific dollar claim on this chain without that verification.

### A.3 Value drivers, ranked

| # | Driver | Module | Why it lands at PG&E | Evidence needed to make the claim credible |
|---|--------|--------|----------------------|--------------------------------------------|
| 1 | **Audit readiness / evidence-gap elimination** | M3 | PG&E's binding constraint is *proving* compliance, repeatedly, under scrutiny. The costly failure is a gap found by an auditor rather than by PG&E. | Run M3 against one real, upcoming PG&E audit and compare gaps found vs. gaps the team already knew about. Any gap the tool finds that the team did not have is the entire business case. |
| 2 | **Obligation decomposition at scale** | M1 + M2 | A single CPUC decision contains a dozen separately-testable duties with distinct deadlines, measurement methods and penalties, today extracted by hand into spreadsheets. | Precision/recall against a human-extracted golden set for 5–10 real decisions. This is measurable and should be measured. |
| 3 | **Enforcement precedent grounding** | M4 | Penalty-exposure and board risk conversations currently rest on institutional memory. | Load the real public case record (CPUC/FERC/NERC/PHMSA/Cal-OSHA), not the synthetic corpus. |
| 4 | **Early warning on regulatory change** | M1 | Value is real but *lowest* differentiated — PG&E's regulatory affairs function already tracks CPUC dockets closely and commercial RegTech feeds exist. | Do not lead with this. Position it as the intake for drivers 1–2, not as the headline. |
| 5 | **Cross-obligation conflict detection** | M2 | Genuinely hard and genuinely valuable — new CPUC/OEIS requirements routinely collide with GO 95/165 and existing WMP commitments. | Needs the real existing-obligation register to be loaded. Highest ceiling, highest data-dependency. |

### A.4 ROI framework (placeholders — DO NOT quote these to the client)

The honest position is that **this asset does not yet have an ROI model** — it has an ROI *shape*. The
framework below is the structure to fill in with PG&E-validated baselines during discovery.

```
Value = (A) analyst time reallocated
      + (B) audit findings avoided
      + (C) disallowance / penalty exposure reduced      <-- the dominant term, and the hardest to substantiate
      + (D) faster obligation-to-owner assignment (deadline misses avoided)
      - (E) LLM inference cost
      - (F) build + integration + review-workflow cost
      - (G) ongoing human review burden (this does NOT go to zero — see A.6)

Discovery questions that determine every term:
  A: How many FTEs currently read rule text and maintain obligation registers? What fraction of their time?
  B: How many audit findings / data requests per year? What is the internal cost of responding to one?
  C: What is the historical cost of disallowances and penalties attributable to evidence or process gaps
     — as opposed to underlying operational failures? (These are very different things. Be rigorous here.)
  D: How many obligation deadlines were missed or made late in the last 24 months, and why?
  E: WF-01 costs 2N+1 LLM calls per run — trivially quantifiable once N and cadence are known.
```

**A caution on term (C).** It is tempting to anchor the business case to PG&E's historical penalty figures —
they are large, public, and dramatic. Resist this. Those penalties were overwhelmingly consequences of
*operational* failures (pipeline integrity, vegetation management, equipment maintenance), not of failures to
*document* compliance. This platform does not prevent a wildfire. Claiming a share of a $1.6B or $2B penalty
as addressable value would be intellectually dishonest and, in front of a sophisticated PG&E audience, would
destroy credibility instantly. The defensible version of (C) is narrow and specific: **cost disallowances and
findings that turned on inadequate documentation, evidence, or demonstrated process** — a much smaller,
much more honest number, and one PG&E's regulatory affairs team can actually help size.

### A.5 What must be fixed before a PG&E conversation

Blocking, in priority order:

1. **The WMP filing path is wrong.** The codebase routes Wildfire Mitigation Plans to CPUC. Since 2021, WMPs
   are submitted to and reviewed by the **Office of Energy Infrastructure Safety (OEIS)** — formerly the
   CPUC's Wildfire Safety Division — with CPUC ratifying, and OEIS issuing the safety certification. Getting
   this wrong in front of PG&E's regulatory affairs team is an immediate credibility loss on the single topic
   they care most about. **OEIS is also entirely absent from the monitored-regulator list and must be added.**
2. **Fix the Audit Supervisor bug (D1).** The `plan` node calls the LLM and discards the result. The
   flagship module's supervisor does not actually supervise.
3. **Complete the de-identification cleanup, then deliberately re-identify.** "the Company Company" and
   `pwe_` collection prefixes cannot appear in a client-facing build.
4. **Correct the stale KPI labels (D5)** — the dashboard claims 12 regulations / 28 cases / $19.8B against
   actual corpora of 11 / 29 / $17.47B. A client who counts will find this, and it invites the question of
   what else is decorative.
5. **Replace the synthetic case corpus with the real public enforcement record.** The precedent-analysis
   claim is worthless on invented cases, and PG&E will recognise its own history instantly.
6. **Add source provenance.** An obligation with no citation back to a span in the source decision cannot
   enter a compliance register. For a legal/regulatory audience this is table stakes, not a nice-to-have.

### A.6 Risks and honest objections PG&E will raise

| Objection | Honest answer |
|-----------|---------------|
| *"Your agent hallucinated a deadline into our obligation register."* | This is the central risk and it is not fully solvable by prompting. Mitigation is architectural: span-level citation, structured output with schema validation, confidence scoring, and a **mandatory human review gate** before any obligation is committed. The current prototype has none of these. |
| *"Module 3 drafts responses 'suitable for regulatory submission.'"* | No AI-generated text should reach a regulator without qualified human review and sign-off. The platform must be positioned as **preparing** the package, never as filing it. The HITL gate is a hard requirement, not a phase-2 enhancement. |
| *"We already have RegTech feeds and a regulatory affairs team."* | Correct, and the monitoring module is the least differentiated component. The differentiation is downstream: obligation decomposition, impact scoring, and the evidence→gap→response chain. Lead there. |
| *"Who is accountable when the AI misses an obligation?"* | PG&E is. The tool augments; it does not assume regulatory accountability. This must be stated explicitly and early, and the review workflow must make the human reviewer's accountability structural rather than nominal. |
| *"How do we prove to a regulator how a compliance decision was made?"* | Every AI-influenced decision needs a reproducible trace: prompt, model version, retrieved context, output, reviewer, timestamp. The `agent_runs` table (with its `trace_json` column) anticipates exactly this — **and nothing currently writes to it.** Wiring it is cheap and should be done before any pilot. |
| *"Our evidence lives in systems with access controls."* | Retrieval must be access-scoped so an agent can only surface evidence the requesting user is entitled to see. Not implemented. |

### A.7 Recommended engagement shape

**Do not pitch this as a platform.** Pitch a narrow, falsifiable proof.

- **Qualify (weeks 0–2)**: discovery with regulatory affairs, internal audit, and compliance. Size terms
  A–D of A.4 with their numbers. Identify one upcoming audit or data request to target.
- **Prove (weeks 2–8)**: a single-audit pilot. Load the real obligations and the real evidence inventory for
  that audit's scope. Run Module 3. The success criterion is stark and binary: **did it surface a real
  evidence gap the team did not already know about?** Everything else is secondary.
- **Expand (post-pilot)**: only if the pilot clears that bar, build live ingestion for CPUC + OEIS,
  provenance, the review gate, and persistence — Phases 1–2 of §13.

### A.8 Portability (the second commercial argument)

The orchestration graphs are domain-agnostic; only the domain pack is PG&E-specific (`SYSTEM_CONTEXT`, the
department model, the existing-obligation register, the enterprise profile). Once proven at PG&E, the
identical asset re-targets to **Southern California Edison, SDG&E, Sempra and other IOUs** with essentially
the same regulatory perimeter and near-identical WMP/HFTD/PSPS obligations — the shortest possible reuse
path — and then more broadly to any regulated industry (Financial Services, Healthcare, Pharma, Telecom).
The PG&E engagement is therefore worth pursuing as much for the **reference asset** it creates as for its
own margin.
