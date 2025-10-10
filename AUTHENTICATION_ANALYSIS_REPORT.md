# AUTHENTICATION ANALYSIS REPORT
**Date:** 2025-10-05
**System:** MyRoofGenius Backend
**Critical Finding:** Custom JWT authentication is being used instead of Supabase Auth

---

## EXECUTIVE SUMMARY

The myroofgenius-backend repository currently implements **CUSTOM JWT AUTHENTICATION** across all 368 route files. This is in **DIRECT CONFLICT** with the user's requirement to use **Supabase Auth with Row Level Security (RLS)**.

**Current State:** Custom JWT with bcrypt password hashing
**Required State:** Supabase Auth with RLS-based tenant isolation
**Impact:** High - Affects all authentication and authorization flows
**Files Affected:** 370+ files need modification/deletion

---

## SECTION 1: CUSTOM AUTHENTICATION IMPLEMENTATIONS (TO BE REMOVED)

### 1.1 Core Custom Auth Files (MARK FOR DELETION)

#### `/home/matt-woodworth/myroofgenius-backend/routes/auth.py` (869 lines)
**Status:** ❌ COMPLETE REPLACEMENT REQUIRED
- **Custom Implementation:** Full JWT auth with bcrypt password hashing
- **Features:**
  - Custom `hash_password()` and `verify_password()` using bcrypt
  - Custom `create_access_token()` and `create_refresh_token()` using PyJWT
  - Custom `get_current_user()` dependency that validates JWT tokens
  - Direct database queries to `app_users` table (not Supabase Auth)
  - Registration endpoint with custom user creation
  - Login endpoint with custom password verification
  - Password reset with custom token generation
  - Email verification with custom tokens
- **JWT Secret:** Uses `JWT_SECRET_KEY` environment variable
- **Dependencies:** bcrypt, jwt (python-jose), SQLAlchemy
- **Database Tables:** app_users, auth_tokens, auth_refresh_tokens, user_sessions

#### `/home/matt-woodworth/myroofgenius-backend/auth/auth_manager.py` (251 lines)
**Status:** ❌ DELETION REQUIRED
- **Custom Implementation:** AuthManager class with JWT operations
- **Features:**
  - `verify_password()` / `hash_password()` using passlib/bcrypt
  - `create_access_token()` using python-jose
  - `decode_token()` for JWT validation
  - `authenticate_user()` with custom database queries
  - `get_current_user()` dependency function
  - Role-based access control (RBAC) with hierarchy
  - `check_permission()` and `require_role()` decorators
- **Database Tables:** Queries both `app_users` and `users` tables
- **JWT Secret:** Uses `JWT_SECRET_KEY` environment variable

#### `/home/matt-woodworth/myroofgenius-backend/auth_middleware.py` (78 lines)
**Status:** ❌ DELETION REQUIRED
- **Custom Implementation:** Simple JWT middleware
- **Features:**
  - `create_access_token()` - custom JWT generation
  - `verify_token()` - custom JWT validation
  - `require_auth()` - authentication dependency
  - `optional_auth()` - optional authentication
- **JWT Secret:** Uses `JWT_SECRET` environment variable (different from auth.py!)

#### `/home/matt-woodworth/myroofgenius-backend/core/auth.py` (12 lines)
**Status:** ⚠️ STUB FILE - Minimal custom implementation
- **Current:** Returns mock user `{"id": "test-user", "email": "test@example.com"}`
- **Note:** This is a stub that should be replaced with Supabase Auth

#### `/home/matt-woodworth/myroofgenius-backend/middleware/rls_middleware.py` (181 lines)
**Status:** ⚠️ PARTIAL RETENTION - Concept is correct but implementation needs update
- **Custom Implementation:** RLS context management using custom JWT
- **Features:**
  - Extracts JWT token from Authorization header
  - Decodes JWT using python-jose (custom)
  - Sets PostgreSQL session variables: `app.current_user_id`, `app.current_user_role`
  - RLS bypass for admin operations
- **Problem:** Uses custom JWT decoding instead of Supabase Auth
- **Solution:** Keep RLS context setting, replace JWT decoding with Supabase auth verification

---

### 1.2 Supporting Custom Auth Files

#### `/home/matt-woodworth/myroofgenius-backend/auth_production_ready.py`
- Custom authentication module (not in use based on grep results)

#### `/home/matt-woodworth/myroofgenius-backend/routes/auth_simple.py`
- Simplified authentication routes (likely duplicate/test)

#### `/home/matt-woodworth/myroofgenius-backend/routes/auth_v118.py`
- Version-specific auth routes (likely old version)

