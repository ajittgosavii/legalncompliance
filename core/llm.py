"""
PWE Compliance AI - LLM Client Configuration
Provides Claude (primary) and Ollama (local) LLM clients.
"""

import os
from anthropic import Anthropic
from langchain_anthropic import ChatAnthropic


def get_anthropic_client() -> Anthropic:
    """Raw Anthropic client for direct API calls."""
    return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def get_claude_sonnet() -> ChatAnthropic:
    """Claude Sonnet 4.6 — primary LLM for analysis and generation."""
    return ChatAnthropic(
        model="claude-sonnet-4-6-20250514",
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0,
        max_tokens=4096,
    )


def get_claude_opus() -> ChatAnthropic:
    """Claude Opus 4.6 — heavy reasoning for complex regulatory analysis."""
    return ChatAnthropic(
        model="claude-opus-4-6-20250610",
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0,
        max_tokens=8192,
    )


def get_local_llm():
    """Llama 3.1 8B via Ollama — classification, summarization, redaction.
    Returns None if Ollama is not available (e.g., on Streamlit Cloud).
    """
    try:
        from langchain_community.llms import Ollama
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        llm = Ollama(
            model="llama3.1:8b",
            base_url=ollama_url,
            temperature=0,
        )
        llm.invoke("ping")
        return llm
    except Exception:
        return None


def get_llm(tier: str = "sonnet") -> ChatAnthropic:
    """Get LLM by tier: 'opus', 'sonnet', or 'local'."""
    if tier == "opus":
        return get_claude_opus()
    elif tier == "local":
        local = get_local_llm()
        if local:
            return local
        return get_claude_sonnet()
    else:
        return get_claude_sonnet()
