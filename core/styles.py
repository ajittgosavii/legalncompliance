"""
Regulatory Compliance AI - Enterprise Design System
Shared CSS and UI components for professional enterprise look.
"""

ENTERPRISE_CSS = """
<style>
    /* === GLOBAL RESET & TYPOGRAPHY === */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hide default Streamlit elements for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* === HERO HEADER === */
    .hero-banner {
        background: linear-gradient(135deg, #0a1628 0%, #1a365d 40%, #2b6cb0 100%);
        padding: 2.5rem 2.5rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(10, 22, 40, 0.3);
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-banner h1 {
        font-size: 1.85rem;
        font-weight: 700;
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.5px;
    }
    .hero-banner .subtitle {
        font-size: 1rem;
        opacity: 0.85;
        font-weight: 400;
        margin: 0;
    }
    .hero-banner .tech-badge {
        display: inline-block;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.2);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        margin-top: 0.8rem;
        font-weight: 500;
        letter-spacing: 0.3px;
    }

    /* === PAGE HEADER (for sub-pages) === */
    .page-header {
        background: linear-gradient(135deg, #0a1628 0%, #1a365d 100%);
        padding: 1.8rem 2rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(10, 22, 40, 0.2);
    }
    .page-header h1 {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
    }
    .page-header .page-desc {
        font-size: 0.9rem;
        opacity: 0.8;
        margin: 0;
    }
    .page-header .ai-type-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 0.6rem;
    }
    .badge-agentic {
        background: rgba(139, 92, 246, 0.25);
        border: 1px solid rgba(139, 92, 246, 0.5);
        color: #c4b5fd;
    }
    .badge-genai {
        background: rgba(56, 189, 248, 0.2);
        border: 1px solid rgba(56, 189, 248, 0.4);
        color: #7dd3fc;
    }

    /* === KPI METRIC CARDS === */
    .kpi-row {
        display: flex;
        gap: 1rem;
        margin: 1.2rem 0;
    }
    .kpi-card {
        flex: 1;
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem 1rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.2s;
    }
    .kpi-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transform: translateY(-1px);
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a365d;
        line-height: 1.2;
    }
    .kpi-label {
        font-size: 0.78rem;
        color: #64748b;
        font-weight: 500;
        margin-top: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-sublabel {
        font-size: 0.7rem;
        color: #94a3b8;
        margin-top: 0.15rem;
    }

    /* === MODULE CARDS === */
    .module-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin: 1.2rem 0;
    }
    .module-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.5rem;
        transition: all 0.2s;
        position: relative;
        overflow: hidden;
    }
    .module-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        border-color: #cbd5e1;
    }
    .module-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
    }
    .module-card.agentic::before { background: linear-gradient(90deg, #7c3aed, #a78bfa); }
    .module-card.genai::before { background: linear-gradient(90deg, #0284c7, #38bdf8); }

    .module-number {
        font-size: 0.7rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.4rem;
    }
    .module-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.5rem;
    }
    .module-desc {
        font-size: 0.85rem;
        color: #475569;
        line-height: 1.5;
        margin-bottom: 0.8rem;
    }
    .module-tech {
        font-size: 0.72rem;
        color: #94a3b8;
        padding-top: 0.6rem;
        border-top: 1px solid #f1f5f9;
    }

    /* === ALERT CARDS === */
    .alert-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid;
        transition: all 0.2s;
    }
    .alert-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
    .alert-critical { border-left-color: #ef4444; }
    .alert-high { border-left-color: #f59e0b; }
    .alert-medium { border-left-color: #3b82f6; }
    .alert-low { border-left-color: #10b981; }

    .alert-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.5rem;
    }
    .alert-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #0f172a;
    }
    .alert-source {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .source-cpuc { background: #ede9fe; color: #6d28d9; }
    .source-ferc { background: #dbeafe; color: #1d4ed8; }
    .source-nerc { background: #fef3c7; color: #92400e; }
    .source-carb { background: #d1fae5; color: #065f46; }
    .source-epa { background: #e0e7ff; color: #3730a3; }
    .source-phmsa { background: #fee2e2; color: #991b1b; }
    .source-cal-osha { background: #fce7f3; color: #9d174d; }

    /* === SEVERITY BADGES === */
    .severity-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .sev-critical { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
    .sev-high { background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }
    .sev-medium { background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }
    .sev-low { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }

    /* === STATUS BADGES === */
    .status-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .status-complete { background: #f0fdf4; color: #166534; }
    .status-partial { background: #fffbeb; color: #92400e; }
    .status-missing { background: #fef2f2; color: #b91c1c; }
    .status-active { background: #eff6ff; color: #1e40af; }

    /* === PROGRESS PIPELINE === */
    .pipeline-container {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 1rem 0;
    }
    .pipeline-steps {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
    }
    .pipeline-step {
        flex: 1;
        text-align: center;
        padding: 0.6rem 0.3rem;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 500;
        transition: all 0.3s;
    }
    .step-pending { background: #f1f5f9; color: #94a3b8; }
    .step-active { background: #dbeafe; color: #1e40af; box-shadow: 0 0 0 2px #3b82f6; }
    .step-done { background: #d1fae5; color: #065f46; }
    .pipeline-arrow {
        color: #cbd5e1;
        font-size: 0.8rem;
        flex-shrink: 0;
    }

    /* === SECTION HEADERS === */
    .section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
        margin: 1.5rem 0 1rem;
    }
    .section-subtext {
        font-size: 0.82rem;
        color: #64748b;
        margin-top: -0.3rem;
        margin-bottom: 1rem;
    }

    /* === DATA TABLE === */
    .data-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        overflow: hidden;
        margin: 0.8rem 0;
    }
    .data-table th {
        background: #f8fafc;
        padding: 0.7rem 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        text-align: left;
        border-bottom: 1px solid #e2e8f0;
    }
    .data-table td {
        padding: 0.65rem 1rem;
        font-size: 0.85rem;
        color: #334155;
        border-bottom: 1px solid #f1f5f9;
    }
    .data-table tr:last-child td { border-bottom: none; }
    .data-table tr:hover td { background: #f8fafc; }

    /* === READINESS GAUGE === */
    .readiness-gauge {
        text-align: center;
        padding: 1.5rem;
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
    }
    .gauge-value {
        font-size: 3rem;
        font-weight: 700;
        line-height: 1;
    }
    .gauge-ready { color: #059669; }
    .gauge-mostly { color: #d97706; }
    .gauge-gaps { color: #dc2626; }
    .gauge-label {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.3rem;
        font-weight: 500;
    }

    /* === EMPTY STATE === */
    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        background: #f8fafc;
        border: 2px dashed #e2e8f0;
        border-radius: 14px;
        margin: 1rem 0;
    }
    .empty-state-icon { font-size: 2.5rem; margin-bottom: 0.8rem; }
    .empty-state-title { font-size: 1.1rem; font-weight: 600; color: #334155; }
    .empty-state-desc { font-size: 0.85rem; color: #64748b; margin-top: 0.3rem; }

    /* === OVERRIDE STREAMLIT DEFAULTS === */
    .stExpander {
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        box-shadow: none !important;
    }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetric"] label {
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #1a365d !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1a365d, #2b6cb0) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.3px !important;
        box-shadow: 0 2px 8px rgba(26, 54, 93, 0.3) !important;
        transition: all 0.2s !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 16px rgba(26, 54, 93, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    .stSelectbox > div > div {
        border-radius: 10px !important;
    }
    div[data-testid="stSidebar"] {
        background: #0f172a !important;
    }
    div[data-testid="stSidebar"] .stMarkdown p,
    div[data-testid="stSidebar"] .stMarkdown li {
        color: #cbd5e1 !important;
    }
    div[data-testid="stSidebar"] h1, div[data-testid="stSidebar"] h2, div[data-testid="stSidebar"] h3 {
        color: white !important;
    }

    /* --- Provenance badges: a verified citation must never look like an unverified one --- */
    .badge {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .badge-verified {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #86efac;
    }
    .badge-unverified {
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #fcd34d;
    }
    .source-quote {
        border-left: 3px solid #94a3b8;
        background: #f8fafc;
        padding: 0.5rem 0.75rem;
        margin: 0.4rem 0;
        font-size: 0.85rem;
        color: #334155;
        font-style: italic;
    }
</style>
"""


