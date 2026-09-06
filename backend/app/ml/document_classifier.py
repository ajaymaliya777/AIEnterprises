import logging
from typing import Tuple, Dict
import numpy as np

logger = logging.getLogger(__name__)

DOCUMENT_CATEGORIES = {
    "Financial Report": [
        "Consolidated balance sheet, cash flows, revenue growth, EBITDA, assets, liabilities, and quarterly earnings.",
        "Financial statements, fiscal year audited reports, balance sheets, and operating margins.",
        "Tax compliance, investment portfolio summary, and capital expenditure breakdown.",
    ],
    "Legal Contract / Compliance": [
        "Mutual non-disclosure agreement, governing law, terms and conditions, dispute resolution, and liability indemnification.",
        "Master services agreement, intellectual property rights, termination clause, confidentiality obligations, and jurisdiction.",
        "Regulatory compliance policy, anti-money laundering, code of conduct, and statutory obligations.",
    ],
    "Technical Specification": [
        "System architecture specification, API endpoints, microservices, database schemas, and network protocols.",
        "Software requirements specification, deployment guide, infrastructure topology, and algorithmic complexity.",
        "Engineering manual, system telemetry, latency benchmarks, and unit testing specifications.",
    ],
    "Executive Memo / HR": [
        "Internal company memorandum, corporate leadership announcement, employee handbook, and benefits guide.",
        "Performance review standards, workplace harassment policy, organizational chart, and annual leave guidelines.",
        "Executive strategy briefing, board meeting minutes, and corporate organizational update.",
    ],
    "General": [
        "General business correspondence, miscellaneous documentation, notes, and informational articles.",
    ]
}


class DocumentDomainClassifier:
    """
    ML Document Domain Classifier using SentenceTransformer embeddings.
    Categorizes enterprise documents into operational domains upon ingestion.
    """

    def __init__(self, embedding_model=None):
        self.model = embedding_model
        self.category_prototypes: Dict[str, np.ndarray] = {}

    def _ensure_prototypes(self):
        if self.category_prototypes:
            return

        if self.model is None:
            from sentence_transformers import SentenceTransformer
            from app.config import settings
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

        for category, exemplars in DOCUMENT_CATEGORIES.items():
            embeddings = self.model.encode(exemplars, normalize_embeddings=True)
            centroid = np.mean(embeddings, axis=0)
            centroid = centroid / np.linalg.norm(centroid)
            self.category_prototypes[category] = centroid

    def classify_text(self, text_sample: str) -> Tuple[str, float]:
        """
        Classifies document based on text sample (e.g. first 2000 characters).
        Returns: (category_name, confidence_score)
        """
        if not text_sample or len(text_sample.strip()) < 30:
            return "General", 0.5

        try:
            self._ensure_prototypes()
            sample = text_sample[:2000]
            sample_vec = self.model.encode([sample], normalize_embeddings=True)[0]

            scores = {}
            for cat, proto_vec in self.category_prototypes.items():
                cosine_sim = float(np.dot(sample_vec, proto_vec))
                scores[cat] = cosine_sim

            exp_scores = {k: np.exp(v * 4.0) for k, v in scores.items()}
            total_exp = sum(exp_scores.values())
            probs = {k: v / total_exp for k, v in exp_scores.items()}

            best_cat = max(probs, key=probs.get)
            confidence = float(probs[best_cat])

            logger.info(f"Document classified as '{best_cat}' (confidence={confidence:.3f})")
            return best_cat, confidence

        except Exception as e:
            logger.warning(f"Error in ML document classification: {e}. Falling back to 'General'.")
            return "General", 1.0


# Global singleton instance
document_classifier = DocumentDomainClassifier()
