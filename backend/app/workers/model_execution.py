import redis
from rq import Queue, Worker
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import get_session_local
from app.services.test_orchestrator import TestOrchestrator

# Redis connection
redis_conn = redis.from_url(settings.REDIS_URL)
queue = Queue(connection=redis_conn)


def execute_model_run_job(variant_id: int, model_config: dict, test_id: int):
    """
    RQ worker task: Execute a single model run
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    try:
        # Execute the model run
        model_run = TestOrchestrator.execute_model_run(
            db=db,
            variant_id=variant_id,
            model_config=model_config
        )
        
        # Update test status
        TestOrchestrator.update_test_status(db, test_id)
        
        return {
            "status": "success",
            "model_run_id": model_run.id,
            "test_id": test_id
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "test_id": test_id
        }
    finally:
        db.close()


def generate_variants_job(test_id: int, count_per_technique: int = 2):
    """
    RQ worker task: Generate variants for a test
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    try:
        count = TestOrchestrator.generate_variants_for_test(
            db=db,
            test_id=test_id,
            count_per_technique=count_per_technique
        )
        
        return {
            "status": "success",
            "test_id": test_id,
            "variants_generated": count
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "test_id": test_id
        }
    finally:
        db.close()


def start_worker():
    """Start the RQ worker"""
    worker = Worker([queue], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    start_worker()