#### `/home/matt-woodworth/myroofgenius-backend/routes/auth_routes.py`
- Additional auth routes using auth_manager

#### `/home/matt-woodworth/myroofgenius-backend/routes/auth_production.py`
- Production auth routes (imports from auth_production_ready.py)

---

## SECTION 2: ROUTES USING CUSTOM AUTH (TO BE MODIFIED)

### 2.1 Authentication Dependency Pattern

**Current Pattern (WRONG):**
```python
from auth.auth_manager import get_current_user
from fastapi import Depends

@router.get("/customers")
async def get_customers(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Custom JWT validation happens in get_current_user
    # Returns user dict from app_users table
```

**Required Pattern (CORRECT):**
```python
from supabase import create_client
from fastapi import Depends, HTTPException, Header

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")

    token = authorization.replace("Bearer ", "")

    # Verify JWT with Supabase (not custom JWT!)
    user = supabase.auth.get_user(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user

@router.get("/customers")
async def get_customers(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Supabase Auth validation happens in get_current_user
    # RLS is enforced at the database level
```

---

### 2.2 Files Using Custom Auth (368 route files total)

**Sample of affected files:**
```
/home/matt-woodworth/myroofgenius-backend/routes/customers_complete.py (8 occurrences)
/home/matt-woodworth/myroofgenius-backend/routes/job_analytics.py (6 occurrences)
/home/matt-woodworth/myroofgenius-backend/routes/job_scheduling.py (4 occurrences)
/home/matt-woodworth/myroofgenius-backend/routes/customer_details.py (6 occurrences)
/home/matt-woodworth/myroofgenius-backend/routes/customer_search.py (6 occurrences)
/home/matt-woodworth/myroofgenius-backend/routes/job_notifications.py (8 occurrences)
/home/matt-woodworth/myroofgenius-backend/routes/invoice_management.py (7 occurrences)
/home/matt-woodworth/myroofgenius-backend/routes/estimate_templates.py (9 occurrences)
/home/matt-woodworth/myroofgenius-backend/routes/ai_vision.py (4 occurrences)
/home/matt-woodworth/myroofgenius-backend/routes/job_documents.py (6 occurrences)
/home/matt-woodworth/myroofgenius-backend/routes/reality_check_testing.py (5 occurrences)
/home/matt-woodworth/myroofgenius-backend/routes/job_reports.py (5 occurrences)
/home/matt-woodworth/myroofgenius-backend/routes/customers_full_crud.py (6 occurrences)
... (and 355+ more route files)
```

**Total Affected:** All 368 route files in `/home/matt-woodworth/myroofgenius-backend/routes/`

---

## SECTION 3: EXISTING SUPABASE INFRASTRUCTURE

### 3.1 Supabase Configuration (ALREADY AVAILABLE)

**Environment Variables (from BrainOps.env):**
```bash
SUPABASE_URL=https://yomagoqdmxszqtdwuhab.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzMzNzY3NzcsImV4cCI6MjA0ODk1Mjc3N30.5tL0ms5Bs9PqQs_RdkBj8Xq_QhqoUvMKZTML3MCXbFw
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTgzMzI3NiwiZXhwIjoyMDY1NDA5Mjc2fQ.7C3guJ_0moYGkdyeFmJ9cd2BmduB5NnU00erIIxH3gQ
SUPABASE_PROJECT_REF=yomagoqdmxszqtdwuhab
SUPABASE_DB_URL=postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@aws-0-us-east-2.pooler.supabase.com:5432/postgres
SUPABASE_STORAGE_BUCKET=roof-images
```

**Status:** ✅ All Supabase credentials are already configured

---

### 3.2 Row Level Security (RLS) Setup

**File:** `/home/matt-woodworth/myroofgenius-backend/migrations/setup_row_level_security.sql`

**Status:** ✅ RLS policies are already defined
- Policies exist for: customers, jobs, invoices, estimates, employees, timesheets, materials, equipment
- Uses PostgreSQL session variables: `app.current_user_id`, `app.current_user_role`
- Role-based access: admin, superadmin, manager, user
- Tenant isolation through user_customers and employee_jobs tables

**Problem:** RLS policies expect session variables to be set, but custom JWT is being used to set them instead of Supabase Auth tokens

---

### 3.3 Database Connection

**File:** `/home/matt-woodworth/myroofgenius-backend/database.py`

**Current:** Direct PostgreSQL connection via asyncpg and SQLAlchemy
- Bypasses Supabase client library
- Uses `DATABASE_URL` directly
- No Supabase Auth integration

