import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.trace import TraceRecord
from app.schemas.trace import TraceResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observability", tags=["Observability & Tracing"])


@router.get("/traces", response_model=List[TraceResponse])
def get_recent_traces(
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Returns recent end-to-end RAG traces with span breakdowns and token usage."""
    traces = db.query(TraceRecord).order_by(TraceRecord.created_at.desc()).limit(limit).all()
    results = []
    for t in traces:
        results.append(TraceResponse(
            id=t.id,
            query_id=t.query_id,
            trace_id=t.trace_id,
            query_text=t.query_text,
            total_latency_ms=t.total_latency_ms,
            prompt_tokens=t.prompt_tokens,
            completion_tokens=t.completion_tokens,
            status=t.status,
            error_message=t.error_message,
            spans=t.spans_json or [],
            created_at=t.created_at
        ))
    return results


@router.get("/stats")
def get_observability_stats(db: Session = Depends(get_db)):
    """Summary metrics of query latency, volume, and Langfuse connectivity."""
    total_traces = db.query(TraceRecord).count()
    avg_latency = db.query(func.avg(TraceRecord.total_latency_ms)).scalar() or 0.0
    total_prompt = db.query(func.sum(TraceRecord.prompt_tokens)).scalar() or 0
    total_comp = db.query(func.sum(TraceRecord.completion_tokens)).scalar() or 0
    error_count = db.query(TraceRecord).filter(TraceRecord.status == "error").count()

    langfuse_configured = bool(settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY)

    return {
        "total_queries_traced": total_traces,
        "avg_latency_ms": round(float(avg_latency), 2),
        "total_prompt_tokens": int(total_prompt),
        "total_completion_tokens": int(total_comp),
        "error_count": error_count,
        "success_rate": round((1.0 - (error_count / total_traces)) * 100, 1) if total_traces > 0 else 100.0,
        "langfuse_cloud_connected": langfuse_configured,
        "langfuse_host": settings.LANGFUSE_HOST if langfuse_configured else None
    }
