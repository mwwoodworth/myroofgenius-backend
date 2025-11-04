#!/usr/bin/env python3
"""
Fix deployment errors for v3.1.143
"""
import os

def fix_roofing_route():
    """Fix missing Query import in roofing.py"""
    roofing_path = "/home/mwwoodworth/code/fastapi-operator-env/apps/backend/routes/roofing.py"
    
    with open(roofing_path, 'r') as f:
        content = f.read()
    
    # Add Query to the imports
    old_import = "from fastapi import APIRouter, Depends, HTTPException, UploadFile, File"
    new_import = "from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query"
    
    content = content.replace(old_import, new_import)
    
    with open(roofing_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed roofing.py - added Query import")

def fix_main_route_loading():
    """Fix aurea_web route loading without prefix"""
    main_path = "/home/mwwoodworth/code/fastapi-operator-env/apps/backend/main.py"
    
    with open(main_path, 'r') as f:
        content = f.read()
    
    # Find the load_route function and add special handling for aurea_web
    old_code = """                if router:
                    # Include the router
                    app.include_router(router, prefix=f"/api/v1/{prefix}")"""
    
    new_code = """                if router:
                    # Special handling for aurea_web (no prefix)
                    if route_name == "aurea_web":
                        app.include_router(router)
                    else:
                        # Include the router with prefix
                        app.include_router(router, prefix=f"/api/v1/{prefix}")"""
    
    content = content.replace(old_code, new_code)
    
    with open(main_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed main.py - special handling for aurea_web route")

def update_version():
    """Update version to 3.1.143"""
    main_path = "/home/mwwoodworth/code/fastapi-operator-env/apps/backend/main.py"
    
    with open(main_path, 'r') as f:
        content = f.read()
    
    content = content.replace('__version__ = "3.1.142"', '__version__ = "3.1.143"')
    
    with open(main_path, 'w') as f:
        f.write(content)
    
    print("✅ Updated version to 3.1.143")

if __name__ == "__main__":
    print("🔧 Fixing deployment errors...")
    fix_roofing_route()
    fix_main_route_loading()
    update_version()
    print("✅ All fixes applied!")