import os
import re
import json
import yaml
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

TIMESTAMP_PATTERN = re.compile(r"\((?:(\d{1,2}):)?(\d{1,2}):(\d{2})\)")
SPEAKER_PATTERN = re.compile(r"([A-Za-z\s\.\'\-]+)\s*\((?:(\d{1,2}):)?(\d{1,2}):(\d{2})\):")


def normalize_timestamp_match(match: re.Match) -> str:
    """Normalizes matched timestamp groups into HH:MM:SS format."""
    h, m, s = match.groups()
    if h is not None:
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
    return f"00:{int(m):02d}:{int(s):02d}"


class TranscriptLoader:
    def __init__(self, transcripts_dir: str = "data/transcripts", cache_dir: str = "data/index_cache"):
        self.transcripts_dir = transcripts_dir
        self.cache_dir = cache_dir
        self.episodes_dir = os.path.join(transcripts_dir, "episodes")
        self.index_dir = os.path.join(transcripts_dir, "index")
        self.cache_file = os.path.join(cache_dir, "chunks_cache.json")
        self.topics_cache_file = os.path.join(cache_dir, "topics_cache.json")

    def load_topics(self) -> Dict[str, List[str]]:
        """Loads curated topic-to-episode mappings from data/transcripts/index."""
        if not os.path.exists(self.index_dir):
            return {}

        topic_map = {}
        for fname in os.listdir(self.index_dir):
            if not fname.endswith(".md") or fname == "README.md":
                continue
            topic_name = fname[:-3].replace("-", " ").lower()
            fpath = os.path.join(self.index_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Matches patterns like: [Guest Name](../episodes/slug/transcript.md)
                episodes = re.findall(r"\.\./episodes/([a-z0-9\-]+)/transcript\.md", content)
                if episodes:
                    topic_map[topic_name] = list(set(episodes))
            except Exception as e:
                logger.warning(f"Error reading topic file {fname}: {e}")
        return topic_map

    def parse_episode(self, slug: str) -> List[Dict[str, Any]]:
        """Parses a single episode's transcript.md into metadata-enriched chunks."""
        file_path = os.path.join(self.episodes_dir, slug, "transcript.md")
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return []

        parts = content.split("---")
        metadata: Dict[str, Any] = {}
        body = content

        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
            except Exception:
                # Fallback manual extraction
                pass
            body = "---".join(parts[2:]).strip()

        raw_guest = metadata.get("guest") or slug.replace("-", " ").title()
        guest = re.sub(r"\s+2\.0$", "", str(raw_guest)).strip()
        title = metadata.get("title") or f"Conversation with {guest}"
        youtube_url = metadata.get("youtube_url")
        keywords = metadata.get("keywords") or []

        # Split transcript into paragraphs
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        chunks: List[Dict[str, Any]] = []
        current_text = []
        current_length = 0
        current_timestamp = None
        chunk_idx = 0

        for para in paragraphs:
            # Check for timestamp
            ts_match = TIMESTAMP_PATTERN.search(para)
            if ts_match and not current_timestamp:
                current_timestamp = normalize_timestamp_match(ts_match)

            current_text.append(para)
            current_length += len(para.split())

            # Chunks of ~350 - 500 words
            if current_length >= 350:
                chunk_id = f"{slug}_c{chunk_idx}"
                full_chunk_text = "\n\n".join(current_text)
                chunks.append({
                    "chunk_id": chunk_id,
                    "episode_slug": slug,
                    "guest": guest,
                    "title": title,
                    "youtube_url": youtube_url,
                    "timestamp": current_timestamp or "00:00:00",
                    "keywords": keywords,
                    "text": full_chunk_text
                })
                chunk_idx += 1
                # Small 1-paragraph overlap
                current_text = current_text[-1:]
                current_length = len(current_text[0].split()) if current_text else 0
                current_timestamp = None

        if current_text:
            chunk_id = f"{slug}_c{chunk_idx}"
            chunks.append({
                "chunk_id": chunk_id,
                "episode_slug": slug,
                "guest": guest,
                "title": title,
                "youtube_url": youtube_url,
                "timestamp": current_timestamp or "00:00:00",
                "keywords": keywords,
                "text": "\n\n".join(current_text)
            })

        return chunks

    def load_all_chunks(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Loads all episode chunks, utilizing disk cache if available."""
        os.makedirs(self.cache_dir, exist_ok=True)

        if not force_refresh and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cached_chunks = json.load(f)
                logger.info(f"Loaded {len(cached_chunks)} transcript chunks from cache.")
                return cached_chunks
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}. Reindexing...")

        logger.info(f"Indexing transcripts from {self.episodes_dir}...")
        if not os.path.exists(self.episodes_dir):
            logger.error(f"Episodes directory not found: {self.episodes_dir}")
            return []

        all_chunks: List[Dict[str, Any]] = []
        episode_slugs = [d for d in os.listdir(self.episodes_dir) if os.path.isdir(os.path.join(self.episodes_dir, d))]

        for slug in episode_slugs:
            chunks = self.parse_episode(slug)
            all_chunks.extend(chunks)

        logger.info(f"Successfully processed {len(episode_slugs)} episodes into {len(all_chunks)} chunks.")

        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(all_chunks, f, ensure_ascii=False)
            logger.info(f"Saved chunks cache to {self.cache_file}.")
        except Exception as e:
            logger.error(f"Failed to write cache: {e}")

        # Also save topic index
        topics = self.load_topics()
        try:
            with open(self.topics_cache_file, "w", encoding="utf-8") as f:
                json.dump(topics, f, ensure_ascii=False)
        except Exception:
            pass

        return all_chunks
