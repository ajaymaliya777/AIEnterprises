import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_text = Column(Text, nullable=False)
    intent = Column(String(50), default="FACTUAL_LOOKUP")  # ML query intent
    intent_confidence = Column(Float, default=1.0)
    answer_text = Column(Text, nullable=False)
    latency_ms = Column(Float, default=0.0)
    is_grounded = Column(Boolean, default=True)
    model_used = Column(String(100), default="gemini-1.5-flash")
    retrieved_chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    citations = relationship("CitationRecord", back_populates="query", cascade="all, delete-orphan")


class CitationRecord(Base):
    __tablename__ = "citations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String(36), ForeignKey("query_history.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(36), nullable=False)
    document_name = Column(String(255), nullable=False)
    chunk_id = Column(String(36), nullable=False)
    page_number = Column(Integer, default=1)
    snippet = Column(Text, nullable=False)
    relevance_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    query = relationship("QueryHistory", back_populates="citations")
