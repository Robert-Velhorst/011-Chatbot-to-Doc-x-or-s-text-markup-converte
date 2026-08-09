from __future__ import annotations

import secrets
import threading
import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import Settings


class SessionStore:
    """Keep short-lived browser sessions in memory so no credential is persisted."""

    def __init__(self) -> None:
        self._sessions: dict[str, float] = {}
        self._lock = threading.Lock()

    def issue(self, ttl_seconds: int = 8 * 60 * 60) -> str:
        value = secrets.token_urlsafe(32)
        now = time.monotonic()
        with self._lock:
            self._purge(now)
            self._sessions[value] = now + ttl_seconds
        return value

    def valid(self, value: str) -> bool:
        if not value:
            return False
        now = time.monotonic()
        with self._lock:
            self._purge(now)
            expires_at = self._sessions.get(value)
            return expires_at is not None and expires_at > now

    def revoke(self, value: str | None) -> None:
        if not value:
            return
        with self._lock:
            self._sessions.pop(value, None)

    def _purge(self, now: float) -> None:
        expired = [value for value, expires_at in self._sessions.items() if expires_at <= now]
        for value in expired:
            self._sessions.pop(value, None)


class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings, sessions: SessionStore):
        super().__init__(app)
        self.settings = settings
        self.sessions = sessions
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/"):
            if self.settings.token and request.url.path != "/api/session":
                supplied = request.headers.get("authorization", "")
                token = (
                    supplied[7:]
                    if supplied.lower().startswith("bearer ")
                    else request.headers.get("x-clean-paste-token", "")
                )
                cookie = request.cookies.get("clean_paste_session", "")
                authorized = secrets.compare_digest(
                    token, self.settings.token
                ) or self.sessions.valid(cookie)
                if not authorized:
                    return JSONResponse({"detail": "Authentication required"}, status_code=401)
            client = request.client.host if request.client else "local"
            if self._limited(client):
                return JSONResponse(
                    {"detail": "Rate limit exceeded"},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        )
        response.headers["Cache-Control"] = (
            "no-store" if request.url.path.startswith("/api/") else "no-cache"
        )
        return response

    def _limited(self, client: str) -> bool:
        now = time.monotonic()
        cutoff = now - 60
        with self._lock:
            bucket = self._requests[client]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.settings.rate_limit_per_minute:
                return True
            bucket.append(now)
            return False