**Required:** Keep PostgreSQL connection BUT add Supabase client for auth verification
```python
from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)
```

---

## SECTION 4: SUPABASE AUTH IMPLEMENTATIONS (CURRENTLY MISSING)

### 4.1 Files That Should Use Supabase (But Don't)

**None found.** There are NO files currently using Supabase Auth properly.

**Evidence:**
```bash
# Searched for: from supabase import | supabase.auth
# Results: Only found in:
- weathercraft_erp.py (different project)
- persistent_memory_brain.py (not auth-related)
- centerpoint_sync.py (not auth-related)
- langgraph_neural_network.py (not auth-related)
- env_manager.py (not auth-related)
```

**Conclusion:** Zero Supabase Auth usage in the backend routes

---

## SECTION 5: MIGRATION PLAN

### 5.1 Phase 1: Create Supabase Auth Module

**New File:** `/home/matt-woodworth/myroofgenius-backend/core/supabase_auth.py`

**Purpose:**
- Initialize Supabase client
- Provide `get_current_user()` dependency using Supabase Auth
- Replace all custom JWT validation with `supabase.auth.get_user(token)`
- Set RLS context based on Supabase user ID and metadata

**Key Functions:**
```python
def get_supabase_client() -> Client:
    """Get Supabase client instance"""

async def verify_supabase_token(token: str) -> dict:
    """Verify token with Supabase Auth"""

async def get_current_user(authorization: str = Header(None)) -> dict:
    """FastAPI dependency for authenticated user (Supabase)"""

async def set_rls_context(db: Session, user: dict):
    """Set RLS session variables from Supabase user"""
```

---

### 5.2 Phase 2: Delete Custom Auth Files

**Files to DELETE:**
1. `/home/matt-woodworth/myroofgenius-backend/routes/auth.py` (869 lines) ❌
2. `/home/matt-woodworth/myroofgenius-backend/auth/auth_manager.py` (251 lines) ❌
3. `/home/matt-woodworth/myroofgenius-backend/auth_middleware.py` (78 lines) ❌
4. `/home/matt-woodworth/myroofgenius-backend/auth_production_ready.py` ❌
5. `/home/matt-woodworth/myroofgenius-backend/routes/auth_simple.py` ❌
6. `/home/matt-woodworth/myroofgenius-backend/routes/auth_v118.py` ❌
7. `/home/matt-woodworth/myroofgenius-backend/routes/auth_production.py` ❌

**Rationale:** All custom JWT/bcrypt authentication will be replaced by Supabase Auth

---

### 5.3 Phase 3: Update RLS Middleware

**File:** `/home/matt-woodworth/myroofgenius-backend/middleware/rls_middleware.py`

**Changes:**
- ❌ Remove custom JWT decoding (lines 42-51)
- ✅ Keep RLS context setting (lines 54-66)
- ✅ Add Supabase token verification
- ✅ Extract user_id from Supabase user object instead of custom JWT payload

**Before:**
```python
# Decode token (CUSTOM JWT)
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
user_id = payload.get("sub")
```

**After:**
```python
# Verify with Supabase
user = await verify_supabase_token(token)
user_id = user.id  # Supabase user ID
tenant_id = user.user_metadata.get("tenant_id")  # Tenant isolation
```

---

### 5.4 Phase 4: Update All Route Files

**Target:** 368 route files in `/home/matt-woodworth/myroofgenius-backend/routes/`

**Find/Replace Operation:**
```python
# OLD (WRONG):
from auth.auth_manager import get_current_user

# NEW (CORRECT):
from core.supabase_auth import get_current_user
```

**Automated Solution:**
```bash
# Find all files using custom auth
find /home/matt-woodworth/myroofgenius-backend/routes -name "*.py" -type f \
  -exec grep -l "from auth.auth_manager import get_current_user" {} \;

# Replace in all files
find /home/matt-woodworth/myroofgenius-backend/routes -name "*.py" -type f \
  -exec sed -i 's|from auth.auth_manager import get_current_user|from core.supabase_auth import get_current_user|g' {} \;
```

---

### 5.5 Phase 5: Update Main Application

**File:** `/home/matt-woodworth/myroofgenius-backend/main.py`

**Changes:**
- Remove references to custom auth modules
- Add Supabase client initialization
- Update middleware registration

---

### 5.6 Phase 6: Update Database Schema

**Requirements:**
1. Remove `app_users` table (or convert to profile extension)
2. Remove `auth_tokens`, `auth_refresh_tokens`, `user_sessions` tables
3. Update RLS policies to use Supabase Auth user IDs
4. Add `tenant_id` to all tenant-scoped tables
5. Update RLS policies to enforce `tenant_id` matching

