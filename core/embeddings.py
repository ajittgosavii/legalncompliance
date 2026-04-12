"""
PG&E Compliance AI - Embedding Models
Voyage Law-2 for legal/regulatory text, with OpenAI fallback.
"""

import os
from langchain_core.embeddings import Embeddings


def get_embeddings() -> Embeddings:
    """Get the best available embedding model.
    Priority: Voyage Law-2 > OpenAI text-embedding-3-small
    """
    voyage_key = os.getenv("VOYAGE_API_KEY")
    if voyage_key:
        try:
            from langchain_voyageai import VoyageAIEmbeddings
            return VoyageAIEmbeddings(
                voyage_api_key=voyage_key,
                model="voyage-law-2",
            )
        except ImportError:
            pass

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                openai_api_key=openai_key,
                model="text-embedding-3-small",
            )
        except ImportError:
            pass

    # Fallback: HuggingFace local embeddings (free, no API key)
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
