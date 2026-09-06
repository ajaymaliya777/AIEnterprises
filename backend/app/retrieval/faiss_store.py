import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from app.retrieval.base_vector_store import BaseVectorStore

logger = logging.getLogger(__name__)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("faiss-cpu is not installed. FAISS store will run in high-performance NumPy fallback mode.")


class FaissVectorStore(BaseVectorStore):
    """
    Production-ready FAISS Vector Store implementation with cosine similarity.
    Persists to disk with index file and metadata catalog.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.id_to_idx: Dict[str, int] = {}
        self.idx_to_id: Dict[int, str] = {}
        self.metadata_store: Dict[str, Dict[str, Any]] = {}
        self.vectors: Optional[np.ndarray] = None  # Backup array for fast rebuilding & NumPy fallback
        self.index = None

        self._init_index()

    def _init_index(self):
        if FAISS_AVAILABLE:
            # IndexFlatIP calculates inner product.
            # On L2-normalized vectors, inner product == cosine similarity.
            self.index = faiss.IndexFlatIP(self.dimension)
        else:
            self.index = None

    def add_vectors(
        self,
        vectors: np.ndarray,
        ids: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        if len(ids) == 0:
            return

        # Ensure vectors are float32 and L2-normalized for cosine similarity
        norm_vectors = vectors.astype(np.float32)
        norms = np.linalg.norm(norm_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        norm_vectors = norm_vectors / norms

        start_idx = len(self.idx_to_id)

        for i, (chunk_id, meta) in enumerate(zip(ids, metadatas)):
            current_idx = start_idx + i
            self.id_to_idx[chunk_id] = current_idx
            self.idx_to_id[current_idx] = chunk_id
            self.metadata_store[chunk_id] = meta

        if self.vectors is None:
            self.vectors = norm_vectors
        else:
            self.vectors = np.vstack([self.vectors, norm_vectors])

        if FAISS_AVAILABLE and self.index is not None:
            self.index.add(norm_vectors)

        logger.info(f"Added {len(ids)} vectors to FAISS store. Total count: {self.count()}")

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filter_document_ids: Optional[List[str]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        if self.count() == 0:
            return []

        # Normalize query vector
        q_vec = query_vector.astype(np.float32).reshape(1, -1)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        filter_set = set(filter_document_ids) if filter_document_ids else None
        results: List[Tuple[str, float, Dict[str, Any]]] = []

        # Request more if filtering is required
        search_k = min(self.count(), top_k * 5 if filter_set else top_k)

        if FAISS_AVAILABLE and self.index is not None:
            scores, indices = self.index.search(q_vec, search_k)
            scores = scores[0]
            indices = indices[0]

            for score, idx in zip(scores, indices):
                if idx == -1 or idx not in self.idx_to_id:
                    continue
                chunk_id = self.idx_to_id[idx]
                meta = self.metadata_store.get(chunk_id, {})

                if filter_set and meta.get("document_id") not in filter_set:
                    continue

                # Cosine similarity in range [0, 1] for typical text embeddings
                normalized_score = float(max(0.0, min(1.0, (score + 1.0) / 2.0)))
                results.append((chunk_id, normalized_score, meta))
                if len(results) >= top_k:
                    break
        else:
            # NumPy fallback calculation
            sims = np.dot(self.vectors, q_vec.T).flatten()
            top_indices = np.argsort(-sims)[:search_k]

            for idx in top_indices:
                chunk_id = self.idx_to_id[idx]
                meta = self.metadata_store.get(chunk_id, {})

                if filter_set and meta.get("document_id") not in filter_set:
                    continue

                score = float(sims[idx])
                normalized_score = float(max(0.0, min(1.0, (score + 1.0) / 2.0)))
                results.append((chunk_id, normalized_score, meta))
                if len(results) >= top_k:
                    break

        return results

    def delete(self, ids: List[str]) -> bool:
        ids_to_remove = set(ids)
        if not ids_to_remove or self.count() == 0:
            return False

        remaining_ids = []
        remaining_metas = []
        remaining_vectors = []

        for idx in range(len(self.idx_to_id)):
            chunk_id = self.idx_to_id.get(idx)
            if chunk_id and chunk_id not in ids_to_remove:
                remaining_ids.append(chunk_id)
                remaining_metas.append(self.metadata_store[chunk_id])
                if self.vectors is not None:
                    remaining_vectors.append(self.vectors[idx])

        # Re-build store
        self.id_to_idx.clear()
        self.idx_to_id.clear()
        self.metadata_store.clear()
        self.vectors = None
        self._init_index()

        if remaining_ids and remaining_vectors:
            self.add_vectors(np.array(remaining_vectors), remaining_ids, remaining_metas)

        logger.info(f"Deleted {len(ids_to_remove)} vectors. Remaining count: {self.count()}")
        return True

    def delete_by_document_id(self, document_id: str) -> bool:
        chunks_to_delete = [
            chunk_id for chunk_id, meta in self.metadata_store.items()
            if meta.get("document_id") == document_id
        ]
        if chunks_to_delete:
            return self.delete(chunks_to_delete)
        return False

    def save(self, directory: str) -> None:
        save_dir = Path(directory)
        save_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata and index mapping
        meta_file = save_dir / "faiss_metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump({
                "dimension": self.dimension,
                "id_to_idx": self.id_to_idx,
                "idx_to_id": {str(k): v for k, v in self.idx_to_id.items()},
                "metadata_store": self.metadata_store
            }, f, indent=2)

        # Save FAISS index
        if FAISS_AVAILABLE and self.index is not None:
            index_file = save_dir / "faiss_index.bin"
            faiss.write_index(self.index, str(index_file))

        # Save raw vectors backup
        if self.vectors is not None:
            vectors_file = save_dir / "faiss_vectors.npy"
            np.save(str(vectors_file), self.vectors)

        logger.info(f"Saved FAISS vector store to {directory}")

    def load(self, directory: str) -> bool:
        load_dir = Path(directory)
        meta_file = load_dir / "faiss_metadata.json"
        if not meta_file.exists():
            return False

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.dimension = data["dimension"]
            self.id_to_idx = data["id_to_idx"]
            self.idx_to_id = {int(k): v for k, v in data["idx_to_id"].items()}
            self.metadata_store = data["metadata_store"]

            vectors_file = load_dir / "faiss_vectors.npy"
            if vectors_file.exists():
                self.vectors = np.load(str(vectors_file))

            index_file = load_dir / "faiss_index.bin"
            if FAISS_AVAILABLE and index_file.exists():
                self.index = faiss.read_index(str(index_file))
            else:
                self._init_index()
                if self.vectors is not None and FAISS_AVAILABLE and self.index is not None:
                    self.index.add(self.vectors)

            logger.info(f"Loaded FAISS vector store from {directory}. Count: {self.count()}")
            return True
        except Exception as e:
            logger.error(f"Failed to load FAISS store from {directory}: {e}", exc_info=True)
            return False

    def count(self) -> int:
        return len(self.id_to_idx)
