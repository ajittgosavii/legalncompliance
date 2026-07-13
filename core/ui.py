"""
Shared UI helpers — industry switcher, secrets loading, provenance and review-gate banners.

Every page calls bootstrap() first. It loads API keys, restores the selected industry
domain into the process environment (so the agent graphs pick it up), and renders the
sidebar with the industry switcher.
"""

import os
import streamlit as st

from core.domains import DOMAIN_PACKS, DOMAIN_LABELS, get_domain, DEFAULT_DOMAIN


def load_secrets() -> None:
    """Promote Streamlit secrets to environment variables for the LLM clients."""
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "VOYAGE_API_KEY"):
        try:
            if key in st.secrets:
                os.environ[key] = st.secrets[key]
        except Exception:
            # No secrets.toml configured (local dev) — fall back to the real environment.
            pass


def _init_domain() -> str:
    """Seed session state BEFORE the widget is created.

    Streamlit forbids writing st.session_state[k] once a widget owns key k, so the seed and
    the post-widget read must be separate: seed here, and afterwards only ever *read* the
    widget's value and mirror it into the environment (which the agent graphs read).
    """
    key = st.session_state.get("active_domain", DEFAULT_DOMAIN)
    if key not in DOMAIN_PACKS:
        key = DEFAULT_DOMAIN
    if "active_domain" not in st.session_state:
        st.session_state["active_domain"] = key
    os.environ["ACTIVE_DOMAIN"] = key
    return key


def _publish_domain() -> str:
    """Read the widget's value and publish it to the environment for the agents. Read-only."""
    key = st.session_state.get("active_domain", DEFAULT_DOMAIN)
    if key not in DOMAIN_PACKS:
        key = DEFAULT_DOMAIN
    os.environ["ACTIVE_DOMAIN"] = key
    return key


def render_sidebar(show_nav: bool = True) -> dict:
    """Render the sidebar: navigation, industry switcher, platform info. Returns the active pack."""
    keys = list(DOMAIN_PACKS)
    _init_domain()

    with st.sidebar:
        if show_nav:
            st.markdown("### Navigation")
            st.page_link("app.py", label="Dashboard", icon="🏠")
            st.page_link("pages/1_Regulatory_Monitor.py", label="Regulatory Monitor", icon="📡")
            st.page_link("pages/2_Obligation_Impact.py", label="Obligation Impact", icon="📊")
            st.page_link("pages/3_Audit_Prep.py", label="Audit Preparation", icon="📋")
            st.page_link("pages/4_Case_Analytics.py", label="Case Analytics", icon="🔍")
            st.markdown("---")

        st.markdown("### Industry")
        st.selectbox(
            "Active domain pack",
            keys,
            format_func=lambda k: DOMAIN_LABELS[k],
            key="active_domain",
            help=(
                "The same seven agents serve every industry. Switching the pack swaps the regulators, "
                "departments, obligation register, evidence repository and case history — no agent "
                "code changes."
            ),
        )
        pack = get_domain(_publish_domain())
        st.caption(f"**{pack['company_full']}**")
        st.caption(pack["vertical"])

        st.markdown("---")
        st.markdown("##### Platform")
        st.markdown(
            f"""
            - **LLM**: GPT-4o (Claude failover)
            - **Framework**: LangGraph
            - **Agents**: 7 specialized
            - **Regulators**: {len(pack['regulators'])}
            """
        )
        configured = bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
        st.markdown(f"**API**: {'🟢 Connected' if configured else '🔴 Not configured'}")

    return pack


def bootstrap(show_nav: bool = True) -> dict:
    """Standard page setup. Returns the active domain pack."""
    load_secrets()
    return render_sidebar(show_nav=show_nav)


def require_llm() -> None:
    """Stop the page with a clear message if no LLM provider is configured."""
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        st.error(
            "No LLM credentials configured. Set OPENAI_API_KEY (and optionally ANTHROPIC_API_KEY "
            "for automatic failover) in Streamlit Cloud Secrets, or in your local .env."
        )
        st.stop()


def render_review_gate() -> None:
    """The human-in-the-loop gate. Compliance output is decision support, never a determination."""
    st.warning(
        "**Human review required.** This output is AI-generated decision support, not a compliance "
        "determination. Every obligation, gap and drafted response must be reviewed and signed off by "
        "qualified personnel before it is relied upon, and nothing here may be submitted to a regulator "
        "without that sign-off."
    )


def render_data_provenance() -> None:
    """Be explicit that the demo corpora are synthetic. Never let a viewer assume otherwise."""
    st.caption(
        "Data provenance: the regulations, evidence documents and enforcement cases in this "
        "demonstration are **illustrative and synthetic** — realistic in structure and vocabulary, but "
        "not verified records. In production these are replaced by live regulator ingestion and the "
        "organisation's own document systems."
    )


def citation_badge(ob: dict) -> str:
    """Render the provenance state of an extracted obligation.

    An obligation whose quote could not be matched against the source is NOT presented as
    equivalent to one that was. That distinction is the whole point of the provenance check.
    """
    if ob.get("citation_verified"):
        return '<span class="badge badge-verified">✓ Citation verified</span>'
    if ob.get("source_quote"):
        return '<span class="badge badge-unverified">⚠ Quote not found in source — verify manually</span>'
    return '<span class="badge badge-unverified">⚠ No source citation — verify manually</span>'
