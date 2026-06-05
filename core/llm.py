"""
Regulatory Compliance AI - LLM Client Configuration
Primary: OpenAI GPT-4o (cost-effective for demo)
Fallback: Claude Sonnet 4.6 (higher accuracy for regulatory text)

If an ANTHROPIC_API_KEY is configured alongside OPENAI_API_KEY, the primary
client automatically fails over to Claude at *runtime* whenever OpenAI errors
(invalid/expired key -> 401, rate limit -> 429, outage). If only one provider's
key is present, that provider is used directly.
"""

import os

# Current model IDs (kept in one place so they're easy to bump).
OPENAI_PRIMARY_MODEL = "gpt-4o"
OPENAI_MINI_MODEL = "gpt-4o-mini"
CLAUDE_SONNET_MODEL = "claude-sonnet-4-6"
CLAUDE_OPUS_MODEL = "claude-opus-4-8"


def _has_openai() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _has_anthropic() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _build_openai(model: str = OPENAI_PRIMARY_MODEL, max_tokens: int = 4096):
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
        max_tokens=max_tokens,
    )


def _build_claude(model: str = CLAUDE_SONNET_MODEL, max_tokens: int = 4096):
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model=model,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0,
        max_tokens=max_tokens,
    )


def get_openai_primary():
    """GPT-4o — primary LLM for the demo (cost-effective).

    When an ANTHROPIC_API_KEY is also configured, returns a runnable that
    automatically falls over to Claude Sonnet if the OpenAI call raises (e.g.
    the 401 invalid_api_key that crashes the pipeline when the OpenAI key is
    revoked). With no OpenAI key at all, Claude is used directly.
    """
    if _has_openai():
        primary = _build_openai()
        if _has_anthropic():
            return primary.with_fallbacks([_build_claude()])
        return primary
    if _has_anthropic():
        return _build_claude()
    raise RuntimeError(
        "No LLM credentials configured. Set OPENAI_API_KEY (and optionally "
        "ANTHROPIC_API_KEY for automatic failover) in Streamlit Cloud Secrets."
    )


def get_openai_mini():
    """GPT-4o-mini — lightweight tasks (classification, summaries).

    Falls over to Claude Sonnet when Anthropic is configured; falls back to
    Claude as primary when no OpenAI key is present.
    """
    if _has_openai():
        primary = _build_openai(model=OPENAI_MINI_MODEL)
        if _has_anthropic():
            return primary.with_fallbacks([_build_claude()])
        return primary
    if _has_anthropic():
        return _build_claude()
    raise RuntimeError(
        "No LLM credentials configured. Set OPENAI_API_KEY (and optionally "
        "ANTHROPIC_API_KEY for automatic failover) in Streamlit Cloud Secrets."
    )


def get_claude_sonnet():
    """Claude Sonnet 4.6 — fallback for high-accuracy regulatory analysis."""
    try:
        if _has_anthropic():
            return _build_claude(model=CLAUDE_SONNET_MODEL)
    except Exception:
        pass
    # If Anthropic not available, fall back to OpenAI.
    return get_openai_primary()


def get_claude_opus():
    """Claude Opus 4.8 — heavy reasoning. Falls back to GPT-4o for demo."""
    try:
        if _has_anthropic():
            return _build_claude(model=CLAUDE_OPUS_MODEL, max_tokens=8192)
    except Exception:
        pass
    # Fallback to GPT-4o.
    return get_openai_primary()


def get_llm(tier: str = "primary"):
    """Get LLM by tier.

    Tiers:
      'primary'  — GPT-4o (default, cost-effective)
      'mini'     — GPT-4o-mini (lightweight tasks)
      'advanced' — Claude Sonnet (high-accuracy fallback)
      'opus'     — Claude Opus (complex reasoning, falls back to GPT-4o)
    """
    if tier == "opus":
        return get_claude_opus()
    elif tier == "advanced":
        return get_claude_sonnet()
    elif tier == "mini":
        return get_openai_mini()
    else:
        return get_openai_primary()
