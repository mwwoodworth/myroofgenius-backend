#!/usr/bin/env python3
"""
Enable CNS v135.0.0 - Make CNS fully operational
Now that database tables exist, properly initialize CNS with the database pool
"""

import re

def enable_cns():
    """Update main.py to properly initialize CNS with database pool"""

    print("🧠 Enabling CNS v135.0.0...")
    print("=" * 60)

    # Read current main.py
    with open('main.py', 'r') as f:
        content = f.read()

    # Find the CNS initialization section
    if 'cns = None  # Will be initialized in lifespan' in content:
        print("✅ Found CNS placeholder initialization")

        # Update the lifespan function to properly initialize CNS
        # Find the section where CNS should be initialized
        lifespan_pattern = r'(async def lifespan.*?try:.*?# Initialize CNS if available.*?)(if CNS_AVAILABLE:.*?pass.*?except Exception as e:.*?logger\.warning.*?CNS_AVAILABLE = False)'

        replacement = r'''\1if CNS_AVAILABLE:
                    # Initialize CNS with the database pool
                    from cns_service import BrainOpsCNS
                    global cns
                    logger.info("Initializing Central Nervous System with database pool...")
                    cns = BrainOpsCNS(db_pool=app.state.db_pool)

                    # Test CNS connection
                    status = await cns.get_status()
                    logger.info(f"✅ CNS initialized successfully!")
                    logger.info(f"  Memory entries: {status.get('memory_count', 0)}")
                    logger.info(f"  Tasks: {status.get('task_count', 0)}")
                    logger.info(f"  Projects: {status.get('project_count', 0)}")
                    logger.info("🧠 Central Nervous System is OPERATIONAL!")

                    # Register CNS routes
                    from cns_service import create_cns_routes
                    cns_routes = create_cns_routes(cns)
                    app.include_router(cns_routes, prefix="/api/v1/cns", tags=["CNS"])
                    logger.info("✅ CNS routes registered at /api/v1/cns")
            except Exception as e:
                logger.warning(f"CNS initialization failed (will continue without CNS): {e}")
                CNS_AVAILABLE = False'''

        content = re.sub(lifespan_pattern, replacement, content, flags=re.DOTALL)

        # Also ensure we have proper import handling at the top
        if 'CNS_AVAILABLE = False' not in content:
            # Add CNS availability flag after imports
            import_section = content.split('\n\n')[0]
            rest_of_file = '\n\n'.join(content.split('\n\n')[1:])

            cns_check = '''
# Check if CNS is available
CNS_AVAILABLE = False
cns = None  # Will be initialized in lifespan
try:
    from cns_service import BrainOpsCNS, create_cns_routes
    CNS_AVAILABLE = True
    logger.info("✅ CNS module is available")
except ImportError as e:
    logger.warning(f"CNS module not available: {e}")
except Exception as e:
    logger.error(f"Error checking CNS availability: {e}")
'''
            content = import_section + '\n' + cns_check + '\n\n' + rest_of_file

    # Update version to v135.0.0
    content = re.sub(r'VERSION = "v\d+\.\d+\.\d+"', 'VERSION = "v135.0.0"', content)

    # Write updated main.py
    with open('main.py', 'w') as f:
        f.write(content)

    print("✅ main.py updated for CNS v135.0.0")
    print("\nChanges made:")
    print("  1. CNS will be initialized with database pool in lifespan")
    print("  2. CNS status will be checked and logged on startup")
    print("  3. CNS routes will be registered if initialization succeeds")
    print("  4. Version updated to v135.0.0")

    return True

if __name__ == "__main__":
    if enable_cns():
        print("\n✅ CNS enablement complete!")
        print("Next steps:")
        print("  1. Build Docker image: docker build -t mwwoodworth/brainops-backend:v135.0.0 .")
        print("  2. Push to Docker Hub")
        print("  3. Deploy to Render")
        print("  4. Add AI API keys to Render for full functionality")