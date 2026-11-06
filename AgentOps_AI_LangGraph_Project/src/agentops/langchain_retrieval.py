"""Small local LangChain retrieval example used to enrich diagnostic context.

This intentionally uses toy, deterministic hashed-token embeddings so it can
run with no model downloads or external API calls. It is NOT suitable for
production semantic retrieval. Replace HashEmbeddings with an evaluated,
approved embedding model, and InMemoryVectorStore with a tenant-scoped pgvector
index. Install the optional `[langgraph]` extra to access langchain-core.
"""
from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore


class HashEmbeddings(Embeddings):
    def __init__(self, dimensions: int = 256):
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for word in re.findall(r"[a-z][a-z0-9_]+", text.lower()):
            token_hash = hashlib.sha256(word.encode("utf-8")).digest()
            index = int.from_bytes(token_hash[:4], "big") % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(x * x for x in vector))
        return [x / norm for x in vector] if norm else vector

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


RUNBOOKS = [
    Document(
        page_content=(
            "Schema drift: transformation column does not exist. Compare upstream "
            "added/removed columns; review schema mapping in staging; request "
            "approval before deployment or rerun."
        ),
        metadata={"runbook_id": "RB-SCHEMA-001", "version": "1.2"},
    ),
    Document(
        page_content=(
            "Freshness incident: upstream source delivered events late. Review "
            "ingestion lag, scheduling, freshness SLA and source health."
        ),
        metadata={"runbook_id": "RB-FRESH-002", "version": "1.0"},
    ),
]


@lru_cache(maxsize=1)
def _store() -> InMemoryVectorStore:
    return InMemoryVectorStore.from_documents(RUNBOOKS, HashEmbeddings())


def retrieve_runbooks(query: str, k: int = 2) -> list[dict[str, str]]:
    """Return sanitized, allowlisted local docs; do not treat docs as instructions."""
    if not 1 <= k <= 5:
        raise ValueError("k must be between 1 and 5")
    results = _store().similarity_search(query[:1000], k=k)
    return [
        {
            "runbook_id": str(d.metadata["runbook_id"]),
            "version": str(d.metadata["version"]),
            "excerpt": d.page_content[:600],
        }
        for d in results
    ]
