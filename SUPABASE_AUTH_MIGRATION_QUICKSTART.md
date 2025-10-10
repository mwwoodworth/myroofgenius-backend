# SUPABASE AUTH MIGRATION - QUICK START GUIDE

## TLDR: What's Wrong?

**Current:** Custom JWT authentication (bcrypt + PyJWT)
**Problem:** 381 files using custom auth instead of Supabase Auth
**Solution:** Replace ALL custom JWT with Supabase Auth + RLS

---

## FILES TO DELETE (7 files)

```bash
rm /home/matt-woodworth/myroofgenius-backend/routes/auth.py
rm /home/matt-woodworth/myroofgenius-backend/auth/auth_manager.py
rm /home/matt-woodworth/myroofgenius-backend/auth_middleware.py
rm /home/matt-woodworth/myroofgenius-backend/auth_production_ready.py
rm /home/matt-woodworth/myroofgenius-backend/routes/auth_simple.py
rm /home/matt-woodworth/myroofgenius-backend/routes/auth_v118.py
rm /home/matt-woodworth/myroofgenius-backend/routes/auth_production.py
```

---

## STEP 1: Create Supabase Auth Module

**File:** `/home/matt-woodworth/myroofgenius-backend/core/supabase_auth.py`

```python
"""
Supabase Authentication Module
Replaces custom JWT authentication with Supabase Auth
"""

from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from supabase import create_client, Client
from typing import Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize Supabase client
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client instance"""
    global _supabase_client

    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

        _supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info("Supabase client initialized")

    return _supabase_client


async def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token with Supabase Auth

    Args:
        token: JWT access token from Supabase

    Returns:
        User object from Supabase Auth

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        supabase = get_supabase_client()

        # Verify token with Supabase Auth
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )

        return user_response.user

    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


async def set_rls_context(db: Session, user: Dict[str, Any]) -> None:
    """
    Set Row Level Security context for database queries

    Args:
        db: Database session
        user: Supabase user object
    """
    try:
        user_id = user.id
        tenant_id = user.user_metadata.get("tenant_id")
        role = user.user_metadata.get("role", "user")

        # Set PostgreSQL session variables for RLS
        db.execute(
            text("SELECT set_config('app.current_user_id', :user_id, false)"),
            {"user_id": user_id}
        )

        if tenant_id:
            db.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, false)"),
                {"tenant_id": tenant_id}
            )

        db.execute(
            text("SELECT set_config('app.current_user_role', :role, false)"),
            {"role": role}
        )

        logger.debug(f"RLS context set for user {user_id}, tenant {tenant_id}")

    except Exception as e:
        logger.error(f"Failed to set RLS context: {e}")
        # Don't raise - RLS will default to restrictive policies


async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(lambda: None)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user from Supabase

    This replaces the custom JWT authentication with Supabase Auth.

    Args:
        authorization: Authorization header (Bearer token)
        db: Optional database session for RLS context

    Returns:
        Supabase user object with additional fields:
        - id: User UUID
        - email: User email
        - user_metadata: Custom user data (includes tenant_id, role, etc.)

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: Bearer <token>"
        )

    # Extract token
    token = authorization.replace("Bearer ", "").strip()

    # Verify with Supabase
    user = await verify_supabase_token(token)

    # Validate tenant_id exists
    tenant_id = user.user_metadata.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail="User missing tenant_id. Please contact support."
        )

    # Set RLS context if database session provided
    if db:
        await set_rls_context(db, user)

    # Return user object
    return {
        "id": user.id,
        "email": user.email,
        "tenant_id": tenant_id,
        "role": user.user_metadata.get("role", "user"),
        "user_metadata": user.user_metadata,
        "created_at": user.created_at,
        "email_confirmed_at": user.email_confirmed_at
    }


async def get_current_user_optional(
    authorization: str = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication - returns user if authenticated, None otherwise

    Use this for endpoints that can work both authenticated and unauthenticated.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization.replace("Bearer ", "").strip()
        user = await verify_supabase_token(token)

        return {
            "id": user.id,
            "email": user.email,
            "tenant_id": user.user_metadata.get("tenant_id"),
            "role": user.user_metadata.get("role", "user"),
            "user_metadata": user.user_metadata
        }
    except:
        return None


async def require_role(required_role: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Dependency to require a specific role

    Usage:
        @router.get("/admin/dashboard")
        async def admin_dashboard(user: dict = Depends(lambda: require_role("admin"))):
            ...
    """
    user_role = current_user.get("role", "user")

    # Role hierarchy
    role_levels = {
        "user": 1,
        "staff": 2,
        "manager": 3,
        "admin": 4,
        "superadmin": 5
    }

    user_level = role_levels.get(user_role, 0)
    required_level = role_levels.get(required_role, 999)

    if user_level < required_level:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required role: {required_role}"
        )

    return current_user


# Export main functions
__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "require_role",
    "get_supabase_client",
    "verify_supabase_token",
    "set_rls_context"
]
```

