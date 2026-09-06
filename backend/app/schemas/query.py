from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="User's natural language question")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional document filter")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of final context chunks to use")
    enable_reranking: bool = Field(default=True, description="Whether to apply cross-encoder reranking")
    include_debug: bool = Field(default=False, description="Include detailed retrieval step breakdown")


class CitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    document_name: str
    chunk_id: str
    page_number: int
    snippet: str
    relevance_score: float


class RetrievedChunkInfo(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int = 1
    content: str
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None
    hybrid_score: Optional[float] = None
    rerank_score: Optional[float] = None


class RetrievalDebugResult(BaseModel):
    query: str
    intent: str
    intent_confidence: float
    dense_results: List[RetrievedChunkInfo] = []
    sparse_results: List[RetrievedChunkInfo] = []
    hybrid_results: List[RetrievedChunkInfo] = []
    reranked_results: List[RetrievedChunkInfo] = []
    timings_ms: Dict[str, float] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    query_id: str
    query: str
    intent: str
    intent_confidence: float = 1.0
    answer: str
    citations: List[CitationResponse] = []
    retrieved_chunks: List[RetrievedChunkInfo] = []
    is_grounded: bool = True
    model_used: str = "gemini-1.5-flash"
    latency_ms: float = 0.0
    trace_id: Optional[str] = None
    debug: Optional[RetrievalDebugResult] = None


class QueryHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query_text: str
    intent: str
    answer_text: str
    latency_ms: float
    is_grounded: bool
    model_used: str
    created_at: datetime
    citations: List[CitationResponse] = []
