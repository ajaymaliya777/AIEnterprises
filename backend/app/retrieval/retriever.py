import time
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from app.config import settings
from app.retrieval.faiss_store import FaissVectorStore
from app.retrieval.bm25_search import BM25Index
from app.retrieval.hybrid_fusion import reciprocal_rank_fusion
from app.retrieval.reranker import reranker_engine
from app.ml.intent_classifier import intent_classifier, QueryIntent

logger = logging.getLogger(__name__)

_EMBEDDER = None


# app/retrieval/retriever.py — already has this, just export it properly
def get_embedder():
    global _EMBEDDER
    if _EMBEDDER is None:
        from sentence_transformers import SentenceTransformer
        _EMBEDDER = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    return _EMBEDDER


class HybridRetriever:
    """
    Enterprise Hybrid Retriever coordinating Dense (FAISS) + Sparse (BM25) search,
    Reciprocal Rank Fusion, and Cross-Encoder Reranking.
    """

    def __init__(self):
        self.vector_store = FaissVectorStore(dimension=settings.EMBEDDING_DIMENSION)
        self.bm25_index = BM25Index()
        self.storage_dir = str(settings.vector_store_path)
        # Attempt to load persistent state if exists
        self.load()

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Chunks format: List of {
            "id": str,
            "document_id": str,
            "document_name": str,
            "page_number": int,
            "content": str,
            "token_count": int,
            "char_start": int,
            "char_end": int,
            "metadata": dict
        }
        """
        if not chunks:
            return

        embedder = get_embedder()
        texts = [c["content"] for c in chunks]
        ids = [c["id"] for c in chunks]
        metadatas = [{
            "chunk_id": c["id"],
            "document_id": c["document_id"],
            "document_name": c.get("document_name", "Document"),
            "page_number": c.get("page_number", 1),
            "content": c["content"],
            "token_count": c.get("token_count", 0),
            "char_start": c.get("char_start", 0),
            "char_end": c.get("char_end", 0),
            **c.get("metadata", {})
        } for c in chunks]

        # 1. Dense Embedding Generation & FAISS Indexing
        logger.info(f"Generating dense embeddings for {len(chunks)} chunks...")
        embeddings = embedder.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        self.vector_store.add_vectors(np.array(embeddings), ids, metadatas)

        # 2. Sparse BM25 Indexing
        logger.info(f"Indexing {len(chunks)} chunks into BM25...")
        self.bm25_index.add_documents(ids, texts, metadatas)

        # Auto-save indices to disk
        self.save()

    def delete_document(self, document_id: str):
        self.vector_store.delete_by_document_id(document_id)
        self.bm25_index.delete_by_document_id(document_id)
        self.save()

    def retrieve(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5,
        enable_reranking: bool = True
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executes full retrieval pipeline:
        Query -> Intent Classification -> Parallel Dense & Sparse Search -> RRF Fusion -> Rerank.
        Returns: (final_reranked_chunks, debug_info_dictionary)
        """
        timings = {}
        t0 = time.perf_counter()

        # 1. ML Query Intent Classification
        intent, confidence = intent_classifier.classify(query)
        t_intent = time.perf_counter()
        timings["intent_classification_ms"] = round((t_intent - t0) * 1000, 2)

        # Dynamic retrieval budget based on ML Intent
        dense_k = settings.RETRIEVAL_TOP_K_DENSE
        sparse_k = settings.RETRIEVAL_TOP_K_SPARSE
        if intent == QueryIntent.SUMMARIZATION.value:
            dense_k = max(dense_k, 30)
            sparse_k = max(sparse_k, 30)
            top_k = max(top_k, 8)
        elif intent == QueryIntent.FACTUAL_LOOKUP.value:
            # High precision, compact top-k
            top_k = min(top_k, 5)

        # 2. Dense Vector Search (FAISS)
        t_dense_start = time.perf_counter()
        embedder = get_embedder()
        query_vector = embedder.encode([query], normalize_embeddings=True)[0]
        dense_hits = self.vector_store.search(
            query_vector=query_vector,
            top_k=dense_k,
            filter_document_ids=document_ids
        )
        t_dense_end = time.perf_counter()
        timings["dense_search_ms"] = round((t_dense_end - t_dense_start) * 1000, 2)

        # 3. Sparse Keyword Search (BM25)
        t_sparse_start = time.perf_counter()
        sparse_hits = self.bm25_index.search(
            query=query,
            top_k=sparse_k,
            filter_document_ids=document_ids
        )
        t_sparse_end = time.perf_counter()
        timings["sparse_search_ms"] = round((t_sparse_end - t_sparse_start) * 1000, 2)

        # 4. Hybrid Reciprocal Rank Fusion (RRF)
        t_fusion_start = time.perf_counter()
        hybrid_candidates = reciprocal_rank_fusion(
            dense_results=dense_hits,
            sparse_results=sparse_hits,
            k=settings.RRF_K,
            vector_weight=settings.RRF_VECTOR_WEIGHT,
            lexical_weight=settings.RRF_LEXICAL_WEIGHT,
            top_k=max(20, top_k * 3)
        )
        t_fusion_end = time.perf_counter()
        timings["rrf_fusion_ms"] = round((t_fusion_end - t_fusion_start) * 1000, 2)

        # 5. Cross-Encoder Reranking
        t_rerank_start = time.perf_counter()
        if enable_reranking and hybrid_candidates:
            reranked_results = reranker_engine.rerank(
                query=query,
                candidates=hybrid_candidates,
                top_k=top_k
            )
        else:
            reranked_results = hybrid_candidates[:top_k]
            for r in reranked_results:
                r["rerank_score"] = r.get("hybrid_score", 0.5)

        t_rerank_end = time.perf_counter()
        timings["reranking_ms"] = round((t_rerank_end - t_rerank_start) * 1000, 2)
        timings["total_retrieval_ms"] = round((t_rerank_end - t0) * 1000, 2)

        # Format debug structures
        def format_hit(chunk_id, score, meta, score_field):
            return {
                "chunk_id": chunk_id,
                "document_id": meta.get("document_id", ""),
                "document_name": meta.get("document_name", "Doc"),
                "page_number": meta.get("page_number", 1),
                "content": meta.get("content", ""),
                score_field: round(score, 4)
            }

        debug_info = {
            "query": query,
            "intent": intent,
            "intent_confidence": confidence,
            "dense_results": [
                format_hit(cid, s, m, "dense_score") for cid, s, m in dense_hits[:10]
            ],
            "sparse_results": [
                format_hit(cid, s, m, "sparse_score") for cid, s, m in sparse_hits[:10]
            ],
            "hybrid_results": [
                {
                    "chunk_id": item["chunk_id"],
                    "document_id": item["metadata"].get("document_id", ""),
                    "document_name": item["metadata"].get("document_name", "Doc"),
                    "page_number": item["metadata"].get("page_number", 1),
                    "content": item["metadata"].get("content", ""),
                    "hybrid_score": round(item["hybrid_score"], 4),
                    "dense_score": round(item["dense_score"], 4) if item.get("dense_score") is not None else None,
                    "sparse_score": round(item["sparse_score"], 4) if item.get("sparse_score") is not None else None,
                }
                for item in hybrid_candidates[:10]
            ],
            "reranked_results": [
                {
                    "chunk_id": item["chunk_id"],
                    "document_id": item["metadata"].get("document_id", ""),
                    "document_name": item["metadata"].get("document_name", "Doc"),
                    "page_number": item["metadata"].get("page_number", 1),
                    "content": item["metadata"].get("content", ""),
                    "rerank_score": item.get("rerank_score", 0.0),
                    "hybrid_score": round(item["hybrid_score"], 4) if item.get("hybrid_score") is not None else None,
                }
                for item in reranked_results
            ],
            "timings_ms": timings
        }

        return reranked_results, debug_info

    def save(self):
        try:
            self.vector_store.save(self.storage_dir)
            self.bm25_index.save(self.storage_dir)
        except Exception as e:
            logger.error(f"Failed to persist retrieval indices: {e}")

    def load(self):
        try:
            self.vector_store.load(self.storage_dir)
            self.bm25_index.load(self.storage_dir)
        except Exception as e:
            logger.error(f"Failed to load retrieval indices: {e}")


# Master singleton retriever instance
retriever = HybridRetriever()
