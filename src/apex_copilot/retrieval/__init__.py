"""
Phase 3 stub: Retrieval — embed query, pgvector search, optional rerank.

TODO (Phase 3):
  - embed_query(text: str) -> list[float]: call embedding model
  - search(query_vec, top_k=5) -> list[Chunk]: pgvector cosine similarity
  - rerank(chunks, query) -> list[Chunk]: optional cross-encoder or Claude rerank
"""
from src.review_core.models import Finding


def retrieve_context(findings: list[Finding]) -> list[str]:
    """
    Phase 3: retrieve relevant SF doc chunks for given findings.
    Phase 1-2: returns empty list (no KB yet).
    """
    # TODO (Phase 3): embed finding messages, search pgvector, return top chunks
    return []
