# Deprecated Routes Archive

This directory contains route files that were archived to resolve routing conflicts.

## Archived Files (2025-12-15)

### complete_erp.py
- **Reason**: No prefix defined, causes route loader issues
- **Conflict**: Router has no prefix, gets auto-assigned `/api/v1/complete-erp` which may conflict with weathercraft alias
- **Details**: Large file (3330 lines) with comprehensive ERP functionality
- **Issue**: When router has no prefix, route_loader assigns a default prefix, which can conflict with other routes
- **Status**: Fully archived - functionality covered by erp_complete.py
- **Note**: Could be restored if prefix is properly defined and functionality is needed

### erp_core_runtime.py (Copy Only)
- **Status**: This is a COPY for reference only
- **Original Location**: The original file is in `routes/erp_core_runtime.py`
- **Why It's Listed Here**: Initially archived, then restored because erp_complete.py depends on it
- **Solution**: File restored to routes/ but added to EXCLUDED_MODULES to prevent route mounting
- **Details**: Provides InMemoryERPStore class used as fallback by erp_complete.py
- **Routes**: NOT mounted (excluded in route_loader.py)
- **Usage**: Imported as dependency by erp_complete.py for offline fallback

## Active ERP Routes

The following ERP routes are active in production:

1. **erp_complete.py** - Primary ERP endpoints at `/api/v1/erp`
   - Real database integration
   - GET operations for customers, jobs, estimates, invoices, inventory
   - Dashboard and schedule endpoints
   - Fallback to mock data (via erp_core_runtime.STORE) when database unavailable

2. **erp_core_runtime.py** - Dependency module (NOT mounted as routes)
   - Provides InMemoryERPStore for fallback functionality
   - Excluded from route loading but available for imports
   - Used by erp_complete.py for offline resilience

3. **weathercraft_integration.py** - WeatherCraft-specific at `/api/v1/erp/weathercraft`
   - Specialized endpoints for WeatherCraft ERP system
   - No conflicts with main ERP routes

4. **public_endpoints.py** - Public ERP access at `/api/v1/erp/public`
   - No authentication required
   - Safe, isolated route

## Route Conflict Resolution Summary

**Problem Identified by Gemini Audit:**
- Multiple routers claiming `/api/v1/erp` prefix
- erp_complete.py - Real DB, GET operations (kept)
- erp_core_runtime.py - In-memory MOCK data (kept as dependency, routes excluded)
- complete_erp.py - Legacy, no prefix, routing conflicts (archived)

**Solution Implemented:**
1. Kept erp_complete.py as primary ERP implementation
2. Kept erp_core_runtime.py but added to EXCLUDED_MODULES (dependency only)
3. Archived complete_erp.py (truly redundant with routing issues)
4. Updated route_loader.py to document the exclusions

## Restoration Process

If complete_erp.py needs to be restored:

1. Add explicit prefix to router definition in complete_erp.py
2. Move file back to routes/ directory
3. Verify no route conflicts exist
4. Test thoroughly
5. Update route_loader.py EXCLUDED_MODULES if necessary
