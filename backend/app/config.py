from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "EnterpriseDoc AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://entrag.netlify.app",
        "*"
    ]

    # Database
    DATABASE_URL: str = "sqlite:///./data/enterprisedoc.db"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # Sentence Transformers / Embeddings
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384

    # Reranker
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Ingestion & Chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 75
    OCR_ENABLED: bool = True
    OCR_DENSITY_THRESHOLD: float = 0.05
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg", ".tiff"]

    # Retrieval
    RETRIEVAL_TOP_K_DENSE: int = 20
    RETRIEVAL_TOP_K_SPARSE: int = 20
    RETRIEVAL_TOP_K_RERANK: int = 5
    RRF_K: int = 60
    RRF_VECTOR_WEIGHT: float = 0.6
    RRF_LEXICAL_WEIGHT: float = 0.4

    # Langfuse
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: str = "./data/uploads"
    VECTOR_STORE_DIR: str = "./data/vector_store"

    @property
    def upload_path(self) -> Path:
        path = self.BASE_DIR / self.UPLOAD_DIR
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def vector_store_path(self) -> Path:
        path = self.BASE_DIR / self.VECTOR_STORE_DIR
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
