from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    GEMINI_API_KEY: str
    DATABASE_URL: str = "sqlite:///./tasks.db"
    DEBUG: bool = False
    PROJECT_NAME: str = "AI Productivity Agent"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
