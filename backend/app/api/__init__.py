from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.documents import router as documents_router
from app.api.query import router as query_router
from app.api.evaluation import router as evaluation_router
from app.api.observability import router as observability_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(documents_router)
api_router.include_router(query_router)
api_router.include_router(evaluation_router)
api_router.include_router(observability_router)

__all__ = ["api_router"]
