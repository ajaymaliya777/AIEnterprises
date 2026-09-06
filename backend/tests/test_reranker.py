import pytest
from app.retrieval.reranker import CrossEncoderReranker, sigmoid


def test_sigmoid():
    assert round(sigmoid(0.0), 2) == 0.5
    assert sigmoid(5.0) > 0.99
    assert sigmoid(-5.0) < 0.01


def test_cross_encoder_reranker_ranking():
    reranker = CrossEncoderReranker()
    query = "What is the company's EBITDA in 2024?"

    candidates = [
        {
            "chunk_id": "c1",
            "content": "The employee holiday party will be hosted at the downtown conference hall in December.",
            "hybrid_score": 0.4
        },
        {
            "chunk_id": "c2",
            "content": "In fiscal year 2024, the company generated an adjusted EBITDA of $62.4 million, representing a 15% margin expansion.",
            "hybrid_score": 0.7
        },
        {
            "chunk_id": "c3",
            "content": "Office printer maintenance guidelines and toner cartridge disposal protocol.",
            "hybrid_score": 0.2
        }
    ]

    reranked = reranker.rerank(query, candidates, top_k=2)
    assert len(reranked) == 2
    # The financial chunk c2 should rank highest
    assert reranked[0]["chunk_id"] == "c2"
    assert "rerank_score" in reranked[0]
