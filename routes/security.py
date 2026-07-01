"""
Security middleware for Hombre: rate limiting, request logging, role-based auth.

Roles:
  admin   – full access (create, delete, settings, export, import)
  editor  – create/edit peers, sessions, chat; no delete/settings
  viewer  – read-only (view, export)

Configuration via environment variables:
  DASHBOARD_USER / DASHBOARD_PASSWORD          – single-user (backward compat)
  DASHBOARD_USERS=user1:pass1:admin,user2:pass2:viewer  – multi-user
  HOMBRE_LOG_DIR                               – log directory (default: logs)
"""

from __future__ import annotations

import base64
import hmac
import logging
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

log = logging.getLogger("hombre")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HONCHO_URL = os.environ.get("HONCHO_URL", "http://localhost:8000")
LOG_DIR = Path(os.environ.get("HOMBRE_LOG_DIR", "logs"))

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin":  {"read", "write", "delete", "settings", "export", "import"},
    "editor": {"read", "write", "export"},
    "viewer": {"read", "export"},
}

# Endpoint → required permission
# POST/PUT/DELETE on /api/settings/*    → settings
# DELETE on /api/workspaces/*           → delete
# POST on /api/workspaces/* (create)    → write
# POST /api/peers/*, /api/sessions/*    → write
# Everything else (GET)                 → read

# Rate limits: (requests_per_minute, path_prefix)
RATE_LIMITS: list[tuple[int, str]] = [
    (5,   "/api/settings/"),
    (5,   "/api/workspaces/"),  # covers deletes (expensive)
    (30,  "/api/peers/"),
    (30,  "/api/sessions/"),
    (30,  "/api/messages/"),
    (5,   "/api/chat"),         # chat endpoint (expensive)
]
DEFAULT_RATE_LIMIT = 60  # requests/minute for unlisted endpoints

RATE_LIMIT_WINDOW = 60  # seconds


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------

class RateLimiter:
    """Simple in-memory sliding-window rate limiter."""

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _client_key(self, request: Request) -> str:
        """Build a per-client rate-limit key from IP + user."""
        ip = request.client.host if request.client else "unknown"
        auth = request.headers.get("authorization", "")
        return f"{ip}:{auth[:20]}"

    def is_allowed(self, key: str, limit: int, window: int = RATE_LIMIT_WINDOW) -> bool:
        now = time.time()
        # Evict expired entries
        self._requests[key] = [t for t in self._requests[key] if now - t < window]
        if len(self._requests[key]) >= limit:
            return False
        self._requests[key].append(now)
        return True

    def get_limit(self, path: str) -> tuple[int, str]:
        """Return (limit, prefix) for the first matching rule."""
        for limit, prefix in RATE_LIMITS:
            if path.startswith(prefix):
                return limit, prefix
        return DEFAULT_RATE_LIMIT, ""

    def retry_after(self, key: str) -> int:
        """Seconds until the oldest request in the window expires."""
        if not self._requests[key]:
            return 0
        oldest = self._requests[key][0]
        return max(1, int(RATE_LIMIT_WINDOW - (time.time() - oldest)))


# ---------------------------------------------------------------------------
# Access Logger
# ---------------------------------------------------------------------------

