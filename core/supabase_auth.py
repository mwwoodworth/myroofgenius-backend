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

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not configured. Set {name} in the environment.")
    return value


# Supabase configuration
SUPABASE_URL = _require_env("SUPABASE_URL")
SUPABASE_ANON_KEY = _require_env("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = _require_env("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET = _require_env("SUPABASE_JWT_SECRET")

# Create Supabase clients
supabase_anon: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_service: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


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
        # Decode the JWT token without verification first to get the payload
        # Supabase JWTs are signed with HS256 using the JWT_SECRET
        # For now, we'll decode without verification to get user info
        # The JWT itself being valid from Supabase is sufficient authentication

        # Decode JWT to get payload (Supabase uses HS256)
        # We decode without verification because we trust tokens from Supabase Auth
        # The token was issued by Supabase after successful authentication
        try:
            payload = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
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
    "supabase_service"
]
