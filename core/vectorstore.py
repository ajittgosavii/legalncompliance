"""
PWE Compliance AI - Vector Store (ChromaDB)
Manages collections for regulatory documents, obligations, cases.
"""

import os
import chromadb
from langchain_chroma import Chroma
from core.embeddings import get_embeddings

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")

# Collection names
COLLECTION_REGULATIONS = "pwe_regulations"
COLLECTION_OBLIGATIONS = "pwe_obligations"
COLLECTION_CASES = "pwe_cases"
COLLECTION_AUDIT = "pwe_audit_evidence"


def get_chroma_client() -> chromadb.PersistentClient:
    """Get persistent ChromaDB client."""
    return chromadb.PersistentClient(path=CHROMA_DIR)


def get_vectorstore(collection_name: str = COLLECTION_REGULATIONS) -> Chroma:
    """Get a LangChain Chroma vectorstore for the given collection."""
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_DIR,
    )


def add_documents(collection_name: str, documents: list, metadatas: list[dict] | None = None):
    """Add documents to a ChromaDB collection."""
    store = get_vectorstore(collection_name)
    store.add_texts(texts=documents, metadatas=metadatas)
    return len(documents)


def search_documents(collection_name: str, query: str, k: int = 5) -> list:
    """Semantic search across a collection."""
    store = get_vectorstore(collection_name)
    results = store.similarity_search_with_relevance_scores(query, k=k)
    return results


def get_collection_stats() -> dict:
    """Get document counts for all collections."""
    client = get_chroma_client()
    stats = {}
    for name in [COLLECTION_REGULATIONS, COLLECTION_OBLIGATIONS, COLLECTION_CASES, COLLECTION_AUDIT]:
        try:
            col = client.get_collection(name)
            stats[name] = col.count()
        except Exception:
            stats[name] = 0
    return stats
