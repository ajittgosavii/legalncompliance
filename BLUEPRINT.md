# Regulatory Compliance AI — Solution Blueprint

> Complete architectural, functional and commercial description of the **PG&E Regulatory Compliance
> AI Platform**, structured for import into **Infosys Topaz Fabric** as an agentic solution asset.
>
> Repository: `https://github.com/ajittgosavii/legalncompliance` · commit `1021968` · 2026-07-12
>
> **Status:** working prototype. Agent graphs, provenance verification, human-review gate and four
> industry packs are implemented and render-tested. Live regulator ingestion, real embeddings and
> persistence are **not** built — see §12. Do not present this as a system that monitors anything
> today; it is a working prototype of the target architecture.

---

## 1. Solution Metadata

```yaml
solution:
  id: regulatory-compliance-ai
  name: Regulatory Compliance AI Platform
  tagline: From reacting to regulatory change, to getting ahead of it.
  version: 0.2.0
  anchor_client: Pacific Gas and Electric Company (PG&E)
  domain: Legal, Risk & Compliance (LRC) — Regulatory Change Management, Audit Readiness
  primary_industry: Energy & Utilities (electric + gas)
  pattern: Multi-agent orchestration (LangGraph) + RAG + programmatic provenance verification
  interface: Streamlit multipage (5 pages)
  language: Python 3.11+
  loc: ~5,400
  data_classification: synthetic / illustrative only — no real client data, no PII

capabilities:
  agents: 7                  # 7 specialised personas, 4 workflows
  workflows: 4               # 3 agentic (LangGraph) + 1 generative (RAG)
  industry_packs: 4          # Energy & Utilities (PG&E) · Retail · Resources · Services
  regulators: 9              # CPUC · OEIS · FERC · NERC · CARB · EPA · PHMSA · Cal-OSHA · CEC
  guardrails: 3              # provenance verification · human-review gate · fail-loud parsing

deployment:
  target: Streamlit Cloud
  entrypoint: app.py
  secrets: OPENAI_API_KEY (required) · ANTHROPIC_API_KEY (optional — automatic failover)
```

### One-line description

An agentic AI platform that watches the regulators PG&E answers to, decomposes each new rule into
atomic, testable obligations **with a machine-verified citation back to the source text**, scores
their business impact, assembles audit-ready evidence packages with gap analysis and named
remediation owners, and mines enforcement history for precedent.

---

## 2. The Problem — and why it is a PG&E problem specifically

PG&E must track a continuous stream of rulemakings, orders, resolutions and emergency regulations
across **nine** federal and state bodies. Today this is manual: analysts read hundreds of pages of
dense legal prose, hand-extract obligations into spreadsheets, chase document owners for audit
evidence, and rely on institutional memory for enforcement precedent.

The result is late detection, missed deadlines, **evidence gaps discovered *during* an audit rather
than before it**, and avoidable exposure.

### Why PG&E is the natural anchor client

PG&E's distinguishing condition is not that it has more rules than its peers. It is that it operates
under **sustained, intense regulatory scrutiny**, with a documented enforcement history. So the
expensive recurring work is not *knowing* the rule — it is **proving compliance on demand**, and the
costly failure mode is an evidence gap found by an auditor rather than by PG&E.

> **The commercial insight that makes this a business case rather than a productivity tool:**
> under California's post-2019 wildfire framework (AB 1054), demonstrated Wildfire Mitigation Plan
> compliance and the annual **Safety Certification** affect the presumption applied in cost-recovery
> proceedings. Separately, the CPUC can **disallow** claimed costs where compliance or process cannot
> be evidenced.
>
> **The ability to evidence compliance on demand is therefore an input to cost recovery — not
> administrative overhead.** An evidence gap is financial risk, not merely audit risk.

⚠️ **Verify before quoting.** The precise legal mechanics of AB 1054's presumption must be confirmed
with qualified counsel before any dollar figure is attached to this chain. What is defensible is the
*mechanism*; what is **not** yet defensible is a specific quantified saving. See §11.

---

