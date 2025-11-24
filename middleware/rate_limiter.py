"""
Rate Limiting Middleware
Prevents API abuse and ensures fair resource usage
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, Tuple
import redis
import json
import hashlib

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(
        self,
        requests_per_minute: int = 1000,
        requests_per_hour: int = 60000,
        requests_per_day: int = 1000000,
        use_redis: bool = False,
        redis_url: str = None
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day

        # Try to use Redis for distributed rate limiting
        self.redis_client = None
        if use_redis and redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Using Redis for distributed rate limiting")
            except:
                logger.warning("Redis not available, using in-memory rate limiting")

        # In-memory storage (fallback)
        self.requests = defaultdict(list)
        self.blocked_ips = {}

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Respect proxy headers when present (Render/ELB will set X-Forwarded-For)
        xff = request.headers.get("x-forwarded-for")
        if xff:
            client_ip = xff.split(",")[0].strip()
            if client_ip:
                return f"ip:{client_ip}"

        # Try to get user ID from request state (set by auth)
        if hasattr(request.state, "user_id") and request.state.user_id:
            return f"user:{request.state.user_id}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _check_redis_limit(self, client_id: str, limit: int, window: int) -> bool:
        """Check rate limit using Redis"""
        try:
            key = f"ratelimit:{client_id}:{window}"
            current = self.redis_client.incr(key)

            if current == 1:
                self.redis_client.expire(key, window)

            return current <= limit

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            return True  # Allow on error

    def _check_memory_limit(
        self,
        client_id: str,
        limit: int,
        window_seconds: int
    ) -> bool:
        """Check rate limit using in-memory storage"""
        now = time.time()
        window_start = now - window_seconds

        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]

        # Check limit
        if len(self.requests[client_id]) >= limit:
            return False

        # Add current request
        self.requests[client_id].append(now)
        return True

    def check_limit(self, request: Request) -> Tuple[bool, str]:
        """Check if request is within rate limits"""
        client_id = self._get_client_id(request)

        # Check if IP is blocked
        if client_id in self.blocked_ips:
            if self.blocked_ips[client_id] > datetime.utcnow():
                return False, "IP temporarily blocked due to rate limit violations"

        # Check different time windows
        checks = [
            (self.requests_per_minute, 60, "minute"),
            (self.requests_per_hour, 3600, "hour"),
            (self.requests_per_day, 86400, "day"),
        ]

        for limit, window, period in checks:
            if self.redis_client:
                allowed = self._check_redis_limit(client_id, limit, window)
            else:
                allowed = self._check_memory_limit(client_id, limit, window)

            if not allowed:
                # Block repeat offenders
                self._handle_violation(client_id)
                return False, f"Rate limit exceeded: {limit} requests per {period}"

        return True, "OK"

    def _handle_violation(self, client_id: str):
        """Handle rate limit violation"""
        # Temporary block for repeat offenders
        if client_id not in self.blocked_ips:
            self.blocked_ips[client_id] = datetime.utcnow() + timedelta(minutes=5)
            logger.warning(f"Temporarily blocked {client_id} for rate limit violations")

    def get_limits_for_client(self, request: Request) -> dict:
        """Get current limits and usage for client"""
        client_id = self._get_client_id(request)

        if self.redis_client:
            try:
                usage = {
                    "minute": int(self.redis_client.get(f"ratelimit:{client_id}:60") or 0),
                    "hour": int(self.redis_client.get(f"ratelimit:{client_id}:3600") or 0),
                    "day": int(self.redis_client.get(f"ratelimit:{client_id}:86400") or 0),
                }
            except:
                usage = {"minute": 0, "hour": 0, "day": 0}
        else:
            now = time.time()
            usage = {
                "minute": len([t for t in self.requests[client_id] if t > now - 60]),
                "hour": len([t for t in self.requests[client_id] if t > now - 3600]),
                "day": len([t for t in self.requests[client_id] if t > now - 86400]),
            }

        return {
            "limits": {
                "minute": self.requests_per_minute,
                "hour": self.requests_per_hour,
                "day": self.requests_per_day,
            },
            "usage": usage,
            "remaining": {
                "minute": max(0, self.requests_per_minute - usage["minute"]),
                "hour": max(0, self.requests_per_hour - usage["hour"]),
                "day": max(0, self.requests_per_day - usage["day"]),
            }
        }

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI"""

    def __init__(self, app, **kwargs):
        super().__init__(app)
        self.limiter = RateLimiter(**kwargs)

        # Paths to exclude from rate limiting
        self.excluded_paths = {
            "/health",
            "/api/v1/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/products/public",
            "/api/v1/products/public/"
        }

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Check rate limit
        allowed, message = self.limiter.check_limit(request)

        if not allowed:
            # Get limit info for headers
            limits = self.limiter.get_limits_for_client(request)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message,
                headers={
                    "X-RateLimit-Limit": str(limits["limits"]["minute"]),
                    "X-RateLimit-Remaining": str(limits["remaining"]["minute"]),
                    "X-RateLimit-Reset": str(int(time.time()) + 60),
                    "Retry-After": "60"
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        limits = self.limiter.get_limits_for_client(request)
        response.headers["X-RateLimit-Limit"] = str(limits["limits"]["minute"])
        response.headers["X-RateLimit-Remaining"] = str(limits["remaining"]["minute"])
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

        return response

# Per-endpoint rate limiting decorator
def rate_limit(
    requests_per_minute: int = 60,
    requests_per_hour: int = 600,
    key_func=None
):
    """Decorator for per-endpoint rate limiting"""
    limiter = RateLimiter(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour
    )

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Check rate limit
            allowed, message = limiter.check_limit(request)

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=message
                )

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
