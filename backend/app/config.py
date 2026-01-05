"""
Configuration settings for WearSearch backend.
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""
    
    # App
    APP_NAME: str = "WearSearch"
    DEBUG: bool = True
    
    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    IMAGES_DIR: Path = DATA_DIR / "images"
    INDEX_DIR: Path = DATA_DIR / "index"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    
    # CLIP Model
    CLIP_MODEL: str = "ViT-B-32"
    CLIP_PRETRAINED: str = "openai"
    EMBEDDING_DIM: int = 512
    
    # Rocchio Algorithm Parameters
    ROCCHIO_ALPHA: float = 1.0  # Weight for original query
    ROCCHIO_BETA: float = 0.75  # Weight for relevant documents
    ROCCHIO_GAMMA: float = 0.15  # Weight for non-relevant documents
    
    # Pseudo Relevance Feedback
    PRF_TOP_K: int = 5  # Number of top documents to assume relevant
    
    # Search
    DEFAULT_TOP_K: int = 20
    MAX_TOP_K: int = 500
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/wearsearch.db"
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Create directories
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

