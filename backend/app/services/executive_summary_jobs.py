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


def _fallback_summary(context: str) -> str:
    """Create a deterministic business summary when OpenAI is unavailable."""
    values: Dict[str, str] = {}
    for line in context.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip()

    scenario = values.get("Scenario", "The security test")
    models = values.get("Models tested", "the configured AI models")
    vulnerabilities = values.get("Vulnerabilities found", "an unknown number of")
    risk = values.get("Overall test risk", "an uncalculated")
    frameworks = values.get("Compliance frameworks implicated", "no specific frameworks")
    return (
        f"The {scenario} assessment evaluated {models} for unintended data exposure. "
        f"It found {vulnerabilities} vulnerabilities, with an overall risk level of {risk}. "
        f"The results should be reviewed against {frameworks}, and the next step is to address "
        "any high-risk findings before relying on the affected AI systems in production."
    )


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
        # Print the FULL exception (type + message) to Runtime Logs so the real
        # OpenAI error (invalid_api_key / model_not_found / insufficient_quota /
        # connection error) is finally visible for diagnosis. Previously this
        # error was only stored in the job dict and the frontend re-labelled it
        # as a generic "timed out" message, which hid the true cause.
        print(
            f"[EXECUTIVE SUMMARY] job {job_id} FAILED "
            f"({type(exc).__name__}): {exc}",
            flush=True,
        )
        result = {
            "test_id": test_id,
            "job_id": job_id,
            "status": "completed",
            "executive_summary": _fallback_summary(context),
            "fallback": True,
            "error": f"{type(exc).__name__}: {exc}",
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