---

## STEP 2: Update One Test Route

**File:** `/home/matt-woodworth/myroofgenius-backend/routes/test_supabase_auth.py`

```python
"""
Test route to verify Supabase Auth integration
"""

from fastapi import APIRouter, Depends
from core.supabase_auth import get_current_user

router = APIRouter(prefix="/api/v1/test", tags=["Test"])


@router.get("/auth/me")
async def test_auth(current_user: dict = Depends(get_current_user)):
    """
    Test endpoint to verify Supabase authentication

    Usage:
        curl -H "Authorization: Bearer <supabase-token>" \
             http://localhost:8000/api/v1/test/auth/me
    """
    return {
        "status": "authenticated",
        "user": current_user
    }
```

---

## STEP 3: Batch Update All Routes

**Command:**
```bash
# Replace imports in all route files
find /home/matt-woodworth/myroofgenius-backend/routes -name "*.py" -type f \
  -exec sed -i 's|from auth\.auth_manager import get_current_user|from core.supabase_auth import get_current_user|g' {} \;

# Verify changes
grep -r "from core.supabase_auth import get_current_user" /home/matt-woodworth/myroofgenius-backend/routes | wc -l
# Should return 368
```

---

## STEP 4: Update RLS Middleware

**File:** `/home/matt-woodworth/myroofgenius-backend/middleware/rls_middleware.py`

**Replace lines 42-51:**
```python
# OLD (WRONG):
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
user_id = payload.get("sub")
user_role = payload.get("role", "user")

# NEW (CORRECT):
from core.supabase_auth import verify_supabase_token

user = await verify_supabase_token(token)
user_id = user.id
user_role = user.user_metadata.get("role", "user")
tenant_id = user.user_metadata.get("tenant_id")
```

---

## STEP 5: Update main.py

**File:** `/home/matt-woodworth/myroofgenius-backend/main.py`

**Add after line 191:**
```python
# Initialize Supabase client on startup
from core.supabase_auth import get_supabase_client

@app.on_event("startup")
async def initialize_supabase():
    """Initialize Supabase client"""
    try:
        client = get_supabase_client()
        logger.info("✅ Supabase Auth client initialized")
    except Exception as e:
        logger.error(f"⚠️ Failed to initialize Supabase client: {e}")
```

---

## STEP 6: Database Migration

**File:** `/home/matt-woodworth/myroofgenius-backend/migrations/add_tenant_id.sql`

```sql
-- Add tenant_id to all multi-tenant tables
ALTER TABLE customers ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE estimates ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS tenant_id UUID;
-- ... repeat for all tenant-scoped tables

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_customers_tenant_id ON customers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_jobs_tenant_id ON jobs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_invoices_tenant_id ON invoices(tenant_id);
-- ... repeat for all tenant-scoped tables

-- Update RLS policies to use Supabase JWT claims
DROP POLICY IF EXISTS customers_select_policy ON customers;
CREATE POLICY customers_select_policy ON customers
    FOR SELECT
    USING (
        -- Extract tenant_id from Supabase JWT
        tenant_id::text = (current_setting('request.jwt.claims', true)::json->>'tenant_id')
        OR
        -- Service role bypass
        (current_setting('request.jwt.claims', true)::json->>'role') = 'service_role'
        OR
        -- Superadmin bypass
        (current_setting('app.current_user_role', true)) = 'superadmin'
    );

-- Repeat for INSERT, UPDATE, DELETE policies on all tables
```

