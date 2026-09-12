# Agent Execution Log: Discovery, Architecture & Core Backend

**Agent**: Antigravity (Google DeepMind)
**Date**: September 12, 2026
**Target**: The Lenny Growth Assistant - Forward Deployed Engineer Assessment

---

## 1. Initial Assessment & Ingestion Setup

### Action
- Extracted and analyzed `assignment.docx` to extract all client requirements, deliverables, and evaluation criteria.
- Cloned Lenny's Podcast transcripts repository (`ChatPRD/lennys-podcast-transcripts`) containing 303 episodes and 89 topic indexes into `data/transcripts/`.

### Architecture Decisions
- Sourced YAML frontmatter (`guest`, `title`, `youtube_url`, `publish_date`, `keywords`) from `transcript.md` files.
- Built `TranscriptLoader` to parse episode bodies, extracting timestamped speaker turns into semantic chunks (~350–500 words).
- Built high-performance local disk caching into `data/index_cache/chunks_cache.json`.
- Result: **15,251 chunks parsed across 303 episodes**; cache loads in **0.28 seconds**.

---

## 2. Failed Attempt & Correction: BM25 Term Leakage & Hallucination Guardrail

### The Failure
During initial automated retrieval testing with pytest:
- Test: `test_out_of_domain_hallucination_guardrail`
- Query: `"How to bake artisan sourdough bread with whole wheat flour"`
- Expected Result: Refusal / no grounded match.
- Actual Result: Returned `sam-schillace` with high score `30.39`!
  ```
  FAILED backend/tests/test_retrieval.py::test_out_of_domain_hallucination_guardrail
  assert (30.39 < 15.0 or not True)
  ```

### Root Cause Analysis
1. The tokenization function did not filter English stopwords.
2. In tech/growth transcripts, terms like `"bread"` and `"wheat"` appeared in an offhand analogy in Sam Schillace's episode. Because these words are extremely rare in the corpus, their BM25 Inverse Document Frequency (IDF) was extraordinarily high!
3. Matching only 2 rare words ("bread", "wheat") generated a score of 30+ even though none of the primary query words (`bake`, `artisan`, `sourdough`, `flour`) were present.

### How We Corrected It
1. Implemented standard English stopwords filtering in `clean_tokens()`.
2. Implemented strict **Query Term Coverage Filtering**:
   ```python
   min_required_coverage = 0.50 if num_query_tokens >= 4 else 0.33
   if coverage < min_required_coverage or overlap == 0:
       continue
   ```
3. Chunks must contain at least 50% of the distinct content keywords in the query to qualify as grounded evidence.
4. Rerun of tests: `test_out_of_domain_hallucination_guardrail` **PASSED**! Out-of-domain queries now trigger the zero-hallucination guardrail reliably.
