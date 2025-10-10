#!/usr/bin/env python3
"""
Fix v134.0.0 CNS deployment issue
Make CNS initialization optional and fail gracefully
"""

import os

def fix_cns_deployment():
    """Fix CNS initialization to be more robust"""

    # Read current main.py
    with open('main.py', 'r') as f:
        content = f.read()

    # Find and fix the module-level CNS initialization
    # This line at 699 is problematic:
    # cns = BrainOpsCNS(db_pool=None)  # Will use global db_pool

    if 'cns = BrainOpsCNS(db_pool=None)' in content:
        # Replace with None initialization
        content = content.replace(
            'cns = BrainOpsCNS(db_pool=None)  # Will use global db_pool',
            'cns = None  # Will be initialized in lifespan'
        )
        print("✅ Fixed module-level CNS initialization")

    # Also ensure the CNS service is imported with try/except
    if 'from cns_service import BrainOpsCNS, create_cns_routes' in content:
        # Replace with safe import
        content = content.replace(
            'from cns_service import BrainOpsCNS, create_cns_routes',
            '''try:
    from cns_service import BrainOpsCNS, create_cns_routes
    CNS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ CNS service not available: {e}")
    CNS_AVAILABLE = False
    BrainOpsCNS = None
    create_cns_routes = None'''
        )
        print("✅ Made CNS import optional")

    # Fix the lifespan CNS initialization to check if available
    lifespan_marker = '''        # Initialize CNS with database pool
        global cns
        try:
            cns = BrainOpsCNS(db_pool=db_pool)
            await cns.initialize()
            print("🧠 Central Nervous System initialized")
        except Exception as e:
            print(f"⚠️ CNS initialization failed: {e}")
            cns = None'''

    if lifespan_marker in content:
        content = content.replace(
            lifespan_marker,
            '''        # Initialize CNS with database pool if available
        global cns
        if CNS_AVAILABLE:
            try:
                cns = BrainOpsCNS(db_pool=db_pool)
                await cns.initialize()
                print("🧠 Central Nervous System initialized")
            except Exception as e:
                print(f"⚠️ CNS initialization failed: {e}")
                cns = None
        else:
            print("⚠️ CNS service not available, skipping initialization")
            cns = None'''
        )
        print("✅ Made lifespan CNS initialization conditional")

    # Fix the route registration to check both CNS_AVAILABLE and cns
    route_marker = '''# Create all CNS routes
if cns:
    create_cns_routes(app, cns)
    print("🧠 CNS routes registered")'''

    if route_marker in content:
        content = content.replace(
            route_marker,
            '''# Create all CNS routes
if CNS_AVAILABLE and cns:
    create_cns_routes(app, cns)
    print("🧠 CNS routes registered")
else:
    print("⚠️ CNS routes not registered (service unavailable)")'''
        )
        print("✅ Made CNS route registration conditional")

    # Update version to 134.0.1
    content = content.replace('version="134.0.0"', 'version="134.0.1"')
    content = content.replace('"version": "134.0.0"', '"version": "134.0.1"')
    content = content.replace('v134.0.0', 'v134.0.1')

    # Write updated main.py
    with open('main.py', 'w') as f:
        f.write(content)

    print("\n✅ Fixed CNS deployment issues!")
    print("✅ Updated to v134.0.1")
    print("✅ Changes made:")
    print("   - Made CNS import optional with try/except")
    print("   - Fixed module-level initialization")
    print("   - Made lifespan initialization conditional")
    print("   - Made route registration conditional")
    print("\n🚀 The system will now start even if CNS has issues")

if __name__ == "__main__":
    fix_cns_deployment()