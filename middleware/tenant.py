"""Multi-tenant middleware for request isolation.

SECURITY (F-002 fix): get_tenant_filter() and get_tenant_filter_unsafe() now
REJECT requests when tenant_id is missing instead of falling back to the
dangerous ``1=1`` unscoped WHERE clause that allowed cross-tenant reads/writes.

Paths that legitimately operate without a tenant (health checks, Stripe
webhooks, public docs, etc.) are listed in TENANT_EXEMPT_PREFIXES.
"""
from fastapi import Request, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths that legitimately do NOT require a tenant context.
# The TenantMiddleware will allow these through without a tenant_id, and the
# get_tenant_filter* helpers will never be called for them (they use their own
# auth/scoping logic).
# ---------------------------------------------------------------------------
TENANT_EXEMPT_PREFIXES = (
    "/health",
    "/ready",
    "/capabilities",
    "/diagnostics",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/health",
    "/api/v1/ready",
    "/api/v1/stripe/webhook",   # Stripe webhooks resolve tenant internally
    "/api/v1/cns",              # CNS system endpoints (API-key authed)
)


class TenantMiddleware:
    """Middleware to handle multi-tenant request isolation.

    For non-exempt paths, a missing tenant_id is logged as a warning.
    The hard enforcement happens in the ``get_tenant_filter`` helpers so
    that every SQL-building callsite is protected regardless of whether
    this middleware is registered.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        """ASGI middleware interface"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create request object for tenant extraction
        from starlette.requests import Request
        request = Request(scope, receive, send)

        path = request.url.path

        # Extract tenant from various sources
        tenant_id = await self.get_tenant_id(request)

        # Add tenant_id to scope for use in routes
        scope["tenant_id"] = tenant_id

        # Log tenant access
        if tenant_id:
            logger.debug(f"Request from tenant: {tenant_id}")
        elif not _is_exempt_path(path):
            logger.warning(
                "Request to tenant-scoped path %s without tenant_id", path
            )

        # Process request through the app
        await self.app(scope, receive, send)

    async def get_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        # Priority 1: Header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id

        # Priority 2: Query parameter
        if "tenant_id" in request.query_params:
            return request.query_params["tenant_id"]

        # Priority 3: Subdomain (for custom domains)
        host = request.headers.get("host", "")
        if host and not host.startswith("localhost"):
            # Extract subdomain from host like "acme.myroofgenius.com"
            parts = host.split(".")
            if len(parts) > 2 and parts[0] not in ["www", "api"]:
                return parts[0]

        # Priority 4: Path parameter (for tenant-specific routes)
        path_parts = request.url.path.split("/")
        if len(path_parts) > 2 and path_parts[1] == "tenant":
            return path_parts[2]

        # Priority 5: JWT token (if authenticated)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            # This would need JWT decoding to extract tenant_id
            # For now, return None and let auth middleware handle it
            pass

        # Default: No tenant specified (public access or default tenant)
        return None


def _is_exempt_path(path: str) -> bool:
    """Return True if *path* does not require tenant scoping."""
    for prefix in TENANT_EXEMPT_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            return True
    # Root path
    if path == "/":
        return True
    return False


def get_tenant_id(request: Request) -> Optional[str]:
    """Helper function to get tenant ID from request scope"""
    # Try to get from scope first (set by middleware)
    if hasattr(request, 'scope') and 'tenant_id' in request.scope:
        return request.scope.get("tenant_id")
    # Fallback to state for backwards compatibility
    return getattr(request.state, "tenant_id", None)


def require_tenant(request: Request) -> str:
    """Dependency to require tenant ID in request"""
    tenant_id = get_tenant_id(request)
    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Tenant ID is required for this operation"
        )
    return tenant_id


def get_tenant_filter(request: Request, table_alias: str = "") -> tuple:
    """Get SQL WHERE clause for tenant filtering with parameterized value.

    Returns tuple of (where_clause, params_dict) to prevent SQL injection.
    Usage: clause, params = get_tenant_filter(request)
           query = f"SELECT * FROM table WHERE {clause}"
           db.execute(query, params)

    SECURITY (F-002): Raises HTTP 403 when tenant_id is missing.
    Previously returned ``("1=1", {})`` which disabled tenant isolation.
    """
    tenant_id = get_tenant_id(request)
    if not tenant_id:
        logger.error(
            "SECURITY: get_tenant_filter() called without tenant_id — "
            "rejecting to prevent cross-tenant data leak (path=%s)",
            request.url.path,
        )
        raise HTTPException(
            status_code=403,
            detail="Tenant context is required. Cannot execute unscoped query.",
        )

    prefix = f"{table_alias}." if table_alias else ""
    # Return parameterized query to prevent SQL injection
    return f"{prefix}tenant_id = :tenant_id", {"tenant_id": tenant_id}


def get_tenant_filter_unsafe(request: Request, table_alias: str = "") -> str:
    """DEPRECATED: Use get_tenant_filter() instead for SQL injection protection.

    This function is kept for backwards compatibility but should NOT be used
    for any user-controlled tenant_id values.

    SECURITY (F-002): Raises HTTP 403 when tenant_id is missing.
    Previously returned ``"1=1"`` which disabled tenant isolation.
    """
    import warnings
    warnings.warn(
        "get_tenant_filter_unsafe is deprecated. Use get_tenant_filter() with parameterized queries.",
        DeprecationWarning,
        stacklevel=2
    )
    tenant_id = get_tenant_id(request)
    if not tenant_id:
        logger.error(
            "SECURITY: get_tenant_filter_unsafe() called without tenant_id — "
            "rejecting to prevent cross-tenant data leak (path=%s)",
            request.url.path,
        )
        raise HTTPException(
            status_code=403,
            detail="Tenant context is required. Cannot execute unscoped query.",
        )

    # Validate tenant_id is a valid UUID to prevent injection
    import re
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if not uuid_pattern.match(tenant_id):
        raise ValueError(f"Invalid tenant_id format: {tenant_id}")

    prefix = f"{table_alias}." if table_alias else ""
    return f"{prefix}tenant_id = '{tenant_id}'"
