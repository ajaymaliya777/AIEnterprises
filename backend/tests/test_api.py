import pytest
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "vector_store_chunks" in data
    assert "bm25_chunks" in data


def test_document_upload_and_query_flow():
    # 1. Upload a text document
    sample_content = (
        "EnterpriseDoc AI Technical Specification.\n\n"
        "The architecture implements a hybrid search retrieval engine utilizing "
        "BM25Okapi for keyword matching and FAISS IndexFlatIP for dense cosine similarity vectors.\n\n"
        "Reciprocal Rank Fusion merges ranked lists using a default constant k of 60.\n\n"
        "Cross-Encoder reranking ensures the top 5 chunks achieve maximum factual relevance."
    )
    file_bytes = io.BytesIO(sample_content.encode("utf-8"))

    upload_resp = client.post(
        "/documents/upload",
        files={"file": ("tech_spec.txt", file_bytes, "text/plain")}
    )
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()
    assert "document" in upload_data
    doc_id = upload_data["document"]["id"]
    assert upload_data["document"]["chunk_count"] >= 1

    # 2. List documents
    list_resp = client.get("/documents")
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert any(d["id"] == doc_id for d in docs)

    # 3. Query the document
    query_resp = client.post(
        "/query",
        json={
            "query": "What vector store and constant k are used?",
            "top_k": 3,
            "enable_reranking": True,
            "include_debug": True
        }
    )
    assert query_resp.status_code == 200
    q_data = query_resp.json()
    assert "answer" in q_data
    assert "citations" in q_data
    assert len(q_data["retrieved_chunks"]) > 0
    assert q_data["debug"] is not None
    assert "dense_results" in q_data["debug"]

    # 4. Query Retrieval Debug endpoint independently
    debug_resp = client.post(
        "/query/retrieval-debug",
        json={"query": "hybrid search BM25", "top_k": 3}
    )
    assert debug_resp.status_code == 200
    d_data = debug_resp.json()
    assert "dense_results" in d_data
    assert "sparse_results" in d_data
    assert "hybrid_results" in d_data
    assert "timings_ms" in d_data

    # 5. Check Query History
    history_resp = client.get("/query/history")
    assert history_resp.status_code == 200
    assert len(history_resp.json()) >= 1

    # 6. Delete Document
    del_resp = client.delete(f"/documents/{doc_id}")
    assert del_resp.status_code == 200

    # Verify it is deleted
    get_del = client.get(f"/documents/{doc_id}")
    assert get_del.status_code == 404
