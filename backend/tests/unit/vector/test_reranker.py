import pytest
from src.vector.reranker import Reranker, get_reranker


def test_reranker_ranking():
    r = Reranker()
    docs = [
        {"content": "Python is a programming language"},
        {"content": "Deep learning uses neural networks"},
        {"content": "Chocolate cake needs cocoa powder"},
    ]
    ranked = r.rerank("how do neural networks work", docs, top_k=2)
    assert len(ranked) == 2
    assert "neural networks" in ranked[0]["content"]
    assert "Python" in ranked[1]["content"]
    assert ranked[0]["rerank_score"] > ranked[1]["rerank_score"]
    for d in ranked:
        print(d["rerank_score"], d["content"][:50])


def test_reranker_edge_cases():
    r = Reranker()

    # Empty list
    assert r.rerank("query", [], top_k=5) == []

    # Single document
    single = [{"content": "Deep learning uses neural networks"}]
    ranked_single = r.rerank("neural networks", single, top_k=1)
    assert len(ranked_single) == 1
    assert "rerank_score" in ranked_single[0]

    # Singleton getter
    s1 = get_reranker()
    s2 = get_reranker()
    assert s1 is s2


def test_reranker_graceful_degradation(monkeypatch):
    r = Reranker(model_name="nonexistent/fake-model")
    # Simulate failed model load
    r._model = None
    r._load_attempted = True
    assert r.is_available() is False

    docs = [{"content": "Doc 1"}, {"content": "Doc 2"}]
    res = r.rerank("query", docs, top_k=1)
    assert len(res) == 1
    assert res[0]["content"] == "Doc 1"
