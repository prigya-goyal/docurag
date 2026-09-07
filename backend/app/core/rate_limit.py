"""
Rate limiting.

Keyed by authenticated user when available (falls back to IP for
unauthenticated routes like /auth/login and /auth/register, where limiting
by IP is exactly what you want to slow down credential-stuffing/brute force).

Limits are deliberately tiered: expensive LLM-backed routes (chat, compare,
summarize, evaluation) get tighter limits than cheap read routes, since
those are the ones that cost real money/quota per call.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def _rate_limit_key(request: Request) -> str:
    # Prefer the authenticated user (set by get_current_user via request.state)
    # so limits apply per-account rather than per-IP once logged in — this
    # matters for anyone behind a shared/NAT'd IP.
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return get_remote_address(request)


limiter = Limiter(key_func=_rate_limit_key, default_limits=["200/minute"])