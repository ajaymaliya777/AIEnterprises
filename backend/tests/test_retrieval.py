import pytest
import numpy as np
from app.retrieval.faiss_store import FaissVectorStore
from app.retrieval.bm25_search import BM25Index, tokenize
from app.retrieval.hybrid_fusion import reciprocal_rank_fusion


def test_faiss_vector_store():
    store = FaissVectorStore(dimension=4)
    vectors = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
    ], dtype=np.float32)

    ids = ["doc1-c1", "doc1-c2", "doc2-c1"]
    metas = [
        {"document_id": "doc1", "content": "Chunk 1"},
        {"document_id": "doc1", "content": "Chunk 2"},
        {"document_id": "doc2", "content": "Chunk 3"},
    ]

    store.add_vectors(vectors, ids, metas)
    assert store.count() == 3

    # Search for vector aligned with doc1-c1
    query = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    results = store.search(query, top_k=2)
    assert len(results) == 2
    assert results[0][0] == "doc1-c1"
    assert results[0][1] >= 0.99  # Cosine similarity close to 1.0

    # Test filtering by document_id
    filtered = store.search(query, top_k=2, filter_document_ids=["doc2"])
    assert len(filtered) == 1
    assert filtered[0][0] == "doc2-c1"

    # Test deletion
    store.delete(["doc1-c1"])
    assert store.count() == 2


def test_bm25_search():
    index = BM25Index()
    ids = ["c1", "c2", "c3"]
    texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Enterprise cloud computing and distributed databases.",
        "Revenue increased by forty percent in the third quarter.",
    ]
    metas = [{"document_id": "d1"}, {"document_id": "d2"}, {"document_id": "d3"}]

    index.add_documents(ids, texts, metas)
    assert index.count() == 3

    results = index.search("cloud computing databases", top_k=2)
    assert len(results) > 0
    assert results[0][0] == "c2"

    results_finance = index.search("revenue quarter", top_k=2)
    assert len(results_finance) > 0
    assert results_finance[0][0] == "c3"


def test_reciprocal_rank_fusion():
    dense = [
        ("c1", 0.95, {"document_name": "Doc A"}),
        ("c2", 0.85, {"document_name": "Doc B"}),
        ("c3", 0.70, {"document_name": "Doc C"}),
    ]
    sparse = [
        ("c2", 12.5, {"document_name": "Doc B"}),
        ("c4", 8.2, {"document_name": "Doc D"}),
        ("c1", 4.1, {"document_name": "Doc A"}),
    ]

    fused = reciprocal_rank_fusion(dense, sparse, k=60, top_k=3)
    assert len(fused) == 3
    # c2 appeared high in both dense and sparse, so it should rank at or near the top
    top_chunk_ids = [item["chunk_id"] for item in fused]
    assert "c2" in top_chunk_ids
    assert "c1" in top_chunk_ids
