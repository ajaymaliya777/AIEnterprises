import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text
from app.database import Base


class TraceRecord(Base):
    __tablename__ = "traces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String(36), nullable=True)
    trace_id = Column(String(64), nullable=False, index=True)
    session_id = Column(String(64), nullable=True)
    query_text = Column(Text, nullable=False)
    total_latency_ms = Column(Float, default=0.0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    status = Column(String(50), default="success")  # success, error
    error_message = Column(Text, nullable=True)
    spans_json = Column(JSON, default=list)  # details of individual spans
    created_at = Column(DateTime, default=datetime.utcnow)
