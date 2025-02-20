# /config/settings.py
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    UPLOAD_DIR: Path = BASE_DIR / "data/uploads"  # Now an absolute path
    FAISS_INDEX: Path = BASE_DIR / "data/faiss_index.bin"
    SCHEMA_MAPPING: Path = BASE_DIR / "data/schema_mapping.json"
    
    # Model paths
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    
    # API configurations
    GROQ_API_KEY: str = "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"
    MAX_UPLOAD_SIZE_MB: int = 50
    
    class Config:
        env_file = ".env"

settings = Settings()