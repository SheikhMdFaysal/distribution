from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Enterprise AI Security Red Teaming Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ai_security_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Model Configuration
    OPENAI_MODEL: str = "gpt-4"
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    GOOGLE_MODEL: str = "gemini-1.5-pro"
    
    # Local Models (Ollama)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_KEYS: str = "demo-api-key-123"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # Model API Timeouts
    MODEL_TIMEOUT_SECONDS: int = 30
    MODEL_MAX_RETRIES: int = 3
    
    # Test Configuration
    DEFAULT_VARIANTS_PER_TECHNIQUE: int = 2
    MAX_BASELINE_PROMPTS: int = 50
    MAX_CONCURRENT_RUNS: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
