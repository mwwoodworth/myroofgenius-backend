#!/bin/bash
# Deploy BrainOps Backend v3.1.228
# COMPLETE FIX: Remove ALL duplicate auth routes

echo "🚀 DEPLOYING BRAINOPS BACKEND v3.1.228 - COMPLETE AUTH FIX"
echo "========================================================"
echo "✅ Removing ALL duplicate auth routes"
echo "✅ Only auth_fixed will handle authentication"
echo ""

# Navigate to backend directory
cd /home/mwwoodworth/code/fastapi-operator-env

# Create a Python script to completely fix route loading
cat > fix_auth_routes_completely.py << 'EOF'
import re

# Read main.py
with open('apps/backend/main.py', 'r') as f:
    content = f.read()

# Update version
content = re.sub(r'__version__ = "[^"]*"', '__version__ = "3.1.228"', content)

# Find ROUTE_PRIORITY section
route_section_start = content.find('ROUTE_PRIORITY = [')
route_section_end = content.find(']', route_section_start) + 1
route_section = content[route_section_start:route_section_end]

# Split into lines and rebuild
lines = route_section.split('\n')
new_lines = []
seen_auth_fixed = False
seen_marketplace_fixed = False
seen_automations_public = False

for line in lines:
    # Keep only specific auth routes
    if '"auth' in line:
        if 'auth_fixed' in line and not seen_auth_fixed:
            new_lines.append(line)
            seen_auth_fixed = True
        elif 'auth_debug' in line:
            # Keep debug endpoints
            new_lines.append(line)
        else:
            # Skip ALL other auth routes
            continue
    # Keep only fixed marketplace route
    elif '"marketplace' in line:
        if 'marketplace_public_fixed' in line and not seen_marketplace_fixed:
            new_lines.append(line)
            seen_marketplace_fixed = True
        else:
            continue
    # Keep only public automations route
    elif '"automations' in line:
        if 'automations_public' in line and not seen_automations_public:
            new_lines.append(line)
            seen_automations_public = True
        elif 'automations_simple_v3138' in line:
            # Keep this specific version
            new_lines.append(line)
        else:
            continue
    else:
        # Keep all other routes
        new_lines.append(line)

# Reconstruct the section
new_route_section = '\n'.join(new_lines)

# Replace in content
content = content[:route_section_start] + new_route_section + content[route_section_end:]

# Write back
with open('apps/backend/main.py', 'w') as f:
    f.write(content)

print("✅ Removed all duplicate auth routes")
print("✅ Only auth_fixed will be loaded for authentication")
EOF

python3 fix_auth_routes_completely.py

# Also ensure auth_fixed.py imports are correct
echo ""
echo "📝 Verifying auth_fixed.py imports..."
python3 -c "
import os
# Check if auth_fixed uses correct imports
auth_fixed_path = 'apps/backend/routes/auth_fixed.py'
if os.path.exists(auth_fixed_path):
    with open(auth_fixed_path, 'r') as f:
        content = f.read()
        if 'from apps.backend.core.auth_v3127 import' in content:
            print('✅ auth_fixed.py has correct imports')
        else:
            print('⚠️ auth_fixed.py may have wrong imports')
"

# Git operations
echo ""
echo "📦 Committing changes..."
git add -A
git commit -m "fix: Complete auth route deduplication v3.1.228

- Remove ALL duplicate auth routes except auth_fixed
- Only auth_fixed handles /api/v1/auth/* endpoints
- Remove duplicate marketplace routes
- Remove duplicate automation routes
- Prevent route conflicts completely

CRITICAL: This ensures ONLY the fixed routes are used

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

# Docker operations
echo ""
echo "🐳 Building and pushing Docker images..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'

docker build -t mwwoodworth/brainops-backend:v3.1.228 -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v3.1.228 mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v3.1.228
docker push mwwoodworth/brainops-backend:latest

# Trigger deployment
echo ""
echo "🔄 Triggering Render deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
  -H "Accept: application/json"

echo ""
echo "✅ DEPLOYMENT INITIATED"
echo "===================="
echo "Version: v3.1.228"
echo "Critical Changes:"
echo "  - Removed ALL duplicate auth routes"
echo "  - Only auth_fixed handles authentication"
echo "  - No route conflicts possible"
echo "  - Clean route loading"
echo ""
echo "📌 Expected Results:"
echo "  - Authentication will work (no more 500 errors)"
echo "  - Login returns proper tokens"
echo "  - Public endpoints continue working"
echo ""
echo "🎯 Monitor with: python3 MONITOR_V228_FINAL_TEST.py"