## 3. The Regulatory Perimeter

| Code | Body | Scope |
|------|------|-------|
| **CPUC** | California Public Utilities Commission | State economic + safety regulator. Its Safety and Enforcement Division (SED) audits and enforces |
| **OEIS** | Office of Energy Infrastructure Safety | **State wildfire-safety regulator. WMPs are filed with, and approved by, OEIS — NOT the CPUC.** OEIS issues the annual Safety Certification; the CPUC ratifies |
| FERC | Federal Energy Regulatory Commission | Interstate transmission, planning, wholesale rates |
| NERC | North American Electric Reliability Corp. (WECC region) | Grid reliability and OT cybersecurity (NERC CIP) |
| CARB | California Air Resources Board | Emissions, cap-and-trade |
| EPA | Environmental Protection Agency | Federal environmental compliance |
| PHMSA | Pipeline & Hazardous Materials Safety Admin. | Federal pipeline safety (CPUC is the state agent) |
| Cal-OSHA | CA Div. of Occupational Safety and Health | Worker safety |
| CEC | California Energy Commission | Energy policy, load forecasting |

> ### A defect we found and fixed — and why it matters more than it looks
>
> The original codebase routed **Wildfire Mitigation Plans to the CPUC**, and did not list OEIS as a
> regulator at all. Since 2021 WMPs go to **OEIS**.
>
> Getting this wrong in front of PG&E's regulatory affairs team — on the single topic they care most
> about — would have ended the credibility conversation before the demo started. The system prompt
> now carries an explicit instruction: *"Never state that a WMP is filed with or approved by the
> CPUC."*
>
> **This is the kind of error a generic RegTech tool makes and a domain-grounded one does not.**

---

## 4. Architecture

```
┌────────────────────────── STREAMLIT UI (5 pages) ──────────────────────────┐
│  Dashboard │ Regulatory Monitor │ Obligation Impact │ Audit Prep │ Cases    │
└──────────┬─────────┬─────────────────┬──────────────────┬──────────┬───────┘
           │         │                 │                  │          │
┌──────────▼─────────▼─────────────────▼──────────────────▼──────────▼───────┐
│                        LangGraph Orchestration                              │
│  WF-01 Monitor      WF-02 Impact       WF-03 Audit Prep      WF-04 Cases    │
│  5-node pipeline    4-node graph       Supervisor + 3        RAG chain      │
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼───────────────────────────────────────────┐
│  core/provenance  ← THE GATE. Every obligation must quote the regulation    │
│                     verbatim, and the system VERIFIES the quote exists.     │
│                     CODE, not a prompt. Unverifiable → flagged, downgraded. │
│  core/domains.py  ← Industry packs. The agents contain NO industry logic.   │
│  core/prompts.py  ← 7 agent personas, composed from the active pack         │
│  core/llm.py      ← GPT-4o primary → automatic failover → Claude Sonnet     │
│  core/db.py       ← SQLite (PostgreSQL-ready): obligations, gaps, agent_runs│
└────────────────────────────────┬───────────────────────────────────────────┘
                                 │
                                 ▼
                   HUMAN REVIEWER SIGNS OFF
        (PENDING_HUMAN_REVIEW — the platform determines nothing)
```

### Repository map

| Path | Role |
|------|------|
| `app.py` | Dashboard, KPIs (computed, not hard-coded), industry switcher, honest-limits tab |
| `pages/1_Regulatory_Monitor.py` | WF-01 UI — alerts + **citation badges** on every obligation |
| `pages/2_Obligation_Impact.py` | WF-02 UI — executive impact report |
| `pages/3_Audit_Prep.py` | WF-03 UI — **the flagship**: readiness score, gaps, drafted responses |
| `pages/4_Case_Analytics.py` | WF-04 UI — precedent search, penalty trends, case browser |
| `agents/regulatory_monitor/graph.py` | 5-node LangGraph + **`_quote_in_source()` provenance verifier** |
| `agents/obligation_impact/graph.py` | 4-node impact graph |
| `agents/audit_prep/graph.py` | Supervisor + 3 specialists (**plan-discard bug fixed**) |
| `agents/case_analytics/chain.py` | RAG chain over the enforcement corpus |
| `core/domains.py` | **Industry packs** — the single point of domain grounding |
| `core/prompts.py` | 7 agent personas, composed at call time from the active pack |
| `core/ui.py` | Industry switcher, review gate, citation badges, credential resolution |

