import re
import logging
from typing import List, Dict, Any, Tuple
from app.schemas.query import CitationResponse

logger = logging.getLogger(__name__)


def build_context_string(chunks: List[Dict[str, Any]]) -> str:
    """
    Formats a list of retrieved chunks into numbered evidence blocks for the LLM prompt.
    """
    if not chunks:
        return "No relevant context chunks found."

    blocks = []
    for idx, c in enumerate(chunks, 1):
        meta = c.get("metadata", {})
        chunk_id = c.get("chunk_id") or meta.get("chunk_id", f"chunk-{idx}")
        doc_name = meta.get("document_name") or c.get("document_name", "Unknown Document")
        page_num = meta.get("page_number") or c.get("page_number", 1)
        content = c.get("content") or meta.get("content", "")

        block = (
            f"[Chunk {idx}] (ID: {chunk_id} | Document: {doc_name} | Page: {page_num})\n"
            f"{content.strip()}"
        )
        blocks.append(block)

    return "\n\n".join(blocks)


def extract_citations(
    answer_text: str,
    retrieved_chunks: List[Dict[str, Any]]
) -> List[CitationResponse]:
    """
    Extracts citations from the generated answer and correlates them with retrieved chunks.
    Matches citations in format: [Doc: <name>, Page: <page>, Chunk: <id>] or [Chunk <N>]
    """
    citations: List[CitationResponse] = []
    seen_keys = set()

    # Index retrieved chunks by chunk_id and numeric index
    chunk_by_id = {}
    for idx, c in enumerate(retrieved_chunks, 1):
        meta = c.get("metadata", {})
        cid = c.get("chunk_id") or meta.get("chunk_id", str(idx))
        chunk_by_id[cid] = (idx, c)
        chunk_by_id[f"chunk_{idx}"] = (idx, c)
        chunk_by_id[str(idx)] = (idx, c)

    # 1. Regex match explicit format [Doc: ..., Page: ..., Chunk: ...]
    pattern_explicit = r"\[Doc:\s*([^,\]]+),\s*Page:\s*(\d+),\s*Chunk:\s*([^\]]+)\]"
    matches_explicit = re.findall(pattern_explicit, answer_text, re.IGNORECASE)

    for doc_name, page_str, chunk_id in matches_explicit:
        chunk_id = chunk_id.strip()
        doc_name = doc_name.strip()
        page_num = int(page_str)
        key = (doc_name, page_num, chunk_id)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        # Lookup chunk snippet and relevance score
        matched_chunk = None
        if chunk_id in chunk_by_id:
            _, matched_chunk = chunk_by_id[chunk_id]
        else:
            # Fallback search by doc_name and page
            for c in retrieved_chunks:
                m = c.get("metadata", {})
                if m.get("document_name") == doc_name and m.get("page_number") == page_num:
                    matched_chunk = c
                    break

        content = matched_chunk.get("content") or matched_chunk.get("metadata", {}).get("content", "") if matched_chunk else ""
        snippet = (content[:250] + "...") if len(content) > 250 else content
        score = matched_chunk.get("rerank_score", matched_chunk.get("hybrid_score", 0.8)) if matched_chunk else 0.8
        doc_id = matched_chunk.get("document_id") or matched_chunk.get("metadata", {}).get("document_id", "") if matched_chunk else ""

        citations.append(CitationResponse(
            document_id=doc_id,
            document_name=doc_name,
            chunk_id=chunk_id,
            page_number=page_num,
            snippet=snippet,
            relevance_score=float(score)
        ))

    # 2. If no explicit citations were parsed, check if LLM referenced [Chunk N]
    if not citations:
        pattern_num = r"\[(?:Chunk\s*)?(\d+)\]"
        matches_num = re.findall(pattern_num, answer_text, re.IGNORECASE)
        for num_str in matches_num:
            idx = int(num_str)
            if 1 <= idx <= len(retrieved_chunks):
                c = retrieved_chunks[idx - 1]
                meta = c.get("metadata", {})
                cid = c.get("chunk_id") or meta.get("chunk_id", f"chunk-{idx}")
                key = (meta.get("document_name", "Document"), meta.get("page_number", 1), cid)
                if key not in seen_keys:
                    seen_keys.add(key)
                    content = c.get("content") or meta.get("content", "")
                    citations.append(CitationResponse(
                        document_id=c.get("document_id") or meta.get("document_id", ""),
                        document_name=meta.get("document_name", "Document"),
                        chunk_id=cid,
                        page_number=meta.get("page_number", 1),
                        snippet=(content[:250] + "...") if len(content) > 250 else content,
                        relevance_score=float(c.get("rerank_score", c.get("hybrid_score", 0.85)))
                    ))

    # 3. If still empty but retrieved chunks exist, attach top 2 chunks as source references
    if not citations and retrieved_chunks:
        for c in retrieved_chunks[:2]:
            meta = c.get("metadata", {})
            cid = c.get("chunk_id") or meta.get("chunk_id", "chunk-1")
            content = c.get("content") or meta.get("content", "")
            citations.append(CitationResponse(
                document_id=c.get("document_id") or meta.get("document_id", ""),
                document_name=meta.get("document_name", "Document"),
                chunk_id=cid,
                page_number=meta.get("page_number", 1),
                snippet=(content[:250] + "...") if len(content) > 250 else content,
                relevance_score=float(c.get("rerank_score", c.get("hybrid_score", 0.75)))
            ))

    return citations
