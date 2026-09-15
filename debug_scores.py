import sys
from backend.app.services.retrieval import HybridRetriever

def debug_scores(query: str):
    r = HybridRetriever.get_instance()
    r.initialize()
    print(f"\nQuery: '{query}'")
    print("-" * 60)
    
    from backend.app.services.retrieval import clean_tokens, DIRECTIVE_WORDS
    query_tokens = clean_tokens(query, filter_stopwords=True)
    content_tokens = [w for w in query_tokens if w not in DIRECTIVE_WORDS]
    tokens_to_search = content_tokens if len(content_tokens) >= 2 else query_tokens
    
    raw_scores = r.bm25.get_scores(tokens_to_search)
    top_indices = sorted(range(len(raw_scores)), key=lambda i: raw_scores[i], reverse=True)[:5]
    
    for rank, idx in enumerate(top_indices):
        chunk = r.chunks[idx]
        print(f"  Rank {rank+1}: score={raw_scores[idx]:.2f} | guest={chunk.get('guest','?')} | title={chunk.get('title','?')[:60]}")
    
    citations, is_grounded = r.search(query)
    print(f"\n  is_grounded={is_grounded}, citations_returned={len(citations)}")
    if citations:
        print(f"  Top citation relevance_score={citations[0].relevance_score}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    debug_scores("What are the best stocks to invest in for 2026?")
    debug_scores("Give me medical advice for treating diabetes")
    debug_scores("What are the 5 components of product positioning according to April Dunford?")
