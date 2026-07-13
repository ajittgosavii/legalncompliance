# Porting to Infosys Topaz Fabric (React)

> **Read this before BLUEPRINT.md if your job is to rebuild the UI.**
>
> BLUEPRINT.md tells you *what the system is*. This tells you *how to move it to React*, and — more
> importantly — **what BLUEPRINT.md alone would NOT have told you.**

---

## The honest answer to "can I rebuild this from the blueprint?"

**No — and not because the blueprint is thin.** Because of a structural fact about the current app:

> ### Streamlit has no API layer.
>
> The page scripts call the agent functions **directly, in-process**. There is no REST contract, no
> request/response schema, no serialisation boundary — because nothing ever needed one.

You cannot build a React frontend against a Python function call. So this is **not a UI rewrite. It
is an architectural split.**

| Today (Streamlit) | On Topaz (React) |
|---|---|
| `pages/1_Regulatory_Monitor.py` calls `run_regulatory_monitor()` in-process | React component → `POST /api/monitor/run` → FastAPI → **the same Python function** |
| Agent output rendered inline with `st.markdown` | Agent output returned as JSON, rendered by React components |
| No API, no schemas, no auth, no async | REST API with typed contracts |

**That seam is now built.** See `api.py`.

---

## What transfers UNCHANGED — do not rewrite any of it

This is ~70% of the value of the asset, and **not one line of it needs to change**:

| Keep as-is | Why |
|---|---|
| `agents/regulatory_monitor/graph.py` | 5-node LangGraph + **the provenance verifier** |
| `agents/obligation_impact/graph.py` | 4-node impact graph |
| `agents/audit_prep/graph.py` | Supervisor + 3 specialists |
| `agents/case_analytics/chain.py` | RAG chain |
| `core/prompts.py` | 7 agent personas |
| `core/domains.py` | **The 4 industry packs — the single lever that re-targets all 7 agents** |
| `core/llm.py` | GPT-4o → automatic failover → Claude Sonnet |
| `core/vectorstore.py`, `core/db.py` | Retrieval, persistence schema |

**Only the UI is thrown away.** `app.py`, `pages/*`, `core/styles.py`, `core/ui.py`.

---

## What you build

### 1. Backend — **already written: `api.py`**

```bash
pip install fastapi uvicorn
uvicorn api:app --reload --port 8000
```

- Interactive docs: `http://localhost:8000/docs`
- **Machine-readable contract: `http://localhost:8000/openapi.json`** (also committed at
  `docs/openapi.json`)

> **Hand the React team `openapi.json`.** They can generate a fully typed TypeScript client from it
> with `openapi-typescript` or `orval`. That is worth more than any amount of prose in a blueprint,
> because it cannot drift from the truth — it is generated from the code.

### 2. Frontend — React components, one per Streamlit page

| Streamlit page | React route | Calls |
|---|---|---|
| `app.py` (Dashboard) | `/` | `GET /api/domains` |
| `pages/1_Regulatory_Monitor.py` | `/monitor` | `POST /api/monitor/run` |
| `pages/2_Obligation_Impact.py` | `/impact` | `GET /api/domains/{d}/regulations` → `POST /api/impact/run` |
| `pages/3_Audit_Prep.py` | `/audit` | `GET /api/domains/{d}/audit-types` → `POST /api/audit/run` |
| `pages/4_Case_Analytics.py` | `/cases` | `GET /api/cases/stats` (no LLM) → `POST /api/cases/analyze` |

---

## The API contract

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/domains` | All 4 industry packs — regulators, departments, counts. Drives every selector |
| `GET` | `/api/domains/{d}/regulations` | Regulation list + full text |
| `GET` | `/api/domains/{d}/audit-types` | Audit type → the obligations it tests |
| `GET` | `/api/domains/{d}/cases` | Enforcement corpus |
| `POST` | `/api/monitor/run` | **WF-01** — alerts + obligations + **provenance summary** |
| `POST` | `/api/impact/run` | **WF-02** — atomic obligations, conflicts, 4-dimension scores, exec report |
| `POST` | `/api/audit/run` | **WF-03 (flagship)** — evidence, **gaps**, draft responses, 0–100 readiness score |
| `POST` | `/api/cases/analyze` | **WF-04** — RAG precedent/trend/risk analysis |
| `GET` | `/api/cases/stats` | Aggregates + penalty timeline. **No LLM call — the dashboard renders free** |
| `GET` | `/api/health` | Readiness + LLM configured |

---

## THE TWO THINGS THE REACT UI MUST GET RIGHT

Everything else is layout. These two are the product.

### 1. Render `citation_verified` — and never flatten it

Every `Obligation` carries:

```ts
{
  source_quote: string        // the VERBATIM span the model copied from the regulation
  source_section: string
  confidence: "high" | "medium" | "low"
  citation_verified: boolean  // <-- THE ONE THAT MATTERS
}
```

`citation_verified` is set by **`_quote_in_source()`** — code, not a prompt. It is `true` only if the
model's quote was actually **found in the source regulation**.

> **A `false` here means the model may have paraphrased or fabricated the obligation.**
>
> The React UI **must** show it with a warning badge, must surface the `Provenance` summary
> (`verified / total`) on the results header, and **must not** let a `false` obligation look the same
> as a `true` one.
>
> If you render them identically, you have thrown away the single mechanism that makes this system
> safe to put in front of a regulated utility. An invented deadline in a compliance register is a
> material harm, not a rounding error.

Suggested treatment:

| `citation_verified` | UI |
|---|---|
| `true` | ✅ green badge — *"Verified against {source_regulation}"* + show `source_quote` as a blockquote |
| `false` | ⚠️ amber badge — *"Quote not found in source — verify manually"*, and force `confidence: low` |

### 2. The human-review gate is not decorative

Every response carries `review_status: "PENDING_HUMAN_REVIEW"` and a `disclaimer`. **Render both.**
Module 3 drafts text explicitly described as *"suitable for regulatory submission"* — the UI must
make it impossible to mistake a draft for a filing.

---

## Gaps you must close before production — and `api.py` will not hide them from you

| # | Gap | Why it matters |
|---|---|---|
| 1 | **WF-01 is `2N + 1` LLM calls** and takes minutes. `POST /api/monitor/run` is **synchronous** — it will time out behind any real gateway. | Make it a **background job** with polling or SSE. The endpoint docstring says so. |
| 2 | **No auth.** | Topaz SSO / RBAC. |
| 3 | **No persistence.** Every run is ephemeral. | `core/db.py` has the schema (`obligations`, `audit_items`, `agent_runs`) and **nothing writes to it**. |
| 4 | **No observability.** `agent_runs` has `tokens_used`, `cost_estimate`, `trace_json` columns — all unwritten. | The cheapest high-value win available. |
| 5 | **CORS is wide open** to localhost dev origins. | Lock down before deploy. |
| 6 | **No live ingestion.** `ingestion/scrapers/` and `ingestion/parsers/` are **empty stub packages**. Regulations are fixture data. | The biggest work item in the whole programme. **Do not let anyone believe ingestion exists because the folders do.** |

---

## Effort for the port specifically

| Task | Effort |
|---|---|
| Backend API (`api.py`) | **DONE** |
| Async job queue for WF-01 (Celery/RQ + polling or SSE) | ~1 week |
| React: 5 routes + typed client generated from `openapi.json` | ~2–3 weeks |
| Provenance badges, review gate, readiness gauge, charts | ~1 week |
| Auth / SSO wiring into Topaz | ~1 week |
| **Total port to a working React app on Topaz** | **~5–6 weeks, 2 engineers** |

This is **the port only**. It does not include live ingestion, persistence, or the evaluation
harness — see BLUEPRINT.md §10 for the full production gap.

---

## Quick start

```bash
git clone https://github.com/ajittgosavii/legalncompliance
cd legalncompliance
pip install -r requirements.txt fastapi uvicorn
cp .env.example .env          # add OPENAI_API_KEY

uvicorn api:app --reload --port 8000
open http://localhost:8000/docs
```

Then, in the React project:

```bash
npx openapi-typescript http://localhost:8000/openapi.json -o src/api/types.ts
```

You now have a fully typed client against a contract generated from the real code — which cannot
drift from it.