**Run migration:**
```bash
psql $DATABASE_URL -f /home/matt-woodworth/myroofgenius-backend/migrations/add_tenant_id.sql
```

---

## STEP 7: Frontend Update

**File:** `myroofgenius-app/src/lib/supabase.ts` (or similar)

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Sign up with tenant_id
export async function signUp(email: string, password: string, tenantId: string) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        tenant_id: tenantId,
        role: 'user'
      }
    }
  })
  return { data, error }
}

// Sign in
export async function signIn(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password
  })
  return { data, error }
}

// Get session token for API calls
export async function getSessionToken() {
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token
}
```

**Update API calls:**
```typescript
// OLD (WRONG):
const response = await fetch('/api/v1/customers', {
  headers: {
    'Authorization': `Bearer ${customJwtToken}`  // Custom JWT
  }
})

// NEW (CORRECT):
const token = await getSessionToken()  // Supabase token
const response = await fetch('/api/v1/customers', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

---

## TESTING

### 1. Test Authentication
```bash
# Sign up via Supabase dashboard or frontend
# Get token from Supabase session

# Test backend authentication
curl -H "Authorization: Bearer <supabase-token>" \
     http://localhost:8000/api/v1/test/auth/me

# Expected response:
{
  "status": "authenticated",
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "tenant_id": "tenant-uuid",
    "role": "user"
  }
}
```

### 2. Test Tenant Isolation
```bash
# User 1 (tenant A) creates customer
curl -X POST http://localhost:8000/api/v1/customers \
     -H "Authorization: Bearer <user1-token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Customer A", "email": "a@example.com"}'

# User 2 (tenant B) tries to get customer
curl http://localhost:8000/api/v1/customers/customer-a-id \
     -H "Authorization: Bearer <user2-token>"

# Expected: 404 Not Found (RLS blocks access)
```

### 3. Test RLS Policies
```sql
-- Connect to database
psql $DATABASE_URL

-- Manually set JWT claims to simulate tenant A
SET LOCAL request.jwt.claims = '{"tenant_id": "tenant-a-uuid"}';

-- Query should only return tenant A's customers
SELECT * FROM customers;

-- Change to tenant B
SET LOCAL request.jwt.claims = '{"tenant_id": "tenant-b-uuid"}';

-- Query should only return tenant B's customers
SELECT * FROM customers;
```

---

## ENVIRONMENT VARIABLES

**Required (already set):**
- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY
- DATABASE_URL

**Remove (no longer needed):**
- JWT_SECRET_KEY
- JWT_SECRET
- JWT_ALGORITHM

---

## ROLLBACK PLAN

If migration fails, restore from backup:

```bash
# Restore custom auth files from git
git checkout HEAD~1 -- routes/auth.py
git checkout HEAD~1 -- auth/auth_manager.py
git checkout HEAD~1 -- auth_middleware.py

# Revert route imports
find /home/matt-woodworth/myroofgenius-backend/routes -name "*.py" -type f \
  -exec sed -i 's|from core.supabase_auth import get_current_user|from auth.auth_manager import get_current_user|g' {} \;
```

---

## VERIFICATION CHECKLIST

- [ ] core/supabase_auth.py created
- [ ] Test route works with Supabase token
- [ ] All 368 routes updated with new import
- [ ] RLS middleware updated
- [ ] main.py updated
- [ ] Database has tenant_id columns
- [ ] RLS policies updated
- [ ] Frontend uses Supabase Auth SDK
- [ ] Custom auth files deleted
- [ ] All tests passing
- [ ] Tenant isolation verified

---

## NEED HELP?

**Full documentation:** `/home/matt-woodworth/myroofgenius-backend/AUTHENTICATION_ANALYSIS_REPORT.md`

**Key files:**
- Core auth: `/home/matt-woodworth/myroofgenius-backend/core/supabase_auth.py`
- RLS middleware: `/home/matt-woodworth/myroofgenius-backend/middleware/rls_middleware.py`
- Database migration: `/home/matt-woodworth/myroofgenius-backend/migrations/add_tenant_id.sql`

**Estimated time:** 11 hours total

---

**Ready to begin migration!**