---

## 5. Agent Registry

Seven personas. All prompts are composed as `build_system_context(active_pack) + role_instructions`,
so **the pack is the single lever that re-targets every agent.**

| ID | Agent | Workflow | Responsibility |
|----|-------|----------|----------------|
| AG-01 | **Regulatory Monitor** | WF-01 | Classify change type + severity; extract obligations **with verified provenance**; map to departments |
| AG-02 | **Obligation Impact** | WF-02 | Decompose into atomic obligations; cross-reference the existing estate for conflicts; score 4 impact dimensions; write the executive report |
| AG-03 | **Audit Supervisor** | WF-03 | Plan the audit approach; then **review the specialists against the plan it set**; issue a 0–100 readiness score |
| AG-04 | **Evidence Collector** | WF-03 | Map evidence to each obligation; rate relevance + sufficiency; flag stale documents |
| AG-05 | **Gap Analyzer** | WF-03 | Type and rank each gap; assign remediation owner, effort, deadline |
| AG-06 | **Response Drafter** | WF-03 | Draft submission-grade regulatory responses with evidence citations |
| AG-07 | **Case Analytics** | WF-04 | RAG over enforcement precedent — precedent / trend / risk / summary |

---

## 6. Workflows

### WF-01 — Regulatory Change Monitor (5-node LangGraph)

```
fetch → classify → extract → map → notify → END
```

| Node | Type | LLM calls |
|------|------|-----------|
| `fetch` | Deterministic — load regulations, filter by regulator | 0 |
| `classify` | Change type, severity, summary, deadlines, penalties | **1 per regulation** |
| `extract` | Atomic obligations **+ verbatim source quote + verification** | **1 per regulation** |
| `map` | Batched — map every obligation to departments, effort, capex, timeline risk | 1 |
| `notify` | Deterministic — join and severity-sort into alerts | 0 |

**Cost profile: `2N + 1` LLM calls** for N regulations. This is the dominant cost driver and the
first target for optimisation (model tiering on `classify`, batching, incremental processing).

### WF-02 — Obligation Impact Analysis (4-node LangGraph)

```
decompose → cross_ref → score → report → END
```

Scores each obligation on **four dimensions**, each with a score, a quantified range and a rationale:
**cost** (1–10, $ range, capex/opex) · **operational** (affected processes, workforce) ·
**timeline risk** (feasibility, critical path) · **penalty risk** (max penalty, enforcement
likelihood). Exactly 4 LLM calls — predictable and cheap.

### WF-03 — Audit Analysis & Preparation (Supervisor pattern) — **THE FLAGSHIP**

```
plan (Supervisor) → collect_evidence → analyze_gaps → draft_responses → supervisor_review → END
```

Produces a **traceable chain**:

> **regulation → obligation → evidence document → gap → remediation owner & date → drafted response**

terminating in a **0–100 readiness score** for the audit committee. That chain is the artefact a
utility needs when a regulator says *"show me."*

> **Defect fixed:** `plan_audit()` previously called the LLM and **discarded the response**. The plan
> never reached the specialists — the supervisor did not actually supervise. The plan is now threaded
> into all three specialists, and the final review explicitly checks them against it.

### WF-04 — Case Analytics (RAG)

Retrieval over the enforcement corpus → precedent / trend / risk / summary analysis. Also renders an
interactive dashboard with **no LLM call at all** — the recommended zero-cost entry point for a demo.

---

## 7. The Trust Architecture — why this is safe to put in front of a regulated utility

### 7.1 Provenance is a CODE check, not a prompt

Every extracted obligation must carry a **verbatim quote** from the source regulation. The system then
**programmatically verifies the quote exists** in the source text (`_quote_in_source()`).

