import os
import re
import uuid
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentResponse, DocumentDetailResponse, DocumentUploadResponse
from app.ingestion.parser import parse_document
from app.ingestion.chunker import chunk_document_pages
from app.ml.document_classifier import document_classifier
from app.retrieval.retriever import retriever

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


def sanitize_filename(filename: str) -> str:
    """Sanitizes filename to prevent directory traversal and unsafe characters."""
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    clean = re.sub(r"_+", "_", clean)
    return clean.strip("._") or "uploaded_file"


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Validate File Extension
    orig_name = file.filename or "unknown.txt"
    ext = Path(orig_name).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not supported. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 2. Read content and validate file size
    contents = await file.read()
    file_size = len(contents)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB (current: {file_size / (1024*1024):.2f}MB)"
        )

    # 3. Save safe file locally
    doc_id = str(uuid.uuid4())
    safe_name = f"{doc_id[:8]}_{sanitize_filename(orig_name)}"
    dest_path = settings.upload_path / safe_name

    with open(dest_path, "wb") as f:
        f.write(contents)

    # 4. Ingestion: Parse Document and run OCR if necessary
    try:
        parsed = parse_document(str(dest_path))
    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()
        logger.error(f"Failed to parse uploaded document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error parsing document: {str(e)}"
        )

    # 5. Chunking: Recursive semantic chunker
    chunks = chunk_document_pages(parsed.pages)
    if not chunks and parsed.full_text:
        # Fallback if pages weren't chunked
        from app.ingestion.parser import PageContent
        chunks = chunk_document_pages([PageContent(page_number=1, text=parsed.full_text)])

    # 6. ML Document Domain Classification
    category, _ = document_classifier.classify_text(parsed.full_text)

    # 7. Create Database Record
    doc = Document(
        id=doc_id,
        filename=safe_name,
        original_name=orig_name,
        mime_type=parsed.mime_type or (file.content_type or "application/octet-stream"),
        file_size=file_size,
        file_path=str(dest_path),
        category=category,
        ocr_applied=parsed.ocr_applied,
        status="indexed",
        chunk_count=len(chunks)
    )
    db.add(doc)
    db.flush()

    # 8. Create Chunk Records in Database & Prepare for Vector Store
    chunk_dicts_for_retriever = []
    for c in chunks:
        chunk_id = str(uuid.uuid4())
        db_chunk = DocumentChunk(
            id=chunk_id,
            document_id=doc_id,
            chunk_index=c.chunk_index,
            page_number=c.page_number,
            content=c.content,
            token_count=c.token_count,
            char_start=c.char_start,
            char_end=c.char_end,
            metadata_json=c.metadata
        )
        db.add(db_chunk)

        chunk_dicts_for_retriever.append({
            "id": chunk_id,
            "document_id": doc_id,
            "document_name": orig_name,
            "page_number": c.page_number,
            "content": c.content,
            "token_count": c.token_count,
            "char_start": c.char_start,
            "char_end": c.char_end,
            "metadata": {
                "category": category,
                "is_ocr": c.metadata.get("is_ocr", False)
            }
        })

    db.commit()
    db.refresh(doc)

    # 9. Index into Dense FAISS and Sparse BM25
    if chunk_dicts_for_retriever:
        try:
            retriever.add_chunks(chunk_dicts_for_retriever)
        except Exception as e:
            logger.error(f"Error indexing chunks into vector/lexical store: {e}", exc_info=True)

    logger.info(f"Successfully processed and indexed document '{orig_name}' with {len(chunks)} chunks.")
    return DocumentUploadResponse(
        message=f"Successfully indexed '{orig_name}' ({len(chunks)} chunks, category: {category})",
        document=DocumentResponse.model_validate(doc)
    )


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    docs = db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    return docs


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document with ID '{document_id}' not found.")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document with ID '{document_id}' not found.")

    # 1. Remove from Vector Store and BM25 index
    retriever.delete_document(document_id)

    # 2. Delete physical file if exists
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning(f"Could not delete physical file {doc.file_path}: {e}")

    # 3. Delete from DB (cascades to chunks)
    db.delete(doc)
    db.commit()

    logger.info(f"Document '{doc.original_name}' (ID: {document_id}) deleted successfully.")
    return {"message": f"Document '{doc.original_name}' deleted successfully."}
