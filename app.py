"""
Regulatory Compliance AI Platform — Main Dashboard

One agentic architecture, many regulated industries. Switch the industry pack in the
sidebar and all seven agents re-target: regulators, departments, obligation register,
evidence repository and enforcement history all swap. No agent code changes.
"""

import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="Regulatory Compliance AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.styles import inject_styles, render_hero, render_kpi_row, render_section
from core.ui import bootstrap, render_data_provenance

inject_styles()
pack = bootstrap()

# --- Everything below is computed from the ACTIVE domain pack. No hard-coded counts. ---
regulators = pack["regulators"]
regulations = pack["regulations"]
cases = pack["cases"]
evidence_docs = sum(len(v) for v in pack["evidence"].values())
audit_types = pack["audit_types"]
total_penalties = sum(c["penalty_amount"] for c in cases)


def _fmt_money(v: float) -> str:
    if v >= 1_000_000_000:
        return f"${v / 1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"${v / 1_000_000:.0f}M"
    return f"${v:,.0f}"


render_hero(
    title="Regulatory Compliance AI Platform",
    subtitle=(
        "Agentic AI for regulatory change monitoring, obligation analysis, audit preparation "
        f"and enforcement analytics — currently configured for {pack['label']}"
    ),
    tech_text="OpenAI GPT-4o  ·  LangGraph Agentic Framework  ·  RAG-Enhanced Analytics",
)

render_kpi_row([
    {"value": str(len(regulators)), "label": "Regulatory Bodies",
     "sublabel": " · ".join(r["code"] for r in regulators)},
    {"value": "4", "label": "AI Modules", "sublabel": "3 Agentic + 1 Generative AI"},
    {"value": "7", "label": "Specialized Agents", "sublabel": "LangGraph State Machines"},
    {"value": str(len(regulations)), "label": "Regulations Monitored",
     "sublabel": f"{len(audit_types)} audit types · {evidence_docs} evidence docs"},
    {"value": str(len(cases)), "label": "Case Records",
     "sublabel": f"{_fmt_money(total_penalties)} total penalty history"},
])

# --- Overview ---
render_section("Overview", "What this platform does and why it matters")

st.markdown(f"""
<div class="module-card" style="border-left: 4px solid #f97316;">
    <div class="module-desc" style="font-size: 1.02rem; line-height: 1.6;">
        <strong>Regulatory Compliance AI</strong> turns the slow, manual work of staying compliant
        into an automated, AI-assisted workflow. It watches the regulators, breaks new rules down into
        concrete, testable obligations with a verifiable citation back to the source text, scores their
        business impact, assembles audit-ready evidence packages with gap analysis, and mines enforcement
        history for precedent — so compliance, legal and operations teams shift from <em>reacting</em> to
        regulatory change to <em>getting ahead</em> of it.
        <br><br>
        The commercial insight: <strong>evidence quality is a financial lever, not administrative
        overhead.</strong> {pack['financial_hook']}
    </div>
</div>
""", unsafe_allow_html=True)

ov1, ov2, ov3 = st.columns(3)
with ov1:
    st.markdown(f"""
    <div class="module-card agentic">
        <div class="module-title" style="font-size: 1.1rem;">What it does</div>
        <div class="module-desc">
            • Monitors {len(regulators)} regulators ({", ".join(r["code"] for r in regulators[:4])}…)<br>
            • Extracts obligations, deadlines &amp; penalties — each with a verified source quote<br>
            • Scores cost, operational, timeline &amp; penalty-risk impact<br>
            • Builds audit packages with evidence mapping &amp; gap analysis<br>
            • Searches {len(cases)} enforcement cases for precedent and trends
        </div>
    </div>
    """, unsafe_allow_html=True)
