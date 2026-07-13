"""
Regulatory Compliance AI - Vector Store
In-memory vector search for Streamlit Cloud compatibility.
Uses simple TF-IDF similarity when ChromaDB is unavailable (Python 3.14 protobuf issue).
"""

import os
import re
import math
from collections import Counter

# Collection names
COLLECTION_REGULATIONS = "pge_regulations"
COLLECTION_OBLIGATIONS = "pge_obligations"
COLLECTION_CASES = "pge_cases"
COLLECTION_AUDIT = "pge_audit_evidence"

# --- In-memory vector store (Streamlit Cloud compatible) ---
# Stores documents as plain text with TF-IDF-based similarity search.
# No external dependencies — works on any Python version.

_store: dict[str, list[dict]] = {}


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r'\b\w+\b', text.lower())


def _tfidf_similarity(query_tokens: list[str], doc_tokens: list[str]) -> float:
    """Compute a simple TF-IDF cosine-like similarity score."""
    if not query_tokens or not doc_tokens:
        return 0.0
    query_counts = Counter(query_tokens)
    doc_counts = Counter(doc_tokens)
    # Intersection terms
    common = set(query_counts.keys()) & set(doc_counts.keys())
    if not common:
        return 0.0
    # Simple dot product / magnitude
    dot = sum(query_counts[t] * doc_counts[t] for t in common)
    mag_q = math.sqrt(sum(v * v for v in query_counts.values()))
    mag_d = math.sqrt(sum(v * v for v in doc_counts.values()))
    if mag_q == 0 or mag_d == 0:
        return 0.0
    return dot / (mag_q * mag_d)


class SimpleDocument:
    """Lightweight document class matching LangChain Document interface."""
    def __init__(self, page_content: str, metadata: dict | None = None):
        self.page_content = page_content
        self.metadata = metadata or {}


def add_documents(collection_name: str, documents: list[str], metadatas: list[dict] | None = None):
    """Add documents to the in-memory store."""
    if collection_name not in _store:
        _store[collection_name] = []
    for i, doc_text in enumerate(documents):
        meta = metadatas[i] if metadatas and i < len(metadatas) else {}
        _store[collection_name].append({
            "text": doc_text,
            "tokens": _tokenize(doc_text),
            "metadata": meta,
        })
    return len(documents)


def search_documents(collection_name: str, query: str, k: int = 5) -> list[tuple]:
    """Semantic search using TF-IDF similarity.
    Returns list of (SimpleDocument, score) tuples.
    """
    if collection_name not in _store or not _store[collection_name]:
        return []

    query_tokens = _tokenize(query)
    scored = []
    for entry in _store[collection_name]:
        score = _tfidf_similarity(query_tokens, entry["tokens"])
        if score > 0:
            scored.append((entry, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    results = []
    for entry, score in scored[:k]:
        doc = SimpleDocument(page_content=entry["text"], metadata=entry["metadata"])
        results.append((doc, score))
    return results


def get_collection_stats() -> dict:
    """Get document counts for all collections."""
    stats = {}
    for name in [COLLECTION_REGULATIONS, COLLECTION_OBLIGATIONS, COLLECTION_CASES, COLLECTION_AUDIT]:
        stats[name] = len(_store.get(name, []))
    return stats
