"""Background execution and status storage for executive-summary requests."""

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any, Dict, Optional
from uuid import uuid4

from app.core.config import settings
from app.models.adapters.openai_adapter import OpenAIAdapter


_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="executive-summary")
_jobs: Dict[str, Dict[str, Any]] = {}
_jobs_lock = Lock()


def _run_summary(job_id: str, test_id: int, context: str) -> None:
    """Run OpenAI work outside the request thread and record its outcome."""
    try:
        adapter = OpenAIAdapter(
            api_key=settings.OPENAI_API_KEY or "",
            model=settings.OPENAI_MODEL,
            timeout=settings.EXECUTIVE_SUMMARY_TIMEOUT_SECONDS,
            max_retries=settings.EXECUTIVE_SUMMARY_MAX_RETRIES,
        )
        summary = adapter.generate_executive_summary(
            settings.EXECUTIVE_SUMMARY_SYSTEM_PROMPT,
            context,
        )
        result = {
            "test_id": test_id,
            "job_id": job_id,
            "status": "completed",
            "executive_summary": summary,
        }
    except Exception as exc:
        result = {
            "test_id": test_id,
            "job_id": job_id,
            "status": "failed",
            "error": f"Executive Summary could not be generated: {exc}",
        }

    with _jobs_lock:
        _jobs[job_id] = result


def start_summary_job(test_id: int, context: str) -> str:
    """Start an executive-summary job and return its opaque identifier."""
    job_id = uuid4().hex
    with _jobs_lock:
        _jobs[job_id] = {
            "test_id": test_id,
            "job_id": job_id,
            "status": "processing",
        }
    _executor.submit(_run_summary, job_id, test_id, context)
    return job_id


def get_summary_job(job_id: str, test_id: int) -> Optional[Dict[str, Any]]:
    """Return a job only when it belongs to the requested security test."""
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job or job.get("test_id") != test_id:
            return None
        return dict(job)
