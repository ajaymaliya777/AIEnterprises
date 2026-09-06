import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.evaluation import EvaluationRecord
from app.schemas.evaluation import EvaluationRunRequest, EvaluationResponse
from app.evaluation.ragas_evaluator import ragas_evaluator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluations", tags=["RAG Evaluation"])


@router.post("/run", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
def run_evaluation_benchmark(
    request: EvaluationRunRequest,
    db: Session = Depends(get_db)
):
    """
    Executes RAGAS evaluation across enterprise benchmark scenarios:
    Faithfulness, Answer Relevancy, Context Precision, and Context Recall.
    """
    try:
        result = ragas_evaluator.run_benchmark(
            sample_size=request.sample_size or 5,
            db_session=db
        )
        return EvaluationResponse(
            id=result["id"],
            run_name=result["run_name"],
            dataset_name=result["dataset_name"],
            sample_count=result["sample_count"],
            faithfulness=result["faithfulness"],
            answer_relevancy=result["answer_relevancy"],
            context_precision=result["context_precision"],
            context_recall=result["context_recall"],
            overall_score=result["overall_score"],
            details=result["details"],
            created_at=result["created_at"]
        )
    except Exception as e:
        logger.error(f"Evaluation run failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.get("", response_model=List[EvaluationResponse])
def get_evaluation_history(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    records = db.query(EvaluationRecord).order_by(EvaluationRecord.created_at.desc()).limit(limit).all()
    results = []
    for r in records:
        results.append(EvaluationResponse(
            id=r.id,
            run_name=r.run_name,
            dataset_name=r.dataset_name,
            sample_count=r.sample_count,
            faithfulness=r.faithfulness,
            answer_relevancy=r.answer_relevancy,
            context_precision=r.context_precision,
            context_recall=r.context_recall,
            overall_score=r.overall_score,
            details=r.details_json or [],
            created_at=r.created_at
        ))
    return results


@router.get("/{eval_id}", response_model=EvaluationResponse)
def get_evaluation_detail(eval_id: str, db: Session = Depends(get_db)):
    r = db.query(EvaluationRecord).filter(EvaluationRecord.id == eval_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evaluation with ID '{eval_id}' not found.")
    return EvaluationResponse(
        id=r.id,
        run_name=r.run_name,
        dataset_name=r.dataset_name,
        sample_count=r.sample_count,
        faithfulness=r.faithfulness,
        answer_relevancy=r.answer_relevancy,
        context_precision=r.context_precision,
        context_recall=r.context_recall,
        overall_score=r.overall_score,
        details=r.details_json or [],
        created_at=r.created_at
    )
