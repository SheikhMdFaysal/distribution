"""API-key authentication for state-changing / expensive endpoints.

The public static demo frontend issues read-only calls with no credentials, so
GET routes stay open. Write and cost-incurring routes (running tests, deleting,
cancelling, generating variants, executive summaries) require a valid API key
supplied via the `X-API-Key` header (or `Authorization: Bearer <key>`).

Valid keys come from the `API_KEYS` setting (comma-separated). In production the
default placeholder key is rejected so the app fails loudly instead of shipping
a known-public credential.
"""
from typing import Optional, Set

from fastapi import Header, HTTPException, status

from app.core.config import settings

_PLACEHOLDER_KEYS = {"demo-api-key-123", ""}


def _valid_keys() -> Set[str]:
    return {k.strip() for k in settings.API_KEYS.split(",") if k.strip()}


def require_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    authorization: Optional[str] = Header(default=None),
) -> str:
    """FastAPI dependency that enforces a valid API key on protected routes."""
    keys = _valid_keys()

    # Fail loudly rather than accepting a known placeholder credential outside dev.
    if not settings.DEBUG and (not keys or keys <= _PLACEHOLDER_KEYS):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured. Set API_KEYS to a non-default value.",
        )

    provided = x_api_key
    if not provided and authorization and authorization.lower().startswith("bearer "):
        provided = authorization[7:].strip()

    if not provided or provided not in keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key.",
            headers={"WWW-Authenticate": "X-API-Key"},
        )

    return provided
