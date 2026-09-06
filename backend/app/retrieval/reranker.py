import logging
from typing import List, Dict, Any
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)

_RERANKER_MODEL = None
_RERANKER_INITIALIZED = False


def get_reranker_model():
    global _RERANKER_MODEL, _RERANKER_INITIALIZED
    if _RERANKER_INITIALIZED:
        return _RERANKER_MODEL

    _RERANKER_INITIALIZED = True
    try:
        from sentence_transformers import CrossEncoder
        logger.info(f"Loading Cross-Encoder model: {settings.RERANKER_MODEL_NAME}")
        _RERANKER_MODEL = CrossEncoder(settings.RERANKER_MODEL_NAME)
        logger.info("Cross-Encoder model loaded successfully.")
    except Exception as e:
        logger.warning(f"Could not load Cross-Encoder model {settings.RERANKER_MODEL_NAME}: {e}. Running in fallback scoring mode.")
        _RERANKER_MODEL = None

    return _RERANKER_MODEL


def sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-x)))


class CrossEncoderReranker:
    """
    Cross-Encoder Reranker using transformer joint cross-attention.
    Significantly reduces hallucination and boosts Precision@K over bi-encoders.
    """

    def __init__(self):
        pass

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate dictionaries from hybrid retrieval.
        Each candidate must contain 'content' or 'metadata.content'.
        """
        if not candidates:
            return []

        # Prepare pairs
        pairs = []
        for cand in candidates:
            text = cand.get("content") or cand.get("metadata", {}).get("content", "")
            pairs.append([query, text])

        model = get_reranker_model()

        if model is not None:
            try:
                raw_scores = model.predict(pairs)
                # Map raw logits to [0, 1] using sigmoid
                if isinstance(raw_scores, (list, np.ndarray)):
                    scores = [sigmoid(float(s)) for s in raw_scores]
                else:
                    scores = [sigmoid(float(raw_scores))]
            except Exception as e:
                logger.error(f"Error during Cross-Encoder prediction: {e}")
                scores = [cand.get("hybrid_score", 0.5) for cand in candidates]
        else:
            # Fallback scoring combining existing hybrid/dense scores
            scores = [cand.get("hybrid_score", 0.5) for cand in candidates]

        # Attach rerank score to candidates
        reranked = []
        for cand, score in zip(candidates, scores):
            updated_cand = dict(cand)
            updated_cand["rerank_score"] = round(score, 4)
            reranked.append(updated_cand)

        # Sort descending by rerank score
        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]


reranker_engine = CrossEncoderReranker()