class AccessLogger:
    """Rotating access log writer."""

    def __init__(self, log_dir: Path = LOG_DIR) -> None:
        self._log_dir = log_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._log_dir / "access.log"
        self._rotate()

    def _rotate(self) -> None:
        """Rotate log if > 5 MB."""
        try:
            if self._log_file.exists() and self._log_file.stat().st_size > 5 * 1024 * 1024:
                ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                self._log_file.rename(self._log_dir / f"access-{ts}.log")
                # Prune old rotated logs (keep last 5)
                rotated = sorted(self._log_dir.glob("access-*.log"))
                for old in rotated[:-5]:
                    old.unlink(missing_ok=True)
        except OSError:
            pass

    def log(
        self,
        method: str,
        path: str,
        status: int,
        duration_ms: float,
        client_ip: str = "",
        user: str = "",
        detail: str = "",
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        parts = [
            now,
            method,
            str(status),
            f"{duration_ms:.1f}ms",
            path,
        ]
        if client_ip:
            parts.append(f"ip={client_ip}")
        if user:
            parts.append(f"user={user}")
        if detail:
            parts.append(detail)
        line = " ".join(parts) + "\n"
        try:
            self._rotate()
            with open(self._log_file, "a") as f:
                f.write(line)
        except OSError as e:
            log.warning("Failed to write access log: %s", e)


# ---------------------------------------------------------------------------
# User store (parsed from env)
# ---------------------------------------------------------------------------

def _parse_users() -> dict[str, dict[str, str]]:
    """
    Build users dict from environment.

    Supports two modes:
      1. Single user:  DASHBOARD_USER + DASHBOARD_PASSWORD + DASHBOARD_ROLE
      2. Multi user:   DASHBOARD_USERS=user1:pass1:admin,user2:pass2:viewer
    """
    users: dict[str, dict[str, str]] = {}

    multi = os.environ.get("DASHBOARD_USERS", "")
    if multi:
        for entry in multi.split(","):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split(":")
            if len(parts) == 3:
                uname, pwd, role = parts
                if role in ROLE_PERMISSIONS:
                    users[uname] = {"password": pwd, "role": role}
            elif len(parts) == 2:
                uname, pwd = parts
                users[uname] = {"password": pwd, "role": "admin"}
    else:
        user = os.environ.get("DASHBOARD_USER", "")
        pwd = os.environ.get("DASHBOARD_PASSWORD", "")
        role = os.environ.get("DASHBOARD_ROLE", "admin")
        if user and pwd:
            if role not in ROLE_PERMISSIONS:
                role = "admin"
            users[user] = {"password": pwd, "role": role}

    return users


# ---------------------------------------------------------------------------
# Middleware: Rate Limiting
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.limiter = RateLimiter()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip health and static
        if request.url.path.startswith("/static") or request.url.path == "/api/health":
            return await call_next(request)

        limit, prefix = self.limiter.get_limit(request.url.path)
        key = self.limiter._client_key(request)

        if not self.limiter.is_allowed(key, limit):
            retry = self.limiter.retry_after(key)
            log.warning(
                "Rate limit exceeded: %s %s (limit=%d/min)",
                request.method, request.url.path, limit,
            )
            return JSONResponse(
                {"error": "rate_limit_exceeded", "retry_after": retry},
                status_code=429,
                headers={"Retry-After": str(retry)},
            )
        return await call_next(request)


# ---------------------------------------------------------------------------
# Middleware: Request Logging
# ---------------------------------------------------------------------------

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.logger = AccessLogger()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000

        client_ip = request.client.host if request.client else "unknown"
        user = getattr(request.state, "user", "") or ""

        # Don't log static assets
        if not request.url.path.startswith("/static"):
            self.logger.log(
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user=user,
            )

        return response


# ---------------------------------------------------------------------------
# Middleware: Role-Based Authentication
# ---------------------------------------------------------------------------

class RoleBasedAuthMiddleware(BaseHTTPMiddleware):
    """
    Enhanced Basic Auth with role support.

    Backward-compatible: if DASHBOARD_USER/DASHBOARD_PASSWORD are set, that
    user gets admin role. If DASHBOARD_USERS is set, multi-user mode.

    Sets request.state.user, request.state.role, request.state.permissions.
    """

    # Paths that require the 'settings' permission (POST/PUT/DELETE)
    _SETTINGS_METHODS = {"POST", "PUT", "DELETE"}
    # Patterns for destructive operations requiring 'delete' permission
    _DELETE_PATTERNS = [
        re.compile(r"^/api/workspaces/[^/]+$"),             # DELETE workspace
        re.compile(r"^/api/workspaces/[^/]+/sessions/[^/]+$"),  # DELETE session
    ]

    def __init__(self, app) -> None:
        super().__init__(app)
        self.users = _parse_users()
        self._401 = JSONResponse(
            {"error": "unauthorized"},
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Hombre"'},
        )
        if not self.users:
            log.warning(
                "No DASHBOARD_USER/DASHBOARD_PASSWORD or DASHBOARD_USERS set — "
                "authentication disabled (open access)"
            )

    def _check_basic_auth(self, auth_header: str) -> tuple[str, str] | None:
        """Return (username, role) or None."""
        if not auth_header.startswith("Basic "):
            return None
        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            user, _, password = decoded.partition(":")
        except Exception:
            return None

        for uname, info in self.users.items():
            if hmac.compare_digest(user, uname) and hmac.compare_digest(password, info["password"]):
                return uname, info["role"]
        return None

    def _infer_permission(self, request: Request) -> str:
        """Infer the required permission for this request."""
        path = request.url.path
        method = request.method

        # Settings endpoints
        if path.startswith("/api/settings/") and method in self._SETTINGS_METHODS:
            return "settings"

        # Delete operations
        if method == "DELETE":
            for pat in self._DELETE_PATTERNS:
                if pat.match(path):
                    return "delete"
            # Generic DELETE fallback
            return "delete"

        # Write operations (POST/PUT)
        if method in {"POST", "PUT"}:
            return "write"

        # GET, HEAD → read
        return "read"

    def _has_permission(self, permissions: set[str], required: str) -> bool:
        return required in permissions

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip health and static
        if request.url.path.startswith("/static") or request.url.path == "/api/health":
            return await call_next(request)

        # No users configured → open access
        if not self.users:
            request.state.user = ""
            request.state.role = ""
            request.state.permissions = ROLE_PERMISSIONS["viewer"]
            return await call_next(request)

        auth = request.headers.get("authorization", "")
        result = self._check_basic_auth(auth)
        if result is None:
            return self._401

        username, role = result
        permissions = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["viewer"])

        # Set state for downstream use
        request.state.user = username
        request.state.role = role
        request.state.permissions = permissions

        # Check role-based permission
        required = self._infer_permission(request)
        if not self._has_permission(permissions, required):
            log.warning(
                "Access denied: user=%s role=%s required=%s path=%s",
                username, role, required, request.url.path,
            )
            return JSONResponse(
                {"error": "forbidden", "required_permission": required},
                status_code=403,
            )

        return await call_next(request)


# ---------------------------------------------------------------------------
# Middleware: Enhanced Security Headers
# ---------------------------------------------------------------------------

class EnhancedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds HSTS, XSS protection, improved CSP."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS (only on HTTPS or when behind proxy)
        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
        if proto == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # CSP - allow inline styles for modals, self for everything else
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self' fonts.googleapis.com fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )

        return response
