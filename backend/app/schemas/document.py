from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    chunk_index: int
    page_number: int = 1
    content: str
    token_count: int
    char_start: int = 0
    char_end: int = 0
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    original_name: str
    mime_type: str
    file_size: int
    category: str = "General"
    ocr_applied: bool = False
    status: str = "pending"
    error_message: Optional[str] = None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    chunks: List[ChunkResponse] = []


class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse
