"""
Phase 3 stub: Knowledge Base — scrape SF docs, chunk, embed, upsert to Supabase pgvector.

TODO (Phase 3):
  - scraper.py: crawl4ai → raw HTML → markdown (local group dep)
  - chunker.py: tiktoken-based splitter, ~512 token chunks with overlap
  - embedder.py: Anthropic claude-3-haiku or Voyage API → float vectors
  - upsert.py: Supabase REST API → pgvector upsert with metadata
"""
