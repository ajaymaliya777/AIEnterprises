import pytest
from app.ingestion.preprocessor import clean_text
from app.ingestion.ocr import detect_ocr_needed
from app.ingestion.chunker import split_text_recursive, chunk_document_pages, estimate_token_count
from app.ingestion.parser import PageContent


def test_clean_text():
    raw = "  Hello \r\n\r\n world \t with   irregular   spacing. \n\n\n\n End. "
    cleaned = clean_text(raw)
    assert "Hello" in cleaned
    assert "world with irregular spacing." in cleaned
    assert "\n\n\n" not in cleaned


def test_estimate_token_count():
    text = "The quick brown fox jumps over the lazy dog."
    count = estimate_token_count(text)
    assert count >= 9


def test_detect_ocr_needed():
    # Empty or tiny text should require OCR
    assert detect_ocr_needed("") is True
    assert detect_ocr_needed("1") is True
    assert detect_ocr_needed("Scanned snippet") is True

    # High density text should not require OCR
    dense_text = "Standard enterprise corporate agreement with extensive detailed contractual terms. " * 20
    assert detect_ocr_needed(dense_text, 612.0, 792.0) is False


def test_split_text_recursive():
    sample_text = (
        "Paragraph 1 discusses the quarterly results. The revenue grew significantly.\n\n"
        "Paragraph 2 discusses operational expenditures. Costs increased by 10%.\n\n"
        "Paragraph 3 discusses strategic hiring and R&D expansion for next quarter."
    )
    chunks = split_text_recursive(sample_text, max_chars=120, overlap_chars=20)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) > 0


def test_chunk_document_pages():
    pages = [
        PageContent(page_number=1, text="Page 1 enterprise context and financial numbers.", word_count=7),
        PageContent(page_number=2, text="Page 2 regulatory compliance details and terms.", word_count=7),
    ]
    chunks = chunk_document_pages(pages, chunk_size_tokens=100, chunk_overlap_tokens=10)
    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2
    assert "financial numbers" in chunks[0].content
    assert "regulatory compliance" in chunks[1].content
