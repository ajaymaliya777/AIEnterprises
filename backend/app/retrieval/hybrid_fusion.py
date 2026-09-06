import logging
from typing import List, Dict, Any, Tuple
from app.config import settings

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    dense_results: List[Tuple[str, float, Dict[str, Any]]],
    sparse_results: List[Tuple[str, float, Dict[str, Any]]],
    k: int = None,
    vector_weight: float = None,
    lexical_weight: float = None,
    top_k: int = 20
) -> List[Dict[str, Any]]:
    """
    Reciprocal Rank Fusion (RRF) algorithm combining dense vector and sparse keyword search.
    RRF Score = sum(weight / (k + rank))
    Returns merged candidates sorted by descending RRF score.
    """
    if k is None:
        k = settings.RRF_K
    if vector_weight is None:
        vector_weight = settings.RRF_VECTOR_WEIGHT
    if lexical_weight is None:
        lexical_weight = settings.RRF_LEXICAL_WEIGHT

    scores: Dict[str, float] = {}
    metadata_map: Dict[str, Dict[str, Any]] = {}
    dense_scores: Dict[str, float] = {}
    sparse_scores: Dict[str, float] = {}

    # 1. Process Dense Results
    for rank, (chunk_id, sim_score, meta) in enumerate(dense_results):
        dense_scores[chunk_id] = sim_score
        metadata_map[chunk_id] = meta
        rrf_contrib = vector_weight / (k + rank + 1)
        scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_contrib

    # 2. Process Sparse Results
    for rank, (chunk_id, bm25_score, meta) in enumerate(sparse_results):
        sparse_scores[chunk_id] = bm25_score
        if chunk_id not in metadata_map:
            metadata_map[chunk_id] = meta
        rrf_contrib = lexical_weight / (k + rank + 1)
        scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_contrib

    # 3. Sort candidates by fused score
    sorted_chunk_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

    fused_results = []
    for cid in sorted_chunk_ids[:top_k]:
        fused_results.append({
            "chunk_id": cid,
            "hybrid_score": float(scores[cid]),
            "dense_score": dense_scores.get(cid),
            "sparse_score": sparse_scores.get(cid),
            "metadata": metadata_map.get(cid, {})
        })

    logger.info(f"RRF fusion evaluated {len(scores)} unique chunks into top-{len(fused_results)} candidates.")
    return fused_results
