import re
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from rank_bm25 import BM25Okapi
from backend.app.schemas.chat import Citation
from backend.app.services.transcript_loader import TranscriptLoader

logger = logging.getLogger(__name__)

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than",
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
    "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's",
    "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd",
    "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}


def clean_tokens(text: str, filter_stopwords: bool = True) -> List[str]:
    """Tokenizes text into lowercase alphanumeric tokens, filtering stopwords."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = [w for w in cleaned.split() if len(w) > 2]
    if filter_stopwords:
        tokens = [w for w in tokens if w not in STOPWORDS]
    return tokens


class HybridRetriever:
    _instance: Optional["HybridRetriever"] = None

    def __init__(self, transcripts_dir: str = "data/transcripts", cache_dir: str = "data/index_cache"):
        self.loader = TranscriptLoader(transcripts_dir, cache_dir)
        self.chunks: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None
        self.topic_map: Dict[str, List[str]] = {}
        self.guest_names: Dict[str, str] = {}  # normalized name -> guest slug
        self.is_ready: bool = False

    @classmethod
    def get_instance(cls) -> "HybridRetriever":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.initialize()
        return cls._instance

    def initialize(self, force_refresh: bool = False):
        """Loads chunks and builds BM25 index."""
        logger.info("Initializing HybridRetriever...")
        self.chunks = self.loader.load_all_chunks(force_refresh=force_refresh)
        if not self.chunks:
            logger.warning("No chunks loaded in retriever.")
            return

        self.topic_map = self.loader.load_topics()

        # Build guest name lookup
        for c in self.chunks:
            guest = c.get("guest")
            if guest:
                self.guest_names[guest.lower()] = c.get("episode_slug", "")

        # Build BM25 index over text + guest + title
        logger.info(f"Building BM25 index for {len(self.chunks)} chunks...")
        tokenized_corpus = []
        for c in self.chunks:
            corpus_text = f"{c.get('guest', '')} {c.get('title', '')} {c.get('text', '')}"
            tokenized_corpus.append(clean_tokens(corpus_text, filter_stopwords=True))

        self.bm25 = BM25Okapi(tokenized_corpus)
        self.is_ready = True
        logger.info("HybridRetriever initialized successfully.")

    def search(
        self,
        query: str,
        top_k: int = 5,
        guest_filter: Optional[str] = None,
        min_score: float = 12.0
    ) -> Tuple[List[Citation], bool]:
        """
        Searches transcript chunks using BM25 with guest and topic boosting.
        Enforces query term coverage and confidence threshold to prevent hallucinations.
        """
        if not self.is_ready or not self.bm25:
            self.initialize()
            if not self.is_ready or not self.bm25:
                return [], False

        query_tokens = clean_tokens(query, filter_stopwords=True)
        if not query_tokens:
            return [], False

        raw_scores = self.bm25.get_scores(query_tokens)
        query_lower = query.lower()

        # Identify mentioned guests
        mentioned_slugs = set()
        for norm_guest, slug in self.guest_names.items():
            if norm_guest in query_lower:
                mentioned_slugs.add(slug)

        # Identify mentioned topics
        topic_boost_slugs = set()
        for topic, eps in self.topic_map.items():
            if topic in query_lower:
                topic_boost_slugs.update(eps)

        final_scores = []
        unique_query_set = set(query_tokens)
        num_query_tokens = len(unique_query_set)

        # Stricter term coverage required for multi-term queries
        min_required_coverage = 0.50 if num_query_tokens >= 4 else 0.33

        for idx, score in enumerate(raw_scores):
            chunk = self.chunks[idx]
            slug = chunk.get("episode_slug", "")

            # Apply guest filter if explicitly provided
            if guest_filter and guest_filter.lower() not in chunk.get("guest", "").lower():
                continue

            # Term coverage check
            chunk_tokens = set(clean_tokens(f"{chunk.get('title', '')} {chunk.get('text', '')}", filter_stopwords=True))
            overlap = len(unique_query_set.intersection(chunk_tokens))
            coverage = overlap / num_query_tokens if num_query_tokens > 0 else 0

            # Guardrail: reject chunks that don't cover sufficient query terms
            if coverage < min_required_coverage or overlap == 0:
                continue

            boosted_score = float(score) * (1.0 + coverage)

            # Boost if guest is mentioned in query
            if slug in mentioned_slugs:
                boosted_score *= 1.5

            # Boost if chunk belongs to a matched topic index
            if slug in topic_boost_slugs:
                boosted_score *= 1.25

            final_scores.append((idx, boosted_score, coverage))

        if not final_scores:
            return [], False

        # Sort by boosted score
        final_scores.sort(key=lambda x: x[1], reverse=True)
        top_matches = final_scores[:top_k]

        max_score = top_matches[0][1] if top_matches else 0.0
        has_sufficient_grounding = max_score >= min_score

        if not has_sufficient_grounding:
            return [], False

        citations: List[Citation] = []
        for idx, score, _ in top_matches:
            chunk = self.chunks[idx]
            text = chunk.get("text", "").strip()
            snippet = text[:280] + ("..." if len(text) > 280 else "")

            citations.append(Citation(
                episode_id=chunk.get("episode_slug", ""),
                guest=chunk.get("guest", "Unknown"),
                title=chunk.get("title", ""),
                youtube_url=chunk.get("youtube_url"),
                timestamp=chunk.get("timestamp", "00:00:00"),
                snippet=snippet,
                relevance_score=round(score, 2)
            ))

        return citations, has_sufficient_grounding

    def format_context_for_prompt(self, citations: List[Citation], max_chunks: int = 4) -> str:
        """Formats retrieved chunks into a prompt-ready context block."""
        if not citations:
            return "No relevant transcripts found."

        context_blocks = []
        for i, c in enumerate(citations[:max_chunks], 1):
            matching_chunk = next(
                (ch for ch in self.chunks if ch.get("episode_slug") == c.episode_id and ch.get("timestamp") == c.timestamp),
                None
            )
            full_text = matching_chunk.get("text", c.snippet) if matching_chunk else c.snippet

            block = (
                f"[Source #{i}]: Episode '{c.title}' with {c.guest} (Timestamp: {c.timestamp})\n"
                f"URL: {c.youtube_url or 'N/A'}\n"
                f"Transcript excerpt:\n{full_text}\n"
            )
            context_blocks.append(block)

        return "\n---\n".join(context_blocks)
