import re
from typing import List, Dict, Any
from dataclasses import dataclass, field
from app.config import settings
from app.ingestion.parser import PageContent


@dataclass
class Chunk:
    chunk_index: int
    page_number: int
    content: str
    token_count: int
    char_start: int
    char_end: int
    metadata: Dict[str, Any] = field(default_factory=dict)


def estimate_token_count(text: str) -> int:
    """
    Approximates token count (avg 4 chars per token for English words, with fallback).
    """
    words = text.split()
    # Average 1.3 tokens per word
    return int(max(1, len(words) * 1.3))


def split_text_recursive(
    text: str,
    max_chars: int = 2000,
    overlap_chars: int = 300,
    separators: List[str] = None
) -> List[str]:
    """
    Recursively splits text into chunks respecting semantic boundaries.
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    if len(text) <= max_chars:
        return [text] if text.strip() else []

    # Find the first separator present in the text
    separator = separators[-1]
    for sep in separators:
        if sep == "":
            separator = ""
            break
        if sep in text:
            separator = sep
            break

    splits = text.split(separator) if separator != "" else list(text)

    chunks = []
    current_chunk = []
    current_len = 0

    for piece in splits:
        piece_str = piece if separator == "" else piece + separator
        piece_len = len(piece_str)

        if current_len + piece_len > max_chars and current_chunk:
            combined = "".join(current_chunk).strip()
            if combined:
                chunks.append(combined)

            # Keep overlap from the end of current_chunk
            overlap_accum = []
            overlap_len = 0
            for item in reversed(current_chunk):
                overlap_accum.insert(0, item)
                overlap_len += len(item)
                if overlap_len >= overlap_chars:
                    break
            current_chunk = overlap_accum
            current_len = overlap_len

        current_chunk.append(piece_str)
        current_len += piece_len

    if current_chunk:
        combined = "".join(current_chunk).strip()
        if combined:
            chunks.append(combined)

    return chunks


def chunk_document_pages(
    pages: List[PageContent],
    chunk_size_tokens: int = None,
    chunk_overlap_tokens: int = None
) -> List[Chunk]:
    """
    Chunks a list of parsed pages while preserving page context and offsets.
    """
    if chunk_size_tokens is None:
        chunk_size_tokens = settings.CHUNK_SIZE
    if chunk_overlap_tokens is None:
        chunk_overlap_tokens = settings.CHUNK_OVERLAP

    # 1 token ~= 4 characters
    max_chars = chunk_size_tokens * 4
    overlap_chars = chunk_overlap_tokens * 4

    chunks: List[Chunk] = []
    chunk_idx = 0

    for page in pages:
        if not page.text or not page.text.strip():
            continue

        raw_chunks = split_text_recursive(
            page.text,
            max_chars=max_chars,
            overlap_chars=overlap_chars
        )

        char_offset = 0
        for text_chunk in raw_chunks:
            # Find char start and end in page
            start_pos = page.text.find(text_chunk[:50], char_offset)
            if start_pos == -1:
                start_pos = char_offset
            end_pos = start_pos + len(text_chunk)
            char_offset = start_pos + max(1, len(text_chunk) - overlap_chars)

            tok_count = estimate_token_count(text_chunk)

            chunk = Chunk(
                chunk_index=chunk_idx,
                page_number=page.page_number,
                content=text_chunk,
                token_count=tok_count,
                char_start=start_pos,
                char_end=end_pos,
                metadata={
                    "is_ocr": page.is_ocr_applied,
                    "page_number": page.page_number,
                    "word_count": len(text_chunk.split())
                }
            )
            chunks.append(chunk)
            chunk_idx += 1

    return chunks