**SQL Migration:**
```sql
-- Add tenant_id to all tables
ALTER TABLE customers ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS tenant_id UUID;
-- ... repeat for all tenant-scoped tables

-- Update RLS policies to use auth.uid() instead of app.current_user_id
CREATE POLICY customers_tenant_isolation ON customers
    FOR SELECT
    USING (tenant_id = (current_setting('request.jwt.claims', true)::json->>'tenant_id')::uuid);
```

---

## SECTION 6: SUPABASE AUTH CORRECT PATTERN

### 6.1 Frontend (MyRoofGenius App)

**Current:** Unknown (needs verification)

**Required:**
```typescript
// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password',
  options: {
    data: {
      tenant_id: 'tenant-uuid-here',
      full_name: 'John Doe'
    }
  }
})

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Get session token
const { data: { session } } = await supabase.auth.getSession()
const token = session.access_token  // Use this in API calls
```

---

### 6.2 Backend (MyRoofGenius API)

**Required:**
```python
from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")

    token = authorization.replace("Bearer ", "")

    try:
        # Verify with Supabase Auth (NOT custom JWT!)
        user = supabase.auth.get_user(token)

        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Extract tenant_id from user metadata
        tenant_id = user.user.user_metadata.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Missing tenant_id")

        # Set RLS context
        db.execute(text("SELECT set_config('app.current_user_id', :user_id, false)"),
                   {"user_id": user.user.id})
        db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, false)"),
                   {"tenant_id": tenant_id})

        return {
            "id": user.user.id,
            "email": user.user.email,
            "tenant_id": tenant_id,
            "metadata": user.user.user_metadata
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
```

---

### 6.3 Row Level Security (Correct Pattern)

**SQL:**
```sql
-- Enable RLS
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- Policy using Supabase Auth
CREATE POLICY customers_tenant_isolation ON customers
    FOR SELECT
    USING (
        -- Extract tenant_id from JWT claims (Supabase Auth)
        tenant_id = (current_setting('request.jwt.claims', true)::json->>'tenant_id')::uuid
        OR
        -- Superadmin bypass
        (current_setting('request.jwt.claims', true)::json->>'role') = 'service_role'
    );

-- INSERT policy
CREATE POLICY customers_insert ON customers
    FOR INSERT
    WITH CHECK (
        tenant_id = (current_setting('request.jwt.claims', true)::json->>'tenant_id')::uuid
    );
```

---

## SECTION 7: CRITICAL SECURITY ISSUES WITH CURRENT SETUP

### 7.1 Multiple JWT Secrets

**Problem:** Three different JWT secrets are being used:
1. `JWT_SECRET_KEY` in `routes/auth.py` (line 35)
2. `JWT_SECRET_KEY` in `auth/auth_manager.py` (line 20)
3. `JWT_SECRET` in `auth_middleware.py` (line 15)

**Risk:** Tokens may be created with one secret and validated with another, causing auth failures

---

### 7.2 Password Storage

**Problem:** Custom bcrypt implementation stores passwords in `app_users` table
- Passwords are hashed but stored in application database
- No benefits of Supabase Auth (email verification, magic links, OAuth, etc.)

**Solution:** Use Supabase Auth which handles all password hashing and storage securely

---

### 7.3 Token Refresh

**Problem:** Custom refresh token implementation stores tokens in `auth_refresh_tokens` table
- Manual token rotation required
- Risk of token leakage if database is compromised

**Solution:** Use Supabase Auth which handles refresh tokens automatically

---

### 7.4 No Multi-Tenant Isolation

**Problem:** Current auth system has NO tenant_id enforcement
- Users from different tenants could access each other's data
- RLS policies exist but are not enforced at auth level

**Solution:** Supabase Auth stores tenant_id in user_metadata, enforced by RLS

---

## SECTION 8: RECOMMENDED IMPLEMENTATION ORDER

### Step 1: Create Supabase Auth Module (1 hour)
- Create `/home/matt-woodworth/myroofgenius-backend/core/supabase_auth.py`
- Implement `get_current_user()` using Supabase
- Test with a single route

### Step 2: Update One Test Route (30 minutes)
- Pick a simple route (e.g., `/api/v1/health`)
- Replace custom auth with Supabase auth
- Verify it works end-to-end

### Step 3: Batch Update All Routes (2 hours)
- Use sed/awk to replace imports in all 368 route files
- Run tests to verify no regressions

### Step 4: Update RLS Middleware (1 hour)
- Replace custom JWT decoding with Supabase token verification
- Keep RLS context setting logic

