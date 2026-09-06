import os
import logging
from typing import List, Dict, Any, Tuple

from app.config import settings
from app.llm.prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.llm.context_builder import build_context_string, extract_citations
from app.schemas.query import CitationResponse


logger = logging.getLogger(__name__)


_GENAI_CLIENT = None


def _configure_gemini():
    global _GENAI_CLIENT

    if _GENAI_CLIENT is not None:
        return _GENAI_CLIENT

    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        return None

    try:
        from google import genai

        _GENAI_CLIENT = genai.Client(api_key=api_key)

        logger.info("Google Gemini API client configured successfully.")

        return _GENAI_CLIENT

    except Exception as e:
        logger.warning(f"Failed to configure Gemini client: {e}")
        return None


def _local_grounded_synthesis(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    intent: str
) -> Tuple[str, List[CitationResponse], bool, Dict[str, Any]]:

    if not retrieved_chunks:
        answer = (
            "The provided documents do not contain sufficient information "
            "to answer this question."
        )

        return (
            answer,
            [],
            False,
            {
                "prompt_tokens": 0,
                "completion_tokens": 15
            }
        )

    citations = []
    response_lines = []

    response_lines.append(
        "Based on the enterprise document knowledge base:\n"
    )

    for idx, c in enumerate(retrieved_chunks[:3], 1):

        meta = c.get("metadata", {})

        doc_name = meta.get(
            "document_name",
            "Document"
        )

        page_num = meta.get(
            "page_number",
            1
        )

        cid = c.get(
            "chunk_id",
            f"chunk-{idx}"
        )

        content = c.get(
            "content",
            ""
        ).strip()

        sentences = [
            s.strip()
            for s in content.split(".")
            if len(s.strip()) > 15
        ]

        key_snippet = (
            sentences[0]
            if sentences
            else content[:120]
        )

        citation_tag = (
            f"[Doc: {doc_name}, "
            f"Page: {page_num}, "
            f"Chunk: {cid}]"
        )

        response_lines.append(
            f"• {key_snippet}. {citation_tag}"
        )

        citations.append(
            CitationResponse(
                document_id=meta.get(
                    "document_id",
                    ""
                ),
                document_name=doc_name,
                chunk_id=cid,
                page_number=page_num,
                snippet=(
                    content[:250] + "..."
                    if len(content) > 250
                    else content
                ),
                relevance_score=float(
                    c.get(
                        "rerank_score",
                        c.get("hybrid_score", 0.85)
                    )
                )
            )
        )

    answer = "\n".join(response_lines)

    return (
        answer,
        citations,
        True,
        {
            "prompt_tokens": 150,
            "completion_tokens": 80
        }
    )


class GeminiGenerator:

    def __init__(self):
        self.model_name = settings.GEMINI_MODEL

    def generate(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        intent: str
    ) -> Tuple[
        str,
        List[CitationResponse],
        bool,
        Dict[str, Any]
    ]:

        if not retrieved_chunks:

            answer = (
                "The provided documents do not contain sufficient "
                "information to answer this question."
            )

            return (
                answer,
                [],
                False,
                {
                    "prompt_tokens": 0,
                    "completion_tokens": 15
                }
            )

        # ---------------------------------------
        # Configure Gemini
        # ---------------------------------------

        client = _configure_gemini()

        if client is None:

            logger.info(
                "GEMINI_API_KEY is not configured. "
                "Using local grounded synthesis fallback."
            )

            return _local_grounded_synthesis(
                query,
                retrieved_chunks,
                intent
            )

        # ---------------------------------------
        # Build RAG prompt
        # ---------------------------------------

        formatted_context = build_context_string(
            retrieved_chunks
        )

        user_prompt = USER_PROMPT_TEMPLATE.format(
            formatted_context=formatted_context,
            query=query,
            intent=intent
        )

        try:

            # New Google GenAI SDK
            from google.genai import types

            response = client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                    max_output_tokens=1024,
                )
            )

            answer_text = ""

            if response.text:
                answer_text = response.text.strip()

            # ---------------------------------------
            # Grounding check
            # ---------------------------------------

            is_grounded = True

            insufficient_phrases = [
                "do not contain sufficient information",
                "does not contain sufficient information",
                "insufficient information to answer",
                "not enough information provided"
            ]

            if any(
                phrase in answer_text.lower()
                for phrase in insufficient_phrases
            ):
                is_grounded = False

            # ---------------------------------------
            # Extract citations
            # ---------------------------------------

            citations = extract_citations(
                answer_text,
                retrieved_chunks
            )

            # ---------------------------------------
            # Approximate token counts
            # ---------------------------------------

            prompt_tokens = (
                len(user_prompt.split())
                + len(SYSTEM_PROMPT.split())
            )

            completion_tokens = len(
                answer_text.split()
            )

            return (
                answer_text,
                citations,
                is_grounded,
                {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens
                }
            )

        except Exception as e:

            logger.error(
                f"Error calling Gemini API: {e}. "
                "Falling back to local grounded synthesis.",
                exc_info=True
            )

            return _local_grounded_synthesis(
                query,
                retrieved_chunks,
                intent
            )


# Global singleton generator instance
gemini_generator = GeminiGenerator()