"""Optional LangChain retrieval tests."""
import pytest
pytest.importorskip("langchain_core")

from agentops.langchain_retrieval import HashEmbeddings, retrieve_runbooks


def test_hash_embeddings_are_stable_and_normalized():
    emb = HashEmbeddings()
    a = emb.embed_query("schema drift schema error")
    b = emb.embed_query("schema drift schema error")
    assert a == b
    assert abs(sum(x*x for x in a) - 1) < 1e-6


def test_retrieves_local_runbooks():
    results = retrieve_runbooks("missing schema mapping column", k=2)
    assert results
    assert all(item["runbook_id"].startswith("RB-") for item in results)