### Step 5: Delete Custom Auth Files (30 minutes)
- Delete 7 custom auth files
- Update imports in any remaining files

### Step 6: Database Migration (2 hours)
- Add tenant_id to all tables
- Update RLS policies to use Supabase JWT claims
- Test tenant isolation

### Step 7: Frontend Update (4 hours)
- Replace any custom auth API calls with Supabase Auth SDK
- Test sign up, sign in, sign out flows

**Total Estimated Time: 11 hours**

---

## SECTION 9: TESTING CHECKLIST

### 9.1 Authentication Tests
- [ ] User can sign up with email/password
- [ ] User receives verification email
- [ ] User can verify email
- [ ] User can sign in with verified email
- [ ] User receives valid JWT token from Supabase
- [ ] Backend validates Supabase JWT token
- [ ] Invalid tokens are rejected
- [ ] Expired tokens are rejected
- [ ] User can refresh token

### 9.2 Authorization Tests
- [ ] User can only access their tenant's data
- [ ] User cannot access other tenant's data
- [ ] Admin can access all data in their tenant
- [ ] Service role can bypass RLS (if needed)
- [ ] RLS policies block unauthorized access

### 9.3 Route Tests
- [ ] All 368 routes use Supabase auth
- [ ] No routes use custom JWT auth
- [ ] Protected routes require authentication
- [ ] Public routes work without authentication

---

## SECTION 10: FILES INVENTORY

### Custom Auth Files (DELETE - 7 files)
1. `/home/matt-woodworth/myroofgenius-backend/routes/auth.py`
2. `/home/matt-woodworth/myroofgenius-backend/auth/auth_manager.py`
3. `/home/matt-woodworth/myroofgenius-backend/auth_middleware.py`
4. `/home/matt-woodworth/myroofgenius-backend/auth_production_ready.py`
5. `/home/matt-woodworth/myroofgenius-backend/routes/auth_simple.py`
6. `/home/matt-woodworth/myroofgenius-backend/routes/auth_v118.py`
7. `/home/matt-woodworth/myroofgenius-backend/routes/auth_production.py`

### Core Files (MODIFY - 4 files)
1. `/home/matt-woodworth/myroofgenius-backend/core/auth.py` - Replace stub with Supabase
2. `/home/matt-woodworth/myroofgenius-backend/middleware/rls_middleware.py` - Update JWT verification
3. `/home/matt-woodworth/myroofgenius-backend/database.py` - Add Supabase client
4. `/home/matt-woodworth/myroofgenius-backend/main.py` - Update middleware

### Route Files (MODIFY - 368 files)
- All files in `/home/matt-woodworth/myroofgenius-backend/routes/*.py`
- Replace `from auth.auth_manager import get_current_user`
- With `from core.supabase_auth import get_current_user`

### Migration Files (CREATE - 2 files)
1. `/home/matt-woodworth/myroofgenius-backend/core/supabase_auth.py` - New Supabase auth module
2. `/home/matt-woodworth/myroofgenius-backend/migrations/add_tenant_id.sql` - Add tenant_id to all tables

**Total Files Affected: 381 files**

---

## SECTION 11: ENVIRONMENT VARIABLES REQUIRED

**Already Configured (✅):**
```bash
SUPABASE_URL=https://yomagoqdmxszqtdwuhab.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
SUPABASE_PROJECT_REF=yomagoqdmxszqtdwuhab
```

**To Remove (❌):**
```bash
JWT_SECRET_KEY  # No longer needed with Supabase Auth
JWT_SECRET      # No longer needed
JWT_ALGORITHM   # No longer needed
```

---

## CONCLUSION

The myroofgenius-backend is currently using a **COMPLETE CUSTOM JWT AUTHENTICATION SYSTEM** with bcrypt password hashing, custom token generation, and custom user management. This is in direct conflict with the requirement to use **Supabase Auth with RLS**.

**Key Findings:**
1. **Zero Supabase Auth Usage** - Not a single route uses Supabase Auth
2. **7 Custom Auth Files** - Need complete deletion
3. **368 Route Files** - All need import updates
4. **Custom JWT Secrets** - Multiple inconsistent secrets in use
5. **No Tenant Isolation** - Custom auth has no tenant_id enforcement
6. **RLS Exists But Unused** - RLS policies are defined but not enforced

**Recommended Action:** Complete migration to Supabase Auth following the 7-step plan above.

**Estimated Effort:** 11 hours of development + testing

---

**Report Generated:** 2025-10-05
**Analyst:** Claude Code
**Status:** Ready for user review and approval to proceed
