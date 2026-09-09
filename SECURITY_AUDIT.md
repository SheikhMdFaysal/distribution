# Security Audit — AI Health Checkup / Red-Teaming Platform

**Scope:** FastAPI backend (`backend/app`) + static/Next.js frontend
**Type:** Read-only audit, followed by targeted hardening fixes
**Branch with fixes:** `v0/security-hardening`

---

## 1. Executive Summary

The platform is functionally rich and the database layer is sound (all access
goes through SQLAlchemy ORM with bound parameters — no SQL injection). However,
the API was fully public with no authentication, no rate limiting, exposed docs,
and hardcoded fallback secrets, leaving a money-spending LLM endpoint wide open.
A guaranteed 500 crash existed in PDF export, and a Google API key prefix was
being logged.

The highest-impact fixes (auth on write routes, rate limiting on the run
endpoint, gated docs, removed secret defaults, stopped key logging, and the PDF
crash) have been applied. Remaining items are documented as recommendations.

---

## 2. Findings by Severity

### Critical / High

| # | Finding | Location | Status |
|---|---------|----------|--------|
| 1 | **No authentication/authorization on any endpoint.** All routes public; anyone could run tests, delete tests, export, and read all data. Auth deps (`python-jose`, `passlib`, `API_KEYS`, `SECRET_KEY`) existed but were wired nowhere. | `security_tests.py`, `variants.py`, `analytics.py`, `health.py` | **Fixed (writes)** |
| 2 | **No rate limiting → cost-based DoS.** `POST /security-tests/run` executes paid LLM calls synchronously in a triple-nested loop with no cap on `baseline_prompts`. `slowapi` present but unused. | `security_tests.py`, `main.py` | **Fixed** |
| 3 | **Interactive API docs public.** `/api/docs` and `/api/redoc` exposed the full unauthenticated API surface. | `main.py` | **Fixed** |
| 4 | **Hardcoded fallback secrets.** `SECRET_KEY = "your-secret-key-change-in-production"` and `API_KEYS = "demo-api-key-123"` shipped as defaults; app ran silently with known secrets if env vars were missing. | `core/config.py` | **Fixed** |

### Medium

| # | Finding | Location | Status |
|---|---------|----------|--------|
| 5 | **PDF export guaranteed 500.** Code referenced `test.target_vendor` / `test.target_model`, which do not exist on `SecurityTest` (only `target_models`, a JSON list). Every `?format=pdf` raised `AttributeError`. | `security_tests.py` ~L562 | **Fixed** |
| 6 | **API key leaked to logs.** `print(api_key[:20])` exposed 20 chars of a Google API key in runtime logs. | `google_adapter.py:32` | **Fixed** |
| 7 | **Adapter errors laundered into "responses".** Exceptions/absent SDK returned fake `"[Error: ...]"` / `"[Simulated ...]"` strings that were then fed to the leakage detector and stored as real model output. | `openai_adapter.py` (+ others) | Recommended |
| 8 | **Executive-summary jobs in in-process dict.** `_jobs` module-level dict is lost on restart and not shared across instances/workers; polling can 404 or hang under multi-instance deploys. | `executive_summary_jobs.py` | Recommended |
| 9 | **Blocking work in the request handler.** Run endpoint does all model I/O synchronously despite Redis + RQ being configured — causes 502/timeout under load. | `security_tests.py`, `workers/model_execution.py` | Recommended |

### Low / Code Quality

| # | Finding | Status |
|---|---------|--------|
| 10 | CORS: `allow_credentials=True` with `allow_methods=["*"]`/`allow_headers=["*"]` is fragile; breaks if `ALLOWED_ORIGINS="*"`. | Recommended |
| 11 | N+1 queries in `get_security_test`, `export_test_results`, `_build_executive_summary_context` (lazy walk of relationships). Use `selectinload`. | Recommended |
| 12 | Leakage detection is naive regex with likely high false positives. | Recommended |
| 13 | `/models` hardcodes a list that diverges from `config.py` defaults (`gpt-4` vs `gpt-4o-mini`). | Recommended |
| 14 | Repo hygiene: committed `desktop.ini`, `Downloads - Shortcut.lnk`, `RUN.bat`, `start_all.bat` artifacts. | Recommended |

