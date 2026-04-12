"""
PWE Compliance AI - LLM Client Configuration
Primary: OpenAI GPT-4o (cost-effective for demo)
Fallback: Claude Sonnet 4.6 (higher accuracy for regulatory text)
"""

import os


def get_openai_primary():
    """GPT-4o — primary LLM for demo (cost-effective)."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model="gpt-4o",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
        max_tokens=4096,
    )


def get_openai_mini():
    """GPT-4o-mini — lightweight tasks (classification, summaries)."""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model="gpt-4o-mini",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
        max_tokens=4096,
    )


def get_claude_sonnet():
    """Claude Sonnet 4.6 — fallback for high-accuracy regulatory analysis."""
    try:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-sonnet-4-6-20250514",
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0,
            max_tokens=4096,
        )
    except Exception:
        # If Anthropic not available, fall back to OpenAI
        return get_openai_primary()


def get_claude_opus():
    """Claude Opus 4.6 — heavy reasoning. Falls back to GPT-4o for demo."""
    try:
        from langchain_anthropic import ChatAnthropic
        key = os.getenv("ANTHROPIC_API_KEY")
        if key:
            return ChatAnthropic(
                model="claude-opus-4-6-20250610",
                anthropic_api_key=key,
                temperature=0,
                max_tokens=8192,
            )
    except Exception:
        pass
    # Fallback to GPT-4o
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
