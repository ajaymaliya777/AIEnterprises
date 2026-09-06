import pytest
from app.ml.intent_classifier import intent_classifier, QueryIntent
from app.ml.document_classifier import document_classifier


def test_intent_classifier():
    # Out of scope / greeting
    intent, conf = intent_classifier.classify("Hello! How are you doing?")
    assert intent == QueryIntent.OUT_OF_SCOPE.value
    assert conf > 0.5

    # Factual lookup
    intent_fact, _ = intent_classifier.classify("What is the interest rate mentioned in clause 4?")
    assert intent_fact in [QueryIntent.FACTUAL_LOOKUP.value, QueryIntent.COMPARISON.value]

    # Summarization
    intent_sum, _ = intent_classifier.classify("Summarize the entire annual financial report and key takeaways.")
    assert intent_sum in [QueryIntent.SUMMARIZATION.value, QueryIntent.FACTUAL_LOOKUP.value]


def test_document_domain_classifier():
    # Financial sample
    fin_text = (
        "Consolidated Balance Sheet. Total revenue for the year reached $120 million. "
        "Operating expenses, EBITDA, and cash flows from operating activities are detailed below."
    )
    cat_fin, _ = document_classifier.classify_text(fin_text)
    assert cat_fin in ["Financial Report", "General"]

    # Legal sample
    legal_text = (
        "Mutual Non-Disclosure Agreement. The receiving party agrees to hold all Proprietary Information "
        "in strict confidence and shall not disclose it without prior written consent. Governing law of Delaware."
    )
    cat_legal, _ = document_classifier.classify_text(legal_text)
    assert cat_legal in ["Legal Contract / Compliance", "General"]
