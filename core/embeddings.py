"""
PWE Compliance AI - Embedding Models
Lightweight implementation for Streamlit Cloud compatibility.
Uses in-memory TF-IDF vectorstore (no external embedding APIs needed for prototype).
"""

# Note: The vectorstore module uses built-in TF-IDF similarity search,
# so no external embedding model is needed for the prototype.
# When deploying to production with ChromaDB, uncomment the appropriate
# embedding provider below.

def get_embeddings():
    """Get embedding model. Returns None for in-memory TF-IDF mode.
    For production, configure one of the providers below.
    """
    import os

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

    # Prototype mode: vectorstore uses built-in TF-IDF, no embeddings needed
    return None
