import pytest
from app.evaluation.ragas_evaluator import ragas_evaluator


def test_ragas_metric_computation():
    question = "What was the total revenue in Q3?"
    contexts = [
        "In Q3, consolidated revenue reached $48.2 million, growing 24.5% year over year.",
        "Operating expenses rose 12% to $29.4 million."
    ]
    answer = "Consolidated revenue in Q3 reached $48.2 million with a 24.5% growth rate [Doc: Report, Page: 1, Chunk: c1]."
    ground_truth = "Q3 revenue was $48.2 million."

    metrics = ragas_evaluator.evaluate_sample(
        question=question,
        answer=answer,
        contexts=contexts,
        ground_truth=ground_truth
    )

    assert 0.0 <= metrics["faithfulness"] <= 1.0
    assert 0.0 <= metrics["answer_relevancy"] <= 1.0
    assert 0.0 <= metrics["context_precision"] <= 1.0
    assert 0.0 <= metrics["context_recall"] <= 1.0

    # Faithfulness should be high since the facts are directly from the context
    assert metrics["faithfulness"] >= 0.7
    assert metrics["context_recall"] >= 0.7


def test_ragas_insufficient_information_handling():
    question = "What is the employee ID of the CEO?"
    contexts = ["Company policies dictate strict adherence to safety standards."]
    answer = "The provided documents do not contain sufficient information to answer this question."

    metrics = ragas_evaluator.evaluate_sample(
        question=question,
        answer=answer,
        contexts=contexts
    )

    # When the model correctly identifies insufficient info, faithfulness is preserved
    assert metrics["faithfulness"] >= 0.8
