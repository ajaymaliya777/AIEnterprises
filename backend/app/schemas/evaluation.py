from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class EvaluationRunRequest(BaseModel):
    dataset_name: Optional[str] = "EnterpriseDoc-Benchmark-v1"
    sample_size: Optional[int] = Field(default=5, ge=1, le=50)


class EvaluationItemDetail(BaseModel):
    query: str
    ground_truth: Optional[str] = None
    answer: str
    contexts: List[str]
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_name: str
    dataset_name: str
    sample_count: int
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    overall_score: float
    details: List[Dict[str, Any]] = []
    created_at: datetime
