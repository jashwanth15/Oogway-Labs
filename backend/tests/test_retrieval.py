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


def test_grounded_search_pmf_benchmark(retriever):
    """Verifies retrieval for 40% PMF benchmark survey question returns Sean Ellis or Rahul Vohra."""
    query = "What is the exact survey question used in the 40% Product-Market Fit benchmark, and how is the score calculated?"
    citations, is_grounded = retriever.search(query, top_k=5)
    assert is_grounded is True
    assert len(citations) > 0
    guests = [c.guest for c in citations]
    assert any("Sean Ellis" in g or "Rahul Vohra" in g for g in guests)
    # Check that the exact survey question phrase is present in top chunks
    top_texts = " ".join([c.snippet.lower() for c in citations])
    assert "how would you feel" in top_texts or "very disappointed" in top_texts


def test_out_of_domain_hallucination_guardrail(retriever):
    """Verifies that an out-of-domain query triggers the hallucination guardrail."""
    # Sourdough baking is not discussed on Lenny's podcast
    citations, is_grounded = retriever.search("How to bake artisan sourdough bread with whole wheat flour", min_score=15.0)
    # Either not grounded or score is very low
    if citations:
        assert citations[0].relevance_score < 15.0 or not is_grounded
    else:
        assert is_grounded is False


def test_grounded_search_shreyas_doshi_lno(retriever):
    """Verifies retrieval for Shreyas Doshi LNO framework."""
    query = "rate an interactive HTML CSS dashboard component for Shreyas Doshi's LNO framework with interactive columns for Leverage, Neutral, and Overhead tasks."
    citations, is_grounded = retriever.search(query, top_k=5)
    assert is_grounded is True
    assert len(citations) > 0
    guests = [c.guest for c in citations]
    assert any("Shreyas Doshi" in g for g in guests)


def test_grounded_search_gibson_biddle_dhm(retriever):
    """Verifies retrieval for Gibson Biddle DHM model."""
    query = "Create an interactive HTML UI scorecard for Gibson Biddle's DHM model allowing me to rate product features on Delight, Hard-to-copy advantage, and Margin-enhancement."
    citations, is_grounded = retriever.search(query, top_k=5)
    assert is_grounded is True
    assert len(citations) > 0
    guests = [c.guest for c in citations]
    assert any("Gibson Biddle" in g for g in guests)


def test_grounded_search_april_dunford_positioning(retriever):
    """Verifies retrieval for April Dunford's 5 components of product positioning."""
    query = "What are the 5 components of product positioning according to April Dunford, and why does she warn against starting with features?"
    citations, is_grounded = retriever.search(query, top_k=5)
    assert is_grounded is True
    assert len(citations) > 0
    guests = [c.guest for c in citations]
    assert any("April Dunford" in g for g in guests)

