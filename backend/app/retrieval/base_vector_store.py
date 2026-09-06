from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import numpy as np


class BaseVectorStore(ABC):
    """
    Abstract Vector Store interface to ensure replaceable vector-store backends
    (FAISS, ChromaDB, pgvector, Qdrant, etc.)
    """

    @abstractmethod
    def add_vectors(
        self,
        vectors: np.ndarray,
        ids: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """Add dense embedding vectors with corresponding IDs and metadata."""
        pass

    @abstractmethod
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filter_document_ids: Optional[List[str]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Search for top_k most similar vectors.
        Returns: List of (chunk_id, similarity_score, metadata)
        """
        pass

    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """Delete vectors by chunk IDs."""
        pass

    @abstractmethod
    def delete_by_document_id(self, document_id: str) -> bool:
        """Delete all vectors belonging to a specific document."""
        pass

    @abstractmethod
    def save(self, directory: str) -> None:
        """Persist index and metadata to disk."""
        pass

    @abstractmethod
    def load(self, directory: str) -> bool:
        """Load index and metadata from disk."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total number of vectors in the store."""
        pass