- Exact match (whitespace/case-normalised) → **verified**
- Elision tolerated (a substantial leading span matches) → **verified**
- Otherwise → **`citation_verified: false`**, confidence force-downgraded to `low`, and the UI shows
  **⚠ Quote not found in source — verify manually**

**The model cannot talk its way past this, because it is code.**

> An invented deadline entering a compliance register is a **material harm**, not a rounding error.
> So the platform does not ask the model to be honest — **it checks.**

The UI reports `Citations Verified: n/m` on every run and raises a warning banner if any obligation
could not be traced.

### 7.2 Human review is a gate, not a suggestion

Module 3 drafts text explicitly described as *"suitable for regulatory submission."* Every audit
package is stamped **`PENDING_HUMAN_REVIEW`**. The platform **prepares** the package. It never files
it. Nothing reaches a regulator without qualified sign-off.

### 7.3 The agents are instructed not to guess

Where the source text does not state a deadline or a penalty, agents must write
**"not stated in source"** rather than estimate — and must label an inference as an inference.

### 7.4 Fail loud

A JSON parse failure surfaces as an explicit unreliable-review finding. In a compliance system,
silence reads as *"nothing wrong here"* — the most dangerous possible failure mode.

---

## 8. Industry Packs — the reuse thesis

The four agent graphs contain **no industry-specific logic**. Everything that makes this "a utility
compliance tool" lives in `core/domains.py`: the regulators, the departments obligations route to,
the existing-obligation register used for conflict detection, the enterprise profile used for impact
scoring, and the corpora.

| Pack | Regulators | Corpora | Financial hook |
|------|-----------|---------|----------------|
| **Energy & Utilities (PG&E)** | 9 | 11 regs · 29 cases · 48 evidence docs · 7 audit types | AB 1054 — evidence quality feeds the cost-recovery presumption |
| Retail | 8 (FTC, FDA, CPSC, CPPA, PCI…) | 3 regs · 6 cases · 22 evidence docs | A traceability gap turns a 3-SKU recall into a 47-SKU recall |
| Resources | 7 (EPA, OSHA PSM, PHMSA…) | 3 regs · 5 cases · 18 evidence docs | The tail risk is the consent decree, not the penalty |
| Services | 7 (SEC, DORA, EU AI Act…) | 3 regs · 5 cases · 20 evidence docs | One control gap breaches dozens of client contracts at once |

**Switch the pack → all 7 agents re-target. No agent code changes.**

> ⚠️ **Do not lead with breadth.** Depth at PG&E is the pitch. The other three packs prove the
> architecture is domain-agnostic — they are the *second act*, not the headline. Verified: 4/4 packs
> build 7/7 agent prompts; all 5 pages render across every pack.

---

## 9. Data Assets

Ground-truth counts, measured from source (the original UI claimed 12 / 28 / $19.8B — **now computed
from the actual data, not hard-coded**):

| Asset | Count |
|-------|-------|
| Regulatory updates (Energy pack) | **11** — OEIS 1, CPUC 3, FERC 2, NERC 1, CARB 1, EPA 1, PHMSA 1, Cal-OSHA 1 |
| Enforcement cases | **29** — CPUC 15, NERC/FERC 4, CARB 3, Cal-OSHA 3, PHMSA 2, FERC 1, CEC 1 |
| Total penalty value in corpus | **$17.47B** |
| Audit evidence documents | **48** across 8 categories |
| Audit types | **7** |

Evidence documents carry a `status` of `current / draft / partial / needs_update` — the stale ones are
the seeded gaps the Gap Analyzer is meant to find.

> **DATA PROVENANCE: all corpora are ILLUSTRATIVE.** Realistic in structure and vocabulary; not
> verified records of real regulations or real enforcement actions. The app says so on screen. Before
> a PG&E conversation, **the case corpus must be replaced with the real public enforcement record** —
> PG&E will recognise its own history instantly, and precedent analysis on invented cases is worthless.

---

## 10. Prototype → Production Gap (honest)

