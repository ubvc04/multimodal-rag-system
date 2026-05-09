"""Application configuration settings."""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic settings loaded from environment variables."""

    # App
    APP_NAME: str = "Multimodal RAG API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_CHAT_MODEL: str = "gpt-4-turbo"
    OPENAI_MAX_TOKENS: int = 2048
    OPENAI_TEMPERATURE: float = 0.1

    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME: str = "rag-multimodal"
    PINECONE_DIMENSION: int = 3072
    PINECONE_METRIC: str = "cosine"
    PINECONE_TOP_K: int = 10

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 3600

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # File upload
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: list[str] = ["pdf", "docx", "txt", "png", "jpg", "jpeg", "csv", "xlsx"]
    UPLOAD_DIR: str = "/tmp/uploads"

    # Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Agent
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT_SECONDS: int = 60

    # AWS
    AWS_REGION: str = "us-east-1"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        """Ensure asyncpg is used for async SQLAlchemy connections."""
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must start with 'postgresql+asyncpg://'")
        return value

    @property
    def sync_database_url(self) -> str:
        """Return sync URL for Alembic by swapping asyncpg with psycopg2."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


settings = Settings()
