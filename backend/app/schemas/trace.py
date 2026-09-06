from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SpanInfo(BaseModel):
    name: str
    start_time_ms: float
    duration_ms: float
    status: str = "ok"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TraceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query_id: Optional[str] = None
    trace_id: str
    query_text: str
    total_latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    status: str = "success"
    error_message: Optional[str] = None
    spans: List[Dict[str, Any]] = []
    created_at: datetime