**This is the most important section for a Topaz Fabric import.** The solution is a well-architected
demo, not a production system.

| # | Gap | Required for production | Effort |
|---|-----|------------------------|--------|
| G1 | **No live ingestion.** `ingestion/scrapers/` and `ingestion/parsers/` are **empty stub packages**. All regulations are hard-coded Python dicts. | Real connectors to CPUC/OEIS/FERC publication feeds; PDF+HTML parsing; change detection and de-duplication. **The single biggest work item.** | **L** |
| G2 | **No real semantic retrieval.** TF-IDF keyword overlap, not embeddings. | Managed vector store + legal-domain embeddings (`voyage-law-2`). The seam already exists in `core/embeddings.py`. | S |
| G3 | **Nothing persists.** Every run is ephemeral in session state. | Wire `core/db.py`; SQLite → PostgreSQL; obligations/gaps with lifecycle status. | M |
| G4 | **No observability.** `agent_runs` has `tokens_used`, `cost_estimate` and `trace_json` columns — **and nothing writes to them.** | Wire `log_agent_run()`. Cheapest high-value win available. | S |
| G5 | **No span-level provenance.** Citation is verified, but not anchored to a character offset in a source PDF. | Required for legal defensibility. | M |
| G6 | **No structured-output enforcement.** JSON is prompt-instructed and brace-sliced. | Tool-calling with schema validation + retry. | S |
| G7 | **No evaluation harness.** No golden set; extraction accuracy is unmeasured. | Precision/recall on obligation extraction against a human-extracted golden set. **Until this exists, every quality claim is anecdote.** | M |
| G8 | **No SSO/RBAC, no access-scoped retrieval.** An agent can see all evidence. | Enterprise table stakes. | M |

*S = 1–3 weeks · M = 3–8 weeks · L = 8–16 weeks (elapsed, for the stated team)*

---

## 11. Commercial Model

### The value chain, in the right order

**Lead with audit readiness, not with monitoring.** Regulatory change monitoring is the *least*
differentiated capability — PG&E's regulatory affairs function already tracks CPUC dockets closely,
and commercial RegTech feeds exist. The differentiation is downstream: **obligation decomposition,
impact scoring, and the evidence → gap → response chain.**

| Driver | Why it lands at PG&E | How to prove it |
|--------|---------------------|-----------------|
| **1. Audit readiness / evidence-gap elimination** | The binding constraint is *proving* compliance under scrutiny. The costly failure is a gap found by an auditor. | Run Module 3 against one real upcoming audit. **Any gap it finds that the team did not have is the entire business case.** |
| **2. Obligation decomposition** | One CPUC decision contains a dozen separately-testable duties, extracted by hand today. | Precision/recall against a human-extracted golden set for 5–10 real decisions. |
| **3. Cross-obligation conflict detection** | New OEIS/CPUC requirements routinely collide with GO 95/165 and existing WMP commitments. | Highest ceiling; needs the real obligation register loaded. |
| **4. Enforcement precedent** | Penalty conversations currently rest on institutional memory. | Load the real public case record. |

### ⚠️ What we deliberately do NOT claim

It is tempting to anchor the business case to PG&E's headline penalty history. **Do not.** Those
penalties arose overwhelmingly from **operational** failures — pipeline integrity, vegetation
management, equipment maintenance. **This platform does not prevent a wildfire.** Claiming a share of
a multi-billion-dollar penalty would be dishonest, and a PG&E audience would see through it
immediately.

The defensible exposure argument is narrow and specific: **findings and cost disallowances that
turned on inadequate documentation, missing evidence, or unprovable process.** A smaller number — and
one PG&E's own Regulatory Affairs team can help size, which is what makes it credible.

### Run cost — computed, not assumed

WF-01 costs `2N+1` LLM calls. A full 11-regulation monitoring run is **well under $1**. An audit-prep
run is ~5 calls, roughly **$0.20**. At enterprise volume, annual inference cost lands in the **low
thousands**.

> **Inference cost is NOT the constraint.** The cost is engineering, integration and change
> management. Anyone presenting token cost as the main expense line has not understood the problem.