### What's Solid
- All DB access via SQLAlchemy ORM with bound parameters — **no SQL injection**.
- Well-reasoned connection-pool sizing and resilient background-bootstrap logic.
- Bounded pagination (`ge`/`le` on limit/offset); export `format` param regex-validated.
- Executive-summary job lookups correctly scoped by `test_id` (no cross-read).

---

## 3. Fixes Applied

Decision taken: **protect writes, keep reads open** (so the static demo frontend
keeps working for read/display), plus PDF crash, run rate limiting, gated docs,
removed secret defaults, and stopped logging the API key.

### 3.1 Authentication — `backend/app/core/auth.py` (new)
- New `require_api_key` dependency validating `X-API-Key` or `Authorization: Bearer`.
- Applied to cost/write routes only:
  - `POST /security-tests/run`
  - `DELETE /security-tests/{id}`
  - `POST /security-tests/{id}/cancel`
  - `POST /security-tests/{id}/executive-summary`
  - `POST /variants/generate`
- All `GET` reads remain public.
- Fails loudly (503) in production if `API_KEYS` is unset or still a placeholder.

### 3.2 Rate limiting — `backend/app/core/rate_limit.py` (new)
- Shared `slowapi` limiter wired into `main.py` with a `429` handler.
- `POST /security-tests/run` capped at `5/minute`.
- `MAX_BASELINE_PROMPTS` cap now enforced so the model-call fan-out can't run unbounded.

### 3.3 Docs gating — `main.py`
- `/api/docs`, `/api/redoc`, and `openapi.json` served only when `DEBUG` is on.

### 3.4 Secret hygiene — `config.py` + `google_adapter.py`
- Removed hardcoded `SECRET_KEY` / `API_KEYS` fallbacks; dev-only defaults via
  validator, strict in production.
- Google adapter no longer logs a key prefix.

### 3.5 PDF export crash — `security_tests.py`
- Replaced non-existent `test.target_vendor` / `test.target_model` with values
  derived from the real `target_models` JSON list. `?format=pdf` no longer 500s.

---

## 4. Action Items For You (outside the code)

1. **Set `API_KEYS`** in the environment (comma-separated allowed keys) and pass
   the key from a trusted context. The static demo frontend and any `window.open`
   PDF export now need an API key for write/export calls.
2. **Set a strong `SECRET_KEY`** in production (e.g. `openssl rand -base64 32`).
3. Confirm `DEBUG=false` in production so docs stay gated.

---

## 5. Recommended Next Steps (not yet applied)

1. **Stop laundering adapter errors** — raise on failure (like
   `generate_executive_summary` already does) instead of returning fake response
   strings that corrupt detection results.
2. **Move job state out of process** — back `executive_summary_jobs` with Redis
   so polling survives restarts and multi-instance deploys.
3. **Offload model execution to RQ** — use the already-configured Redis + RQ
   worker instead of blocking the request handler; return a job id and poll.
4. **Fix N+1 queries** — add `selectinload` for
   `baseline_prompts → variants → model_runs → evaluation`.
5. **Tighten CORS** — explicit origins, methods, and headers; avoid `"*"` with
   `allow_credentials=True`.
6. **Harden leakage detection** — reduce false positives; consider a scored /
   classifier-based approach over raw regex.
7. **Single source of truth for models** — derive `/models` from `config.py`.
8. **Repo hygiene** — remove `desktop.ini`, `.lnk`, and `.bat` artifacts; add to
   `.gitignore`.

---

## 6. Files Changed

| File | Change |
|------|--------|
| `backend/app/core/auth.py` | **new** — API key dependency |
| `backend/app/core/rate_limit.py` | **new** — shared slowapi limiter |
| `backend/app/core/config.py` | removed secret defaults; dev validator |
| `backend/app/main.py` | gated docs; wired limiter + 429 handler |
| `backend/app/api/routes/security_tests.py` | auth on writes; rate limit + cap on run; PDF fix |
| `backend/app/api/routes/variants.py` | auth on `POST /variants/generate` |
| `backend/app/models/adapters/google_adapter.py` | removed API key logging |
