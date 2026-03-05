from fastapi import APIRouter
from datetime import datetime, timezone
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": "production" if not settings.DEBUG else "development"
    }

@router.get("/health/production")
def production_health_check():
    """Detailed health check for production monitoring"""
    # Check database
    try:
        from app.models.database import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"error: {str(e)}"
    
    # Check model API keys
    model_status = {
        "openai": bool(settings.OPENAI_API_KEY),
        "anthropic": bool(settings.ANTHROPIC_API_KEY),
        "google": bool(settings.GOOGLE_API_KEY)
    }
    
    return {
        "status": "healthy" if db_status == "connected" and redis_status == "connected" else "degraded",
        "version": settings.APP_VERSION,
        "environment": "production" if not settings.DEBUG else "development",
        "database": db_status,
        "redis": redis_status,
        "model_apis": model_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
