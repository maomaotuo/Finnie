"""One cached FAISS store with configurable metadata-filtered retrievers."""
from functools import lru_cache
from math import isfinite
from urllib.parse import urlparse

from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnableLambda
from src.core.config import ROOT, option
from src.rag.embeddings import get_embeddings

VECTORSTORE_PATH = ROOT / "src/rag/faiss_index"


@lru_cache(maxsize=1)
def get_vectorstore():
    """Load the trusted local index once for all specialists and filters."""
    return FAISS.load_local(
        str(VECTORSTORE_PATH),
        get_embeddings(),
        # FAISS stores document metadata in pickle. Load the project’s trusted index here.
        allow_dangerous_deserialization=True,
    )


def metadata_filter(category=None, preferred_categories=(), source_domains=()):
    """Build a predicate; category constraints and domain constraints intersect."""
    def matches(metadata):
        document_category = metadata.get("category", "")
        if category and document_category != category:
            return False
        if preferred_categories and document_category.lower() not in preferred_categories:
            return False
        if source_domains:
            host = (urlparse(metadata.get("source_url", "")).hostname or "").lower()
            if not any(host == domain or host.endswith("." + domain)
                       for domain in source_domains):
                return False
        return True
    return matches


@lru_cache(maxsize=32)
def get_retriever(category=None, *, preferred_categories=(), source_domains=()):
    """Create a search view over the shared index; no separate index is built."""
    search_kwargs = {"k": int(option("retrieval_k", 5))}
    max_distance = float(option("retrieval_max_distance", 0.90))
    if not isfinite(max_distance) or max_distance < 0:
        raise ValueError("retrieval_max_distance must be a finite non-negative number")
    if preferred_categories or source_domains:
        search_kwargs.update(
            filter=metadata_filter(category, preferred_categories, source_domains),
            fetch_k=100,
        )
    elif category:
        search_kwargs.update(filter={"category": category}, fetch_k=100)
    # Each search view applies its own filters over the same cached index.
    store = get_vectorstore()

    def search(query):
        # Distances belong to this query. Copy each document so the shared index
        # keeps its original metadata for other conversations.
        return [
            document.model_copy(update={
                "metadata": {**document.metadata, "faiss_distance": float(distance)}
            })
            for document, distance in store.similarity_search_with_score(query, **search_kwargs)
            if distance <= max_distance
        ]

    return RunnableLambda(search)
