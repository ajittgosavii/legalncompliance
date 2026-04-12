"""
PWE Compliance & Regulatory AI Platform
Main Streamlit Application
"""

import streamlit as st
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load API keys from Streamlit secrets (Streamlit Cloud) or .env (local)
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
if "VOYAGE_API_KEY" in st.secrets:
    os.environ["VOYAGE_API_KEY"] = st.secrets["VOYAGE_API_KEY"]
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

st.set_page_config(
    page_title="PWE Compliance AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom Styling ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 50%, #3d8bc9 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
    }
    .module-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: box-shadow 0.2s;
    }
    .module-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .metric-box {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .severity-critical { background: #fee2e2; color: #991b1b; }
    .severity-high { background: #fef3c7; color: #92400e; }
    .severity-medium { background: #dbeafe; color: #1e40af; }
    .severity-low { background: #d1fae5; color: #065f46; }
    .agentic-badge { background: #ede9fe; color: #5b21b6; padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; }
    .genai-badge { background: #e0f2fe; color: #0369a1; padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size: 2.2rem;">PWE Compliance & Regulatory AI Platform</h1>
    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
        Agentic AI & Gen AI for Regulatory Change Monitoring, Obligation Analysis, Audit Preparation & Case Analytics
    </p>
    <p style="margin: 0.3rem 0 0 0; font-size: 0.85rem; opacity: 0.7;">
        Powered by OpenAI GPT-4o | LangGraph Agentic Framework | RAG-Enhanced Analytics | Claude Fallback
    </p>
</div>
""", unsafe_allow_html=True)

# --- Platform Overview ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-box">
        <h3 style="margin:0; color: #1e3a5f;">5</h3>
        <p style="margin:0; font-size:0.85rem; color: #666;">Regulatory Sources</p>
        <p style="margin:0; font-size:0.7rem; color: #999;">CPUC, FERC, NERC, CARB, EPA</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-box">
        <h3 style="margin:0; color: #1e3a5f;">4</h3>
        <p style="margin:0; font-size:0.85rem; color: #666;">AI Modules</p>
        <p style="margin:0; font-size:0.7rem; color: #999;">3 Agentic + 1 Gen AI</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-box">
        <h3 style="margin:0; color: #1e3a5f;">7</h3>
        <p style="margin:0; font-size:0.85rem; color: #666;">AI Agents</p>
        <p style="margin:0; font-size:0.7rem; color: #999;">Specialized LangGraph Agents</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-box">
        <h3 style="margin:0; color: #1e3a5f;">100%</h3>
        <p style="margin:0; font-size:0.85rem; color: #666;">Audit Trail</p>
        <p style="margin:0; font-size:0.7rem; color: #999;">Every AI decision traced</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- Module Cards ---
st.subheader("AI Modules")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    <div class="module-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h4 style="margin:0;">1. Regulatory Change Monitor</h4>
            <span class="agentic-badge">AGENTIC AI</span>
        </div>
        <p style="color:#666; margin:0.5rem 0;">
            Continuously monitors CPUC, FERC, NERC, CARB, and EPA for regulatory changes.
            Multi-step agent pipeline: Fetch → Classify → Extract Obligations → Map to Departments → Alert.
        </p>
        <p style="font-size:0.8rem; color:#999;">
            Agent: 5-node LangGraph state machine | LLM: GPT-4o
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="module-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h4 style="margin:0;">3. Audit Analysis & Preparation</h4>
            <span class="agentic-badge">AGENTIC AI</span>
        </div>
        <p style="color:#666; margin:0.5rem 0;">
            Multi-agent system with Supervisor coordinating Evidence Collector, Gap Analyzer,
            and Response Drafter agents. Produces audit-ready packages.
        </p>
        <p style="font-size:0.8rem; color:#999;">
            Agent: Supervisor + 3 Sub-Agents | LLM: GPT-4o
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown("""
    <div class="module-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h4 style="margin:0;">2. Obligation Impact Analysis</h4>
            <span class="agentic-badge">AGENTIC AI</span>
        </div>
        <p style="color:#666; margin:0.5rem 0;">
            Decomposes regulations into atomic obligations, cross-references existing requirements,
            scores impact across cost/effort/risk/timeline dimensions with executive reporting.
        </p>
        <p style="font-size:0.8rem; color:#999;">
            Agent: 4-node graph with deep scoring | LLM: GPT-4o
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="module-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h4 style="margin:0;">4. Case Analytics</h4>
            <span class="genai-badge">GEN AI</span>
        </div>
        <p style="color:#666; margin:0.5rem 0;">
            RAG-powered analysis of historical CPUC/FERC enforcement cases.
            Precedent search, trend analysis, penalty prediction, and risk assessment.
        </p>
        <p style="font-size:0.8rem; color:#999;">
            Chain: RAG + GPT-4o | Vector: In-Memory TF-IDF
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --- Architecture Diagram ---
st.subheader("Platform Architecture")

st.markdown("""
```
┌─────────────────────────────── STREAMLIT UI ──────────────────────────────┐
│  Regulatory Monitor │ Obligation Impact │ Audit Prep │ Case Analytics     │
└──────────┬──────────┴────────┬──────────┴─────┬──────┴────────┬──────────┘
           │                   │                │               │
┌──────────▼───────────────────▼────────────────▼───────────────▼──────────┐
│                    LangGraph Agent Orchestrator                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  5-Node     │  │  4-Node      │  │  Supervisor  │  │  RAG Chain   │  │
│  │  Pipeline   │  │  Impact      │  │  + 3 Agents  │  │  + Search    │  │
│  │  Agent      │  │  Graph       │  │  Multi-Agent │  │  Analytics   │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼────────────────┼─────────────────┼─────────────────┼──────────┘
          │                │                 │                 │
┌─────────▼────────────────▼─────────────────▼─────────────────▼──────────┐
│  OpenAI GPT-4o      │  Claude Sonnet    │  TF-IDF    │  SQLite/PgSQL  │
│  (Primary LLM)      │  (Fallback)       │  (Vectors) │  (Structured)  │
└─────────────────────────────────────────────────────────────────────────┘
```
""")

# --- Tech Stack ---
st.subheader("Technology Stack")
col_t1, col_t2, col_t3 = st.columns(3)

with col_t1:
    st.markdown("""
    **AI / LLM Layer**
    - OpenAI GPT-4o (primary)
    - Claude Sonnet 4.6 (fallback)
    - LangGraph (agentic orchestration)
    - Voyage Law-2 (legal embeddings)
    """)

with col_t2:
    st.markdown("""
    **Data Layer**
    - ChromaDB (vector store)
    - SQLite (structured data)
    - Regulatory web scrapers
    - Document parsers (PDF/DOCX)
    """)

with col_t3:
    st.markdown("""
    **Application Layer**
    - Streamlit (UI)
    - Python 3.11+
    - LangChain (tool framework)
    - Plotly (visualizations)
    """)

# --- Navigation ---
st.markdown("---")
st.info("Use the **sidebar navigation** to access each module, or select from the pages below.")

col_n1, col_n2, col_n3, col_n4 = st.columns(4)
with col_n1:
    st.page_link("pages/1_Regulatory_Monitor.py", label="Regulatory Monitor", icon="📡")
with col_n2:
    st.page_link("pages/2_Obligation_Impact.py", label="Obligation Impact", icon="📊")
with col_n3:
    st.page_link("pages/3_Audit_Prep.py", label="Audit Preparation", icon="📋")
with col_n4:
    st.page_link("pages/4_Case_Analytics.py", label="Case Analytics", icon="🔍")
