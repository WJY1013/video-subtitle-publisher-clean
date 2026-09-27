from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    app_name: str = "GULF Video Subtitle Publisher"
    
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/gulf_db")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    minio_bucket: str = os.getenv("MINIO_BUCKET", "gulf-videos")
    
    upload_max_size: int = 5 * 1024 * 1024 * 1024
    allowed_video_formats: list = ["mp4", "mov", "avi", "mkv"]
    
    jwt_secret: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()
