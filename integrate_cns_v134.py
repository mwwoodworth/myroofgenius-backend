#!/usr/bin/env python3
"""
Integration script to add CNS to main.py
Creates v134.0.0 with complete Central Nervous System
"""

import os

def integrate_cns():
    """Add CNS integration to main.py"""

    # Read current main.py
    with open('main.py', 'r') as f:
        content = f.read()

    # Find the AI service import section
    ai_import_marker = "from ai_service_complete import ComprehensiveAIService"

    if ai_import_marker in content:
        # Add CNS import right after AI service
        cns_import = """from ai_service_complete import ComprehensiveAIService
from cns_service import BrainOpsCNS, create_cns_routes"""

        content = content.replace(
            "from ai_service_complete import ComprehensiveAIService",
            cns_import
        )

        # Find where AI service is initialized
        ai_init_marker = "ai_service = ComprehensiveAIService()"

        if ai_init_marker in content:
            # Add CNS initialization
            cns_init = """ai_service = ComprehensiveAIService()

# Initialize Central Nervous System
cns = BrainOpsCNS(db_pool=None)  # Will use global db_pool"""

            content = content.replace(ai_init_marker, cns_init)

        # Update lifespan to initialize CNS
        lifespan_marker = '    print("✅ Database pool initialized")'
        if lifespan_marker in content:
            cns_lifespan = '''    print("✅ Database pool initialized")

    # Initialize CNS with database pool
    global cns
    try:
        cns = BrainOpsCNS(db_pool=db_pool)
        await cns.initialize()
        print("🧠 Central Nervous System initialized")
    except Exception as e:
        print(f"⚠️ CNS initialization failed: {e}")
        cns = None'''

            content = content.replace(lifespan_marker, cns_lifespan)

        # Update version to 134.0.0
        content = content.replace('version="133.0.0"', 'version="134.0.0"')
        content = content.replace('"version": "133.0.0"', '"version": "134.0.0"')
        content = content.replace('v133.0.0', 'v134.0.0')

        # Add CNS routes at the end, before if __name__ == "__main__"
        if 'if __name__ == "__main__":' in content:
            cns_routes = """
# ==================== CENTRAL NERVOUS SYSTEM ENDPOINTS ====================
# Create all CNS routes
if cns:
    create_cns_routes(app, cns)
    print("🧠 CNS routes registered")

"""
            content = content.replace(
                '\nif __name__ == "__main__":',
                f'{cns_routes}\nif __name__ == "__main__":'
            )

        # Write updated main.py
        with open('main.py', 'w') as f:
            f.write(content)

        print("✅ CNS integration complete!")
        print("✅ Updated to v134.0.0")
        print("✅ Added:")
        print("   - CNS service import")
        print("   - CNS initialization in lifespan")
        print("   - All CNS API endpoints")
        print("\n📝 CNS Endpoints added:")
        print("   - POST /api/v1/cns/memory - Store permanent memory")
        print("   - GET  /api/v1/cns/memory/search - Semantic search")
        print("   - POST /api/v1/cns/tasks - Create tasks")
        print("   - GET  /api/v1/cns/tasks - Get tasks")
        print("   - PUT  /api/v1/cns/tasks/{id}/status - Update task")
        print("   - POST /api/v1/cns/projects - Create projects")
        print("   - POST /api/v1/cns/threads - Create threads")
        print("   - POST /api/v1/cns/decisions - Record decisions")
        print("   - POST /api/v1/cns/automations - Create automation rules")
        print("   - GET  /api/v1/cns/status - System status")

        return True
    else:
        print("❌ Could not find AI service import marker")
        return False

if __name__ == "__main__":
    if integrate_cns():
        print("\n🚀 Next steps:")
        print("1. Test locally: python3 main.py")
        print("2. Build Docker: docker build -t mwwoodworth/brainops-backend:v134.0.0 .")
        print("3. Deploy to production")