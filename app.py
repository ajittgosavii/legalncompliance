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

# --- Architecture ---
render_section("Platform Architecture")

st.markdown("""
<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1.5rem; font-family: monospace; font-size: 0.8rem; line-height: 1.6; color: #334155;">
<pre style="margin:0; white-space: pre;">
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
</pre>
</div>
""", unsafe_allow_html=True)

# --- Tech Stack ---
render_section("Technology Stack")

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
