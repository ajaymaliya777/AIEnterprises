import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from app.database import Base


class EvaluationRecord(Base):
    __tablename__ = "evaluations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_name = Column(String(255), nullable=False)
    dataset_name = Column(String(255), default="EnterpriseDoc-Benchmark-v1")
    sample_count = Column(Integer, default=0)
    faithfulness = Column(Float, default=0.0)
    answer_relevancy = Column(Float, default=0.0)
    context_precision = Column(Float, default=0.0)
    context_recall = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    details_json = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
