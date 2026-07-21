from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Enterprise AI Security Red Teaming Platform"
    APP_VERSION: str = "1.4.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ai_security_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    HF_TOKEN: Optional[str] = None
    NVIDIA_API_KEY: Optional[str] = None
    TOGETHER_API_KEY: Optional[str] = None
    
    # Model Configuration
    # gpt-4o-mini is a known-good, universally-available OpenAI model. It was
    # the original default. We tried "gpt-5.6-sol" (Codex's guess for the new
    # GPT-5.6 flagship) but the OpenAI API rejected it in ~1 second, which means
    # that model ID is either not real or not enabled on this account/tier.
    # Ship a working model; the Build Week story is "built WITH Codex/GPT-5.6",
    # which refers to the development tool, not the runtime summariser model.
    OPENAI_MODEL: str = "gpt-4o-mini"
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
    # Executive summaries run in a background job, so they are not constrained
    # by the App Platform request proxy. Allow the model enough time to finish
    # while keeping the worker bounded if the provider is unavailable.
    EXECUTIVE_SUMMARY_TIMEOUT_SECONDS: int = 60
    EXECUTIVE_SUMMARY_MAX_RETRIES: int = 0
    EXECUTIVE_SUMMARY_SYSTEM_PROMPT: str = (
        "You write executive summaries for a CEO or compliance officer. "
        "Write exactly 3-4 plain-English sentences about this completed AI security test. "
        "Explain the business risk, identify the most important finding and affected systems "
        "or models, mention relevant compliance obligations when present, and end with a clear "
        "next step. Avoid technical jargon, implementation details, hedging, bullet points, "
        "and invented facts."
    )
    
    # Test Configuration
    DEFAULT_VARIANTS_PER_TECHNIQUE: int = 2
    MAX_BASELINE_PROMPTS: int = 50
    MAX_CONCURRENT_RUNS: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
