import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
}


def tokenize(text: str) -> List[str]:
    """Tokenize, lowercase, and filter stopwords and non-alphanumerics."""
    tokens = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


class BM25Index:
    """
    BM25Okapi Lexical Search index for document chunks.
    Provides fast keyword-based sparse retrieval.
    """

    def __init__(self):
        self.chunk_ids: List[str] = []
        self.corpus_tokens: List[List[str]] = []
        self.metadata_store: Dict[str, Dict[str, Any]] = {}
        self.bm25: Optional[BM25Okapi] = None

    def add_documents(self, ids: List[str], texts: List[str], metadatas: List[Dict[str, Any]]):
        for chunk_id, text, meta in zip(ids, texts, metadatas):
            tokens = tokenize(text)
            self.chunk_ids.append(chunk_id)
            self.corpus_tokens.append(tokens)
            self.metadata_store[chunk_id] = meta

        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)

        logger.info(f"Updated BM25 index. Total chunks indexed: {len(self.chunk_ids)}")

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_document_ids: Optional[List[str]] = None
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        if not self.bm25 or not self.chunk_ids:
            return []

        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        doc_scores = self.bm25.get_scores(q_tokens)

        # Pair (score, index)
        scored_pairs = []
        filter_set = set(filter_document_ids) if filter_document_ids else None

        for idx, score in enumerate(doc_scores):
            if score <= 0:
                continue
            chunk_id = self.chunk_ids[idx]
            meta = self.metadata_store.get(chunk_id, {})

            if filter_set and meta.get("document_id") not in filter_set:
                continue

            scored_pairs.append((chunk_id, float(score), meta))

        # Sort descending by score
        scored_pairs.sort(key=lambda x: x[1], reverse=True)
        return scored_pairs[:top_k]

    def delete(self, ids: List[str]):
        ids_to_remove = set(ids)
        if not ids_to_remove or not self.chunk_ids:
            return

        new_ids = []
        new_corpus = []
        new_metas = {}

        for chunk_id, tokens in zip(self.chunk_ids, self.corpus_tokens):
            if chunk_id not in ids_to_remove:
                new_ids.append(chunk_id)
                new_corpus.append(tokens)
                new_metas[chunk_id] = self.metadata_store.get(chunk_id, {})

        self.chunk_ids = new_ids
        self.corpus_tokens = new_corpus
        self.metadata_store = new_metas

        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)
        else:
            self.bm25 = None

        logger.info(f"BM25 chunks deleted. Remaining: {len(self.chunk_ids)}")

    def delete_by_document_id(self, document_id: str):
        to_delete = [
            cid for cid, m in self.metadata_store.items()
            if m.get("document_id") == document_id
        ]
        if to_delete:
            self.delete(to_delete)

    def save(self, directory: str):
        save_dir = Path(directory)
        save_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "chunk_ids": self.chunk_ids,
            "corpus_tokens": self.corpus_tokens,
            "metadata_store": self.metadata_store,
        }
        with open(save_dir / "bm25_index.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self, directory: str) -> bool:
        load_dir = Path(directory)
        idx_file = load_dir / "bm25_index.json"
        if not idx_file.exists():
            return False

        try:
            with open(idx_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.chunk_ids = data["chunk_ids"]
            self.corpus_tokens = data["corpus_tokens"]
            self.metadata_store = data["metadata_store"]

            if self.corpus_tokens:
                self.bm25 = BM25Okapi(self.corpus_tokens)
            return True
        except Exception as e:
            logger.error(f"Error loading BM25 index from {directory}: {e}")
            return False

    def count(self) -> int:
        return len(self.chunk_ids)