with ov2:
    st.markdown("""
    <div class="module-card agentic">
        <div class="module-title" style="font-size: 1.1rem;">Who it is for</div>
        <div class="module-desc">
            • Compliance &amp; regulatory-affairs teams<br>
            • Legal counsel and risk management<br>
            • Internal audit and controls<br>
            • Operations leaders in regulated industries<br>
            • Any organisation that must evidence compliance on demand
        </div>
    </div>
    """, unsafe_allow_html=True)
with ov3:
    st.markdown("""
    <div class="module-card genai">
        <div class="module-title" style="font-size: 1.1rem;">Why it is useful</div>
        <div class="module-desc">
            • Cuts hours of manual rule-reading to minutes<br>
            • Finds evidence gaps <em>before</em> the auditor does<br>
            • Protects cost recovery by making compliance provable<br>
            • Grounds decisions in real enforcement precedent<br>
            • Gives leadership a prioritised view of exposure
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Cross-industry ---
render_section("One Architecture, Many Industries", "The agents are domain-agnostic — the domain is a swappable pack")

st.markdown("""
The four workflows contain no industry-specific logic. Everything that makes this "a utility compliance
tool" or "a retail compliance tool" lives in a **domain pack**: the regulators, the departments obligations
route to, the existing-obligation register used for conflict detection, the enterprise profile used for
impact scoring, and the corpora. Switch the pack in the sidebar and all seven agents re-target.
""")

from core.domains import DOMAIN_PACKS

cols = st.columns(len(DOMAIN_PACKS))
for col, (key, p) in zip(cols, DOMAIN_PACKS.items()):
    active = key == pack["key"]
    with col:
        st.markdown(f"""
        <div class="module-card {'agentic' if active else ''}"
             style="{'border-left: 4px solid #f97316;' if active else 'opacity: 0.75;'}">
            <div class="module-number">{p['vertical']}</div>
            <div class="module-title" style="font-size: 1.0rem;">{p['label']}</div>
            <div class="module-desc" style="font-size: 0.85rem;">
                {p['tagline']}<br><br>
                <strong>{len(p['regulators'])}</strong> regulators
                {'&nbsp;·&nbsp;<strong>ACTIVE</strong>' if active else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- Modules ---
render_section("AI Modules", "Select a module from the sidebar or open one below")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="module-card agentic">
        <div class="module-number">Module 01</div>
        <div class="module-title">Regulatory Change Monitor</div>
        <div class="module-desc">
            Monitors {", ".join(r["code"] for r in regulators)} for regulatory change. A five-node agentic
            pipeline classifies each change, extracts obligations <em>with a verified verbatim citation to the
            source text</em>, maps them to departments, and generates prioritised alerts.
        </div>
        <div class="module-tech">5-Node LangGraph Pipeline · GPT-4o · {len(regulations)} Regulations · Citation-verified</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_Regulatory_Monitor.py", label="Open Regulatory Monitor →", icon="📡")

    st.markdown(f"""
    <div class="module-card agentic" style="margin-top: 1rem;">
        <div class="module-number">Module 03</div>
        <div class="module-title">Audit Analysis &amp; Preparation</div>
        <div class="module-desc">
            The flagship. A Supervisor plans the audit, then Evidence Collector, Gap Analyzer and Response
            Drafter work to that plan. Produces a traceable chain — regulation → obligation → evidence → gap →
            owner &amp; date → drafted response — ending in a 0–100 readiness score.
        </div>
        <div class="module-tech">Supervisor + 3 Sub-Agents · {len(audit_types)} Audit Types · {evidence_docs} Evidence Documents</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_Audit_Prep.py", label="Open Audit Preparation →", icon="📋")

with col2:
    st.markdown("""
    <div class="module-card agentic">
        <div class="module-number">Module 02</div>
        <div class="module-title">Obligation Impact Analysis</div>
        <div class="module-desc">
            Decomposes a regulation into atomic, testable obligations. Cross-references them against the
            existing obligation estate to find conflicts and overlaps, scores four impact dimensions
            (cost, operations, timeline, penalty risk), and writes an executive report.
        </div>
        <div class="module-tech">4-Node Impact Graph · GPT-4o · Multi-Dimensional Scoring</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Obligation_Impact.py", label="Open Obligation Impact →", icon="📊")

    st.markdown(f"""
    <div class="module-card genai" style="margin-top: 1rem;">
        <div class="module-number">Module 04</div>
        <div class="module-title">Case Analytics</div>
        <div class="module-desc">
            RAG-powered analysis of enforcement history. Semantic precedent search, penalty trend analysis,
            risk assessment and interactive charts across {len(cases)} cases totalling
            {_fmt_money(total_penalties)} in penalties.
        </div>
        <div class="module-tech">RAG + GPT-4o · {len(cases)} Cases · Plotly Dashboards · No LLM needed to browse</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/4_Case_Analytics.py", label="Open Case Analytics →", icon="🔍")

# --- Start here ---
st.markdown("")
rec1, rec2 = st.columns(2)
with rec1:
    st.success(f"""
    **Recommended: Start Here**

    New to the platform? Open **Case Analytics** — it loads instantly with {len(cases)} pre-loaded
    cases and interactive charts. No AI agent execution required.
    """)
    st.page_link("pages/4_Case_Analytics.py", label="Open Case Analytics →", icon="🔍")
with rec2:
    st.info(f"""
    **Ready to Run AI Agents?**

    Try the **Regulatory Monitor** — one click runs the 5-step agentic pipeline over
    {len(regulations)} regulations, extracting citation-verified obligations.
    """)
    st.page_link("pages/1_Regulatory_Monitor.py", label="Open Regulatory Monitor →", icon="📡")

# --- Guide ---
render_section("Getting Started", "How to use the platform")

tab_start, tab_workflows, tab_arch, tab_trust = st.tabs(
    ["Quick Start", "Module Workflows", "Architecture", "Trust & Limitations"]
)

with tab_start:
    st.markdown(f"""
    ### Step 0: Pick your industry
    Use the **Industry** switcher in the sidebar. The platform is currently configured for
    **{pack['label']}** — {pack['company_full']}. Switching re-targets all seven agents.

    ---

    ### Step 1: Explore Case Analytics (no AI needed)
    {len(cases)} pre-loaded enforcement cases with interactive charts and filters. Nothing to run.

    ---

    ### Step 2: Run your first agent — Regulatory Monitor
    1. Open **Regulatory Monitor**
    2. Pick a regulator (or leave "all")
    3. Click **Run Monitor Agent**
    4. Watch the 5-step pipeline classify, extract, map and alert
    5. Check the **citation badge** on each obligation — the platform verifies that the quote the model
       gave actually appears in the source text. An obligation it cannot verify is flagged, not hidden.

    ---

    ### Step 3: Deep-dive with Obligation Impact
    Pick one regulation, run the impact analysis, and read the executive report: cost range, earliest
    deadline, conflicts with existing obligations, and recommended actions with owners.

    ---

    ### Step 4: Prepare for an audit — the flagship
    1. Open **Audit Preparation**
    2. Choose an audit type and the regulations in scope
    3. Click **Run Audit Prep Agent**
    4. Read the readiness score, then the gaps. **The gaps are the product.** The question that matters
       is whether the agents found an evidence gap your team did not already know about.

    ---

    ### Step 5: Ask questions in Case Analytics
    Natural-language queries over enforcement history — precedent, trend, risk or summary analysis.
    """)

with tab_workflows:
    wf1, wf2 = st.columns(2)
    with wf1:
        st.markdown("""
        #### 1. Regulatory Change Monitor
        **Agentic — 5-node pipeline**

        | Step | Agent Action |
        |------|-------------|
        | Fetch | Load regulatory sources |
        | Classify | Determine change type & severity |
        | Extract | Pull obligations **+ verify source quote** |
        | Map | Assign to departments |
        | Alert | Prioritise by severity |

        ---

        #### 3. Audit Analysis & Preparation
        **Agentic — Supervisor + 3 specialists**

        | Agent | Role |
        |-------|------|
        | Supervisor | Plans the approach; reviews the package against its own plan |
        | Evidence Collector | Maps evidence; rates relevance & sufficiency |
        | Gap Analyzer | Finds gaps; assigns owner, effort, deadline |
        | Response Drafter | Drafts responses with citations |
        """)
    with wf2:
        st.markdown("""
        #### 2. Obligation Impact Analysis
        **Agentic — 4-node graph**

        | Step | Agent Action |
        |------|-------------|
        | Decompose | Break into atomic obligations |
        | Cross-Ref | Find conflicts with existing estate |
        | Score | Cost, operations, timeline, penalty |
        | Report | Executive summary + actions |

        ---

        #### 4. Case Analytics
        **Generative AI — RAG**

        | Feature | Description |
        |---------|-------------|
        | Dashboard | Penalty charts & trends |
        | AI Search | Natural-language case queries |
        | Browser | Filter and explore cases |
        | Analysis | Precedent, trend, risk, summary |
        """)

with tab_arch:
    st.code("""
┌──────────────────────── STREAMLIT UI ─────────────────────────────────┐
│  Regulatory Monitor │ Obligation Impact │ Audit Prep │ Case Analytics │
└──────────┬──────────┴────────┬──────────┴─────┬──────┴────────┬───────┘
           │                   │                │               │
┌──────────▼───────────────────▼────────────────▼───────────────▼───────┐
│                    LangGraph Agent Orchestrator                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐   │
│  │  5-Node     │  │  4-Node      │  │  Supervisor  │  │  RAG      │   │
│  │  Pipeline   │  │  Impact      │  │  + 3 Agents  │  │  Chain    │   │
│  └─────────────┘  └──────────────┘  └──────────────┘  └───────────┘   │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│              INDUSTRY DOMAIN PACK  (core/domains.py)                   │
│   Energy & Utilities  │  Retail  │  Resources  │  Services            │
│   regulators · departments · obligation register · profile · corpora   │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│   OpenAI GPT-4o   │  Claude (failover)  │  TF-IDF Retrieval │ SQLite  │
└───────────────────────────────────────────────────────────────────────┘
    """, language=None)
    st.markdown("""
    **The design point**: the orchestration layer knows nothing about wildfires, or PCI DSS, or methane.
    It knows about *regulations*, *obligations*, *evidence* and *gaps*. The industry lives in the pack.
    """)

with tab_trust:
    st.markdown("""
    ### What this platform will and will not do

    Compliance is a domain where a confident wrong answer is worse than no answer. So:

    **Provenance is enforced, not requested.** Every extracted obligation must carry a verbatim quote from
    the source. The platform then checks that the quote *actually appears* in the source text. If it does
    not, the obligation is flagged `⚠ Quote not found` and its confidence is downgraded — it is never
    presented as equivalent to a verified one.

    **Human review is a gate, not a suggestion.** Output is decision support. The audit package is stamped
    `PENDING_HUMAN_REVIEW`. Nothing here is a compliance determination, and nothing goes to a regulator
    without qualified sign-off.

    **The agents are told not to guess.** Where the source text does not state a deadline or a penalty, the
    agents are instructed to write "not stated in source" rather than estimate. An invented deadline in a
    compliance register is a material harm, not a rounding error.

    ### Known limitations of this prototype

    - **No live ingestion.** Regulations are fixture data, not scraped from regulators. Production requires
      real connectors with change detection.
    - **Retrieval is TF-IDF**, not embeddings. A real vector store and legal-domain embeddings are the
      production path (the seam already exists in `core/embeddings.py`).
    - **Nothing persists.** Runs are ephemeral; the SQLite schema exists but the obligation lifecycle is
      not yet wired to it.
    - **No access-scoped retrieval.** In production, an agent must only see evidence the requesting user is
      entitled to see.
    """)
    render_data_provenance()
