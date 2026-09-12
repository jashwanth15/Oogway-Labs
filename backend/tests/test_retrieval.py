import pytest
from backend.app.services.retrieval import HybridRetriever


@pytest.fixture(scope="module")
def retriever():
    r = HybridRetriever.get_instance()
    if not r.is_ready:
        r.initialize()
    return r


def test_retriever_initialization(retriever):
    assert retriever.is_ready is True
    assert len(retriever.chunks) > 1000
    assert retriever.bm25 is not None


def test_grounded_search_rahul_vohra(retriever):
    """Verifies that queries about Superhuman/Rahul Vohra retrieve his episode with high score."""
    citations, is_grounded = retriever.search("How did Superhuman measure product market fit", top_k=5)
    assert is_grounded is True
    assert len(citations) > 0
    # Top results should include Rahul Vohra
    guest_names = [c.guest for c in citations]
    assert any("Rahul Vohra" in g for g in guest_names)
    assert citations[0].relevance_score > 10.0
    assert citations[0].episode_id != ""


def test_grounded_search_elena_verna(retriever):
    """Verifies retrieval for Elena Verna B2B PLG growth loops."""
    citations, is_grounded = retriever.search("Elena Verna B2B product led growth loops", top_k=5)
    assert is_grounded is True
    assert len(citations) > 0
    assert any("Elena Verna" in c.guest for c in citations)


def test_out_of_domain_hallucination_guardrail(retriever):
    """Verifies that an out-of-domain query triggers the hallucination guardrail."""
    # Sourdough baking is not discussed on Lenny's podcast
    citations, is_grounded = retriever.search("How to bake artisan sourdough bread with whole wheat flour", min_score=15.0)
    # Either not grounded or score is very low
    if citations:
        assert citations[0].relevance_score < 15.0 or not is_grounded
    else:
        assert is_grounded is False
