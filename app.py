"""
PWE Compliance & Regulatory AI Platform
Main Dashboard
"""

import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load API keys from Streamlit secrets
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

st.set_page_config(
    page_title="PWE Compliance AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.styles import inject_styles, render_hero, render_kpi_row, render_section

inject_styles()

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Navigation")
    st.page_link("app.py", label="Dashboard", icon="🏠")
    st.page_link("pages/1_Regulatory_Monitor.py", label="Regulatory Monitor", icon="📡")
    st.page_link("pages/2_Obligation_Impact.py", label="Obligation Impact", icon="📊")
    st.page_link("pages/3_Audit_Prep.py", label="Audit Preparation", icon="📋")
    st.page_link("pages/4_Case_Analytics.py", label="Case Analytics", icon="🔍")
    st.markdown("---")
    st.markdown("##### Platform Info")
    st.markdown("""
    - **LLM**: OpenAI GPT-4o
    - **Framework**: LangGraph
    - **Search**: TF-IDF In-Memory
    - **Agents**: 7 Specialized
    """)
    api_status = "Connected" if os.getenv("OPENAI_API_KEY") else "Not Configured"
    api_color = "🟢" if os.getenv("OPENAI_API_KEY") else "🔴"
    st.markdown(f"**API Status**: {api_color} {api_status}")

# --- Hero Banner ---
render_hero(
    title="PWE Compliance & Regulatory AI Platform",
    subtitle="Agentic AI and Generative AI for Regulatory Change Monitoring, Obligation Analysis, Audit Preparation, and Case Analytics",
    tech_text="OpenAI GPT-4o  ·  LangGraph Agentic Framework  ·  RAG-Enhanced Analytics"
)

# --- KPI Row ---
render_kpi_row([
    {"value": "7", "label": "Regulatory Bodies", "sublabel": "CPUC · FERC · NERC · CARB · EPA · PHMSA · Cal-OSHA"},
    {"value": "4", "label": "AI Modules", "sublabel": "3 Agentic + 1 Generative AI"},
    {"value": "7", "label": "Specialized Agents", "sublabel": "LangGraph State Machines"},
    {"value": "12", "label": "Active Regulations", "sublabel": "Monitored in Real-Time"},
    {"value": "28", "label": "Case Records", "sublabel": "$19.8B Total Penalty History"},
])

# --- Module Cards ---
render_section("AI Modules", "Select a module from the sidebar or click below to begin")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="module-card agentic">
        <div class="module-number">Module 01</div>
        <div class="module-title">Regulatory Change Monitor</div>
        <div class="module-desc">
            Continuously monitors CPUC, FERC, NERC, CARB, EPA, PHMSA, and Cal-OSHA for regulatory
            changes. Multi-step agentic pipeline automatically classifies changes, extracts obligations,
            maps to departments, and generates prioritized alerts.
        </div>
        <div class="module-tech">5-Node LangGraph Pipeline · GPT-4o · 12 Sample Regulations</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_Regulatory_Monitor.py", label="Open Regulatory Monitor →", icon="📡")

    st.markdown("""
    <div class="module-card agentic" style="margin-top: 1rem;">
        <div class="module-number">Module 03</div>
        <div class="module-title">Audit Analysis & Preparation</div>
        <div class="module-desc">
            Multi-agent system with Supervisor coordinating Evidence Collector, Gap Analyzer,
            and Response Drafter. Produces audit-ready packages with evidence mapping, gap
            identification, and professional regulatory responses.
        </div>
        <div class="module-tech">Supervisor + 3 Sub-Agents · 7 Audit Types · 45+ Evidence Documents</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_Audit_Prep.py", label="Open Audit Preparation →", icon="📋")

with col2:
    st.markdown("""
    <div class="module-card agentic">
        <div class="module-number">Module 02</div>
        <div class="module-title">Obligation Impact Analysis</div>
        <div class="module-desc">
            Decomposes complex regulations into atomic, testable obligations. Cross-references
            against existing requirements, scores multi-dimensional impact (cost, operations,
            timeline, penalty risk), and generates executive reports.
        </div>
        <div class="module-tech">4-Node Impact Graph · GPT-4o · Multi-Dimensional Scoring</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Obligation_Impact.py", label="Open Obligation Impact →", icon="📊")

    st.markdown("""
    <div class="module-card genai" style="margin-top: 1rem;">
        <div class="module-number">Module 04</div>
        <div class="module-title">Case Analytics</div>
        <div class="module-desc">
            RAG-powered analysis of historical enforcement cases across 7 regulators.
            Semantic precedent search, penalty trend analysis, risk assessment, and
            interactive visualizations with 28 case records totaling $19.8B in penalties.
        </div>
        <div class="module-tech">RAG + GPT-4o · 28 Cases · 7 Regulators · Plotly Dashboards</div>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/4_Case_Analytics.py", label="Open Case Analytics →", icon="🔍")

# --- Recommended Start ---
st.markdown("")
rec1, rec2 = st.columns([1, 1])
with rec1:
    st.success("""
    **Recommended: Start Here**

    New to the platform? Begin with **Case Analytics** — it loads instantly with
    interactive charts and 28 pre-loaded cases. No AI agent execution required.
    """)
    st.page_link("pages/4_Case_Analytics.py", label="Open Case Analytics →", icon="🔍")
with rec2:
    st.info("""
    **Ready to Run AI Agents?**

    Try the **Regulatory Monitor** — click one button to watch the 5-step agentic
    pipeline classify 12 regulations, extract obligations, and generate prioritized alerts.
    """)
    st.page_link("pages/1_Regulatory_Monitor.py", label="Open Regulatory Monitor →", icon="📡")

# --- Getting Started Guide ---
render_section("Getting Started", "Follow these steps to begin using the platform")

tab_start, tab_workflows, tab_arch = st.tabs(["Quick Start Guide", "Module Workflows", "Architecture & Tech Stack"])

with tab_start:
    st.markdown("""
    ### Step 1: Explore the Case Analytics Dashboard (No AI needed)

    The **Case Analytics** module loads instantly with **28 pre-loaded enforcement cases**
    across 7 regulators. You can explore interactive charts, browse cases, and filter by
    regulator, type, and penalty — all without running any AI agents.

    **Try it now:** Click **Case Analytics** in the sidebar.

    ---

    ### Step 2: Run Your First AI Agent — Regulatory Monitor

    This is the best place to start with AI-powered analysis:

    1. Navigate to **Regulatory Monitor** in the sidebar
    2. Select a regulator from the dropdown (or leave as "All")
    3. Click **"Run Monitor Agent"**
    4. Watch the 5-step agentic pipeline process 12 regulations in real time
    5. Review the generated alerts sorted by severity — each includes extracted obligations,
       affected departments, deadlines, and penalty risks

    **What happens behind the scenes:** The AI agent reads each regulation, classifies the
    change type and severity, extracts specific compliance obligations, maps them to your
    departments, and generates prioritized alerts.

    ---

    ### Step 3: Deep-Dive with Obligation Impact Analysis

    Once you've seen the regulatory alerts, pick any specific regulation for deep analysis:

    1. Navigate to **Obligation Impact** in the sidebar
    2. Select a regulation from the dropdown
    3. Click **"Run Impact Analysis"**
    4. Review the executive report with cost estimates, deadlines, and recommended actions
    5. Explore each decomposed obligation with multi-dimensional impact scores

    ---

    ### Step 4: Prepare for an Audit

    The most powerful module — a team of 4 AI agents working together:

    1. Navigate to **Audit Preparation** in the sidebar
    2. Choose an audit type (e.g., "CPUC Wildfire Safety Audit")
    3. Select the regulations in scope
    4. Click **"Run Audit Prep Agent"**
    5. Review the Supervisor's readiness score, evidence inventory, gap analysis, and draft responses

    ---

    ### Step 5: Ask Questions in Case Analytics

    Use natural language to query the enforcement case database:

    1. Navigate to **Case Analytics** in the sidebar
    2. Type a question like *"What are the precedents for wildfire penalties?"*
    3. Select an analysis type (precedent, trend, risk, or summary)
    4. Review AI-generated analysis with relevant cases, risk assessment, and recommendations
    """)

with tab_workflows:
    st.markdown("### Module Workflow Details")
    st.markdown("")

    wf1, wf2 = st.columns(2)
    with wf1:
        st.markdown("""
        #### 1. Regulatory Change Monitor
        **Type:** Agentic AI (5-node pipeline)

        | Step | Agent Action |
        |------|-------------|
        | Fetch | Scans 7 regulatory sources |
        | Classify | AI determines change type & severity |
        | Extract | Pulls specific obligations from text |
        | Map | Assigns to PWE departments |
        | Alert | Generates prioritized notifications |

        **Best for:** Staying current with regulatory changes,
        identifying new compliance obligations early.

        ---

        #### 3. Audit Analysis & Preparation
        **Type:** Agentic AI (Supervisor + 3 Sub-Agents)

        | Agent | Role |
        |-------|------|
        | Supervisor | Plans approach, reviews final package |
        | Evidence Collector | Finds and validates documentation |
        | Gap Analyzer | Identifies compliance gaps |
        | Response Drafter | Writes audit-ready responses |

        **Best for:** Preparing for regulatory audits,
        identifying evidence gaps before auditors arrive.
        """)

    with wf2:
        st.markdown("""
        #### 2. Obligation Impact Analysis
        **Type:** Agentic AI (4-node graph)

        | Step | Agent Action |
        |------|-------------|
        | Decompose | Breaks regulation into atomic obligations |
        | Cross-Ref | Checks conflicts with existing rules |
        | Score | Rates cost, operations, timeline, penalty |
        | Report | Generates executive summary |

        **Best for:** Understanding the full impact of a new
        regulation before planning compliance response.

        ---

        #### 4. Case Analytics
        **Type:** Generative AI (RAG + Search)

        | Feature | Description |
        |---------|-------------|
        | Dashboard | Interactive penalty charts & trends |
        | AI Search | Natural language case queries |
        | Browser | Filter & explore 28 cases |
        | Analysis | Precedent, trend, risk, summary |

        **Best for:** Understanding enforcement history,
        finding precedents, assessing penalty exposure.
        """)

with tab_arch:
    st.markdown("### Platform Architecture")
    st.code("""
┌──────────────────────── STREAMLIT CLOUD UI ────────────────────────────┐
│  Regulatory Monitor │ Obligation Impact │ Audit Prep │ Case Analytics  │
└──────────┬──────────┴────────┬──────────┴─────┬──────┴────────┬───────┘
           │                   │                │               │
┌──────────▼───────────────────▼────────────────▼───────────────▼───────┐
│                    LangGraph Agent Orchestrator                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  5-Node     │  │  4-Node      │  │  Supervisor  │  │  RAG      │  │
│  │  Pipeline   │  │  Impact      │  │  + 3 Agents  │  │  Chain    │  │
│  └─────────────┘  └──────────────┘  └──────────────┘  └───────────┘  │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│   OpenAI GPT-4o    │   Claude (Fallback)  │  TF-IDF Search  │ SQLite │
└───────────────────────────────────────────────────────────────────────┘
    """, language=None)

    st.markdown("### Technology Stack")

    tc1, tc2, tc3, tc4 = st.columns(4)
    with tc1:
        st.markdown("""
        **AI / LLM**
        - OpenAI GPT-4o (primary)
        - Claude Sonnet (fallback)
        - LangGraph orchestration
        """)
    with tc2:
        st.markdown("""
        **Data**
        - In-Memory TF-IDF search
        - SQLite structured store
        - 28 enforcement cases
        """)
    with tc3:
        st.markdown("""
        **Regulatory**
        - 12 active regulations
        - 7 regulatory bodies
        - 45+ evidence documents
        """)
    with tc4:
        st.markdown("""
        **Application**
        - Streamlit Cloud
        - Plotly visualizations
        - Python 3.11+
        """)
