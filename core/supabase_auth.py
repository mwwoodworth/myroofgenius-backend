"""
Supabase Authentication Integration
Replaces custom JWT authentication with Supabase Auth

This is the CORRECT way to handle authentication:
- Supabase manages user accounts, passwords, JWT tokens
- Backend validates Supabase JWT tokens via direct JWT decoding
- RLS policies enforce tenant isolation using JWT claims
"""

from supabase import create_client, Client
from fastapi import Header, HTTPException, Depends, Request
from typing import Dict, Any, Optional
import os
import logging
import jwt
from jwt import PyJWTError

logger = logging.getLogger(__name__)

# Supabase configuration (optional)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

SUPABASE_AVAILABLE = all([
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_JWT_SECRET,
])

supabase_anon: Optional[Client] = None
supabase_service: Optional[Client] = None

if SUPABASE_AVAILABLE:
    supabase_anon = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    supabase_service = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
else:
    logger.warning(
        "Supabase configuration not detected. Authentication middleware will run in offline mode."
    )

DEFAULT_OFFLINE_TENANT = os.getenv(
    "OFFLINE_TENANT_ID",
    "51e728c5-94e8-4ae0-8a0a-6a08d1fb3457"
)

OFFLINE_USER_CONTEXT: Dict[str, Any] = {
    "id": os.getenv("OFFLINE_SYSTEM_USER_ID", "offline-system-user"),
    "email": os.getenv("OFFLINE_SYSTEM_USER_EMAIL", "offline@brainops.local"),
    "tenant_id": DEFAULT_OFFLINE_TENANT,
    "user_metadata": {
        "tenant_id": DEFAULT_OFFLINE_TENANT,
        "role": os.getenv("OFFLINE_SYSTEM_USER_ROLE", "service"),
    },
    "app_metadata": {
        "tenant_id": DEFAULT_OFFLINE_TENANT,
        "role": os.getenv("OFFLINE_SYSTEM_USER_ROLE", "service"),
    },
    "role": os.getenv("OFFLINE_SYSTEM_USER_ROLE", "service"),
    "created_at": None,
    "last_sign_in_at": None,
}


async def get_current_user(authorization: str = Header(None)) -> Dict[str, Any]:
    """
    Get current user from Supabase Auth JWT token

    This replaces the custom JWT authentication.
    Frontend sends: Authorization: Bearer <supabase_jwt_token>

    Returns:
        dict: User info including id, email, tenant_id, metadata

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not SUPABASE_AVAILABLE:
        # Offline fallback: trust incoming request and return deterministic identity
        return OFFLINE_USER_CONTEXT.copy()

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract JWT token
    token = authorization.replace("Bearer ", "").strip()

    try:
        # Decode the JWT token with verification
        # Supabase JWTs are signed with HS256 using the JWT_SECRET
        audience = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
        
        try:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience=audience,
                options={"verify_aud": True}
            )
        except PyJWTError as jwt_error:
            logger.error(f"JWT verification error: {jwt_error}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )

        # Extract user information from JWT payload
        user_id = payload.get("sub")
        email = payload.get("email")
        user_metadata = payload.get("user_metadata", {})
        app_metadata = payload.get("app_metadata", {})
        role = payload.get("role", "authenticated")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user ID"
            )

        # Extract tenant_id from user metadata
        tenant_id = user_metadata.get("tenant_id")

        if not tenant_id:
            logger.warning(f"User {user_id} has no tenant_id in metadata")

        # Return user info in standardized format
        return {
            "id": user_id,
            "email": email,
            "tenant_id": tenant_id,
            "user_metadata": user_metadata,
            "app_metadata": app_metadata,
            "role": role,
            "created_at": payload.get("created_at"),
            "last_sign_in_at": payload.get("last_sign_in_at")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Supabase auth error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


async def get_supabase_client() -> Client:
    """
    Get Supabase client for service operations

    Use this for backend operations that need service-level access
    (creating users, admin operations, etc.)

    Returns:
        Client: Supabase client with service role privileges
    """
    if not SUPABASE_AVAILABLE or not supabase_service:
        raise RuntimeError("Supabase service client unavailable in offline mode.")
    return supabase_service


async def get_authenticated_user(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Retrieve the authenticated user, leveraging request state when available.

    Args:
        request: Current HTTP request.
        authorization: Authorization header (fallback when middleware not applied).

    Returns:
        dict: Authenticated user context.
    """
    user = getattr(request.state, "user", None)
    if user:
        return user
    return await get_current_user(authorization=authorization)


async def verify_tenant_access(
    user: Dict[str, Any] = Depends(get_current_user),
    required_tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verify user has access to specific tenant

    Args:
        user: Current user from get_current_user
        required_tenant_id: Tenant ID to check access for

    Returns:
        dict: User info if authorized

    Raises:
        HTTPException: If user doesn't have access to tenant
    """
    user_tenant_id = user.get("tenant_id")

    if not user_tenant_id:
        raise HTTPException(
            status_code=403,
            detail="User not assigned to any tenant"
        )

    if required_tenant_id and user_tenant_id != required_tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied: insufficient tenant permissions"
        )

    return user


def require_role(required_role: str):
    """
    Dependency to require specific user role

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
        async def admin_endpoint():
            ...

    Args:
        required_role: Required role (admin, user, service, etc.)
    """
    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        user_role = user.get("role", "user")

        # Role hierarchy
        role_levels = {
            "user": 1,
            "manager": 2,
            "admin": 3,
            "service": 4
        }

        user_level = role_levels.get(user_role, 0)
        required_level = role_levels.get(required_role, 999)

        if user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )

        return user

    return role_checker


# Export commonly used functions
__all__ = [
    "get_current_user",
    "get_supabase_client",
    "verify_tenant_access",
    "require_role",
    "supabase_anon",
    "supabase_service",
    "SUPABASE_AVAILABLE",
]
