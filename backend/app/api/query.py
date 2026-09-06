import time
import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.query import QueryHistory, CitationRecord
from app.schemas.query import (
    QueryRequest,
    QueryResponse,
    QueryHistoryResponse,
    RetrievalDebugResult,
    RetrievedChunkInfo,
    CitationResponse
)
from app.retrieval.retriever import retriever
from app.llm.gemini_client import gemini_generator
from app.observability.tracer import TraceContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Query & RAG"])


@router.post("", response_model=QueryResponse)
def execute_rag_query(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Complete Grounded RAG Pipeline:
    Query -> Intent Classification -> Hybrid Retrieval -> Cross-Encoder Reranking -> Gemini Generation -> Citations.
    """
    t_start = time.perf_counter()
    tracer = TraceContext(query=request.query)

    try:
        # 1. Hybrid Retrieval & Reranking
        retrieved_chunks, debug_info = retriever.retrieve(
            query=request.query,
            document_ids=request.document_ids,
            top_k=request.top_k,
            enable_reranking=request.enable_reranking
        )

        # Record retrieval spans
        timings = debug_info.get("timings_ms", {})
        tracer.add_span("intent_classification", timings.get("intent_classification_ms", 5.0), {"intent": debug_info["intent"]})
        tracer.add_span("faiss_dense_search", timings.get("dense_search_ms", 10.0), {"hits": len(debug_info["dense_results"])})
        tracer.add_span("bm25_sparse_search", timings.get("sparse_search_ms", 8.0), {"hits": len(debug_info["sparse_results"])})
        tracer.add_span("rrf_hybrid_fusion", timings.get("rrf_fusion_ms", 3.0), {"candidates": len(debug_info["hybrid_results"])})
        tracer.add_span("cross_encoder_rerank", timings.get("reranking_ms", 25.0), {"final_k": len(retrieved_chunks)})

        # 2. Grounded LLM Generation
        t_gen_start = time.perf_counter()
        answer, citations, is_grounded, token_stats = gemini_generator.generate(
            query=request.query,
            retrieved_chunks=retrieved_chunks,
            intent=debug_info["intent"]
        )
        gen_duration_ms = (time.perf_counter() - t_gen_start) * 1000
        tracer.add_span("gemini_generation", gen_duration_ms, {"model": gemini_generator.model_name})
        tracer.set_tokens(token_stats.get("prompt_tokens", 0), token_stats.get("completion_tokens", 0))

        total_latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

        # 3. Finalize Trace & Persist
        trace_summary = tracer.finish(answer=answer, db_session=db)

        # 4. Save Query History to Database
        query_id = str(uuid.uuid4())
        q_record = QueryHistory(
            id=query_id,
            query_text=request.query,
            intent=debug_info["intent"],
            intent_confidence=debug_info.get("intent_confidence", 1.0),
            answer_text=answer,
            latency_ms=total_latency_ms,
            is_grounded=is_grounded,
            model_used=gemini_generator.model_name,
            retrieved_chunk_count=len(retrieved_chunks)
        )
        db.add(q_record)

        # Save Citations
        for c in citations:
            cit_record = CitationRecord(
                id=str(uuid.uuid4()),
                query_id=query_id,
                document_id=c.document_id,
                document_name=c.document_name,
                chunk_id=c.chunk_id,
                page_number=c.page_number,
                snippet=c.snippet,
                relevance_score=c.relevance_score
            )
            db.add(cit_record)

        db.commit()

        # 5. Format Retrieved Chunks for response
        retrieved_chunk_infos = []
        for c in retrieved_chunks:
            meta = c.get("metadata", {})
            retrieved_chunk_infos.append(RetrievedChunkInfo(
                chunk_id=c.get("chunk_id") or meta.get("chunk_id", ""),
                document_id=c.get("document_id") or meta.get("document_id", ""),
                document_name=meta.get("document_name", "Document"),
                page_number=meta.get("page_number", 1),
                content=c.get("content") or meta.get("content", ""),
                dense_score=c.get("dense_score"),
                sparse_score=c.get("sparse_score"),
                hybrid_score=c.get("hybrid_score"),
                rerank_score=c.get("rerank_score")
            ))

        debug_result = RetrievalDebugResult(**debug_info) if request.include_debug else None

        return QueryResponse(
            query_id=query_id,
            query=request.query,
            intent=debug_info["intent"],
            intent_confidence=debug_info.get("intent_confidence", 1.0),
            answer=answer,
            citations=citations,
            retrieved_chunks=retrieved_chunk_infos,
            is_grounded=is_grounded,
            model_used=gemini_generator.model_name,
            latency_ms=total_latency_ms,
            trace_id=trace_summary["trace_id"],
            debug=debug_result
        )

    except Exception as e:
        logger.error(f"Error during RAG execution: {e}", exc_info=True)
        tracer.set_error(str(e))
        tracer.finish(answer="Error executing query", db_session=db)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(e)}"
        )


@router.post("/retrieval-debug", response_model=RetrievalDebugResult)
def retrieval_debug_inspection(request: QueryRequest):
    """
    Dedicated endpoint for the Retrieval-Debug panel:
    Runs retrieval independently of Gemini to evaluate Keyword, Vector, Hybrid, and Reranked results side-by-side.
    """
    _, debug_info = retriever.retrieve(
        query=request.query,
        document_ids=request.document_ids,
        top_k=request.top_k,
        enable_reranking=request.enable_reranking
    )
    return RetrievalDebugResult(**debug_info)


@router.get("/history", response_model=List[QueryHistoryResponse])
def get_query_history(
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    history = db.query(QueryHistory).order_by(QueryHistory.created_at.desc()).limit(limit).all()
    return history
