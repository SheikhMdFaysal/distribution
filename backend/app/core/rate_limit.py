"""Shared slowapi rate limiter.

Kept in its own module so both `main.py` (to register the middleware and error
handler) and the route modules (to apply `@limiter.limit(...)` decorators) can
import the same instance without a circular import.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# Default limit derived from configured requests-per-window.
DEFAULT_LIMIT = f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW}second"

limiter = Limiter(key_func=get_remote_address, default_limits=[DEFAULT_LIMIT])