### Indicative engagement (ILLUSTRATIVE — must be validated)

| Stage | Duration | Indicative revenue |
|-------|----------|-------------------|
| Qualify & discovery | 2–4 weeks | $100k – 200k |
| Single-audit pilot | 6–8 weeks | $300k – 600k |
| Production build (ingestion, provenance, review workflow, persistence) | 6–9 months | $1.2M – 2.5M |
| Managed run | annual | $300k – 800k ARR |

**Time to production MVP: ~7–9 months, ~28 FTE-months.** Each additional industry pack: **~2.5
FTE-months** — that reuse ratio is the strongest commercial argument in this document.

---

## 12. Verification Status

### ✅ Verified by test
- All files parse; **4/4 industry packs build 7/7 agent prompts**
- **All 5 pages render across every pack**
- Provenance verifier is wired into WF-01 and reports `citation_verified` per obligation
- Supervisor plan is threaded into all three specialists (the discard bug is closed)
- KPI counts are computed from the data, not hard-coded

### ⚠️ NOT verified
- **Agent output quality is unmeasured.** There is no golden set and no evaluation harness (G7).
  Until one exists, every claim about extraction accuracy is an anecdote.
- **The provenance verifier's *hit rate* against real LLM output is unknown.** The mechanism is
  unit-testable; how often GPT-4o actually quotes verbatim rather than paraphrasing is not yet
  measured. If it paraphrases, obligations will correctly show as UNVERIFIED — the system stays
  honest, but the review *looks* weak. That is a prompt-tuning problem, and the `Citations Verified`
  metric on screen will reveal it immediately.

---

## 13. Recommended Engagement Shape

**Do not pitch a platform. Pitch one narrow, falsifiable proof.**

1. **Qualify (weeks 0–2)** — discovery with Regulatory Affairs, Internal Audit and Compliance. Size
   the value with PG&E's own numbers. Identify **one upcoming audit or data request** to target.
2. **Prove (weeks 2–8)** — a single-audit pilot. Load the **real** obligations and the **real**
   evidence inventory for that audit's scope. Run Module 3.
   > **Success is binary: did it surface a real evidence gap the team did not already know about?**
   > Everything else is secondary. **The test is designed so it can fail** — and if it does, we say so.
3. **Expand (post-pilot)** — only if the pilot clears that bar: live ingestion for CPUC + OEIS,
   span-level provenance, the review workflow, persistence.

---

## 14. Topaz Fabric Import Summary

```yaml
asset_type: agentic_solution
agents: 7
workflows: 4                # 3 LangGraph state machines + 1 RAG chain
industry_packs: 4           # Energy & Utilities (PG&E) · Retail · Resources · Services
regulators: 9               # incl. OEIS — the fix that earns credibility with PG&E
guardrails:
  - programmatic citation verification (CODE, not a prompt) — flags unverifiable obligations
  - mandatory human-review gate (PENDING_HUMAN_REVIEW)
  - fail-loud parsing (no silent empty results in a compliance system)
models: GPT-4o primary, Claude Sonnet automatic failover, 4 tiers available
pii: none — all corpora synthetic
production_readiness: prototype — 8 architectural gaps (§10); no live ingestion
```

### The reusable IP

1. **The obligation-extraction contract** — a schema for turning dense legal prose into atomic,
   assignable, testable, measurable obligations. **The heart of the asset.**
2. **Programmatic provenance verification** — the code that proves a model's citation is real and
   flags it when it is not. **The most transferable component in the portfolio**: it is what makes
   *any* LLM safe to deploy in a domain where a confident wrong answer causes harm.
3. **The four-dimension impact scoring model** — cost / operational / timeline / penalty risk, each
   with a score, a quantified range and a rationale.
4. **The supervisor audit chain** — regulation → obligation → evidence → gap → response, terminating
   in a 0–100 readiness score.
5. **The swappable industry pack** — domain content fully separated from agent logic.

Everything else — the regulators, the departments, the corpora — is a **pack** to be replaced per
client.
