import os
import time
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

_LANGFUSE_CLIENT = None
_LANGFUSE_INITIALIZED = False


def get_langfuse_client():
    global _LANGFUSE_CLIENT, _LANGFUSE_INITIALIZED
    if _LANGFUSE_INITIALIZED:
        return _LANGFUSE_CLIENT

    _LANGFUSE_INITIALIZED = True
    pub_key = settings.LANGFUSE_PUBLIC_KEY or os.getenv("LANGFUSE_PUBLIC_KEY")
    sec_key = settings.LANGFUSE_SECRET_KEY or os.getenv("LANGFUSE_SECRET_KEY")

    if pub_key and sec_key:
        try:
            from langfuse import Langfuse
            _LANGFUSE_CLIENT = Langfuse(
                public_key=pub_key,
                secret_key=sec_key,
                host=settings.LANGFUSE_HOST
            )
            logger.info("Langfuse client connected successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize Langfuse SDK: {e}. Running local tracing mode.")
            _LANGFUSE_CLIENT = None
    else:
        logger.info("Langfuse credentials not set; running in local database tracing mode.")
        _LANGFUSE_CLIENT = None

    return _LANGFUSE_CLIENT


class TraceContext:
    """
    Structured execution trace for a single RAG request.
    Records individual spans and sends them to Langfuse and DB persistence.
    """

    def __init__(self, query: str, session_id: Optional[str] = None):
        self.trace_id = str(uuid.uuid4())
        self.query = query
        self.session_id = session_id or str(uuid.uuid4())
        self.start_time = time.perf_counter()
        self.spans: List[Dict[str, Any]] = []
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.status = "success"
        self.error_message: Optional[str] = None
        self.langfuse_trace = None

        # If Langfuse is available, start cloud trace
        lf = get_langfuse_client()
        if lf is not None:
            try:
                self.langfuse_trace = lf.trace(
                    id=self.trace_id,
                    name="rag-query-pipeline",
                    session_id=self.session_id,
                    input={"query": query}
                )
            except Exception as e:
                logger.warning(f"Error starting Langfuse trace: {e}")

    def add_span(
        self,
        name: str,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "ok"
    ):
        span_data = {
            "name": name,
            "duration_ms": round(duration_ms, 2),
            "status": status,
            "metadata": metadata or {}
        }
        self.spans.append(span_data)

        if self.langfuse_trace is not None:
            try:
                self.langfuse_trace.span(
                    name=name,
                    metadata=metadata or {},
                    status_message=status
                )
            except Exception as e:
                logger.warning(f"Failed to record Langfuse span '{name}': {e}")

    def set_tokens(self, prompt_tokens: int, completion_tokens: int):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

    def set_error(self, error: str):
        self.status = "error"
        self.error_message = error

    def finish(self, answer: str, db_session=None) -> Dict[str, Any]:
        total_latency_ms = round((time.perf_counter() - self.start_time) * 1000, 2)

        # Complete Langfuse trace
        if self.langfuse_trace is not None:
            try:
                self.langfuse_trace.update(
                    output={"answer": answer},
                    metadata={"total_latency_ms": total_latency_ms}
                )
            except Exception as e:
                logger.warning(f"Failed to finalize Langfuse trace: {e}")

        # Persist to DB if session provided
        if db_session is not None:
            try:
                from app.models.trace import TraceRecord
                record = TraceRecord(
                    trace_id=self.trace_id,
                    session_id=self.session_id,
                    query_text=self.query,
                    total_latency_ms=total_latency_ms,
                    prompt_tokens=self.prompt_tokens,
                    completion_tokens=self.completion_tokens,
                    status=self.status,
                    error_message=self.error_message,
                    spans_json=self.spans,
                    created_at=datetime.utcnow()
                )
                db_session.add(record)
                db_session.commit()
            except Exception as e:
                logger.error(f"Failed to save trace record to database: {e}")
                db_session.rollback()

        return {
            "trace_id": self.trace_id,
            "total_latency_ms": total_latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "status": self.status,
            "spans": self.spans
        }