def inject_styles():
    """Inject enterprise CSS into the current Streamlit page."""
    import streamlit as st
    st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)


def render_hero(title: str, subtitle: str, tech_text: str = ""):
    """Render the main hero banner."""
    import streamlit as st
    tech_html = f'<div class="tech-badge">{tech_text}</div>' if tech_text else ""
    st.markdown(f"""
    <div class="hero-banner">
        <h1>{title}</h1>
        <p class="subtitle">{subtitle}</p>
        {tech_html}
    </div>
    """, unsafe_allow_html=True)


def render_page_header(title: str, description: str, ai_type: str = "agentic"):
    """Render a sub-page header."""
    import streamlit as st
    badge_class = "badge-agentic" if ai_type == "agentic" else "badge-genai"
    badge_text = "Agentic AI" if ai_type == "agentic" else "Generative AI"
    st.markdown(f"""
    <div class="page-header">
        <h1>{title}</h1>
        <p class="page-desc">{description}</p>
        <span class="ai-type-badge {badge_class}">{badge_text}</span>
    </div>
    """, unsafe_allow_html=True)


def render_kpi_row(kpis: list[dict]):
    """Render a row of KPI cards using Streamlit columns for reliable rendering."""
    import streamlit as st
    cols = st.columns(len(kpis))
    for i, kpi in enumerate(kpis):
        with cols[i]:
            sub = f'<div class="kpi-sublabel">{kpi.get("sublabel", "")}</div>' if kpi.get("sublabel") else ""
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{kpi['value']}</div>
                <div class="kpi-label">{kpi['label']}</div>
                {sub}
            </div>""", unsafe_allow_html=True)


def render_section(title: str, subtitle: str = ""):
    """Render a section header."""
    import streamlit as st
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtext">{subtitle}</div>', unsafe_allow_html=True)


def render_pipeline(steps: list[str], active_index: int = -1):
    """Render a pipeline progress indicator using Streamlit columns."""
    import streamlit as st
    cols = st.columns(len(steps) * 2 - 1)
    col_idx = 0
    for i, step in enumerate(steps):
        if active_index < 0:
            cls = "step-pending"
        elif i < active_index:
            cls = "step-done"
        elif i == active_index:
            cls = "step-active"
        else:
            cls = "step-pending"
        with cols[col_idx]:
            st.markdown(f'<div class="pipeline-step {cls}">{step}</div>', unsafe_allow_html=True)
        col_idx += 1
        if i < len(steps) - 1:
            with cols[col_idx]:
                st.markdown('<div class="pipeline-arrow" style="text-align:center; padding-top:0.6rem; color:#cbd5e1;">&#9654;</div>', unsafe_allow_html=True)
            col_idx += 1


def render_empty_state(icon: str, title: str, description: str):
    """Render an empty state placeholder."""
    import streamlit as st
    st.markdown(f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def severity_badge(severity: str) -> str:
    """Return HTML for a severity badge."""
    cls = f"sev-{severity}"
    return f'<span class="severity-badge {cls}">{severity.upper()}</span>'


def source_badge(source: str) -> str:
    """Return HTML for a regulatory source badge."""
    cls = f"source-{source.lower().replace('/', '-')}"
    return f'<span class="alert-source {cls}">{source}</span>'


def status_badge(status: str) -> str:
    """Return HTML for a status badge."""
    cls_map = {"complete": "status-complete", "partial": "status-partial",
               "missing": "status-missing", "active": "status-active",
               "current": "status-complete", "needs_update": "status-partial",
               "draft": "status-partial"}
    cls = cls_map.get(status, "status-partial")
    return f'<span class="status-badge {cls}">{status.replace("_", " ").title()}</span>'
