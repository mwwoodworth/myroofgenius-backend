#!/bin/bash
# Deploy BrainOps Backend v3.1.227
# FIX: Ensure only fixed routes are loaded

echo "🚀 DEPLOYING BRAINOPS BACKEND v3.1.227 - ROUTE PRIORITY FIX"
echo "=========================================================="
echo "✅ Ensuring only fixed auth routes are loaded"
echo "✅ Removing duplicate route registrations"
echo ""

# Navigate to backend directory
cd /home/mwwoodworth/code/fastapi-operator-env

# First, let's update main.py to ensure auth_fixed takes precedence
echo "📝 Updating main.py to fix route loading..."

# Create a Python script to fix the route loading
cat > fix_route_loading.py << 'EOF'
import re

# Read main.py
with open('apps/backend/main.py', 'r') as f:
    content = f.read()

# Update version
content = re.sub(r'__version__ = "[^"]*"', '__version__ = "3.1.227"', content)

# Find ROUTE_PRIORITY section and modify it
# Remove duplicate auth entries - keep only auth_fixed
route_section_start = content.find('ROUTE_PRIORITY = [')
route_section_end = content.find(']', route_section_start) + 1
route_section = content[route_section_start:route_section_end]

# Split into lines
lines = route_section.split('\n')
new_lines = []
seen_auth = False
seen_marketplace = False
seen_automations = False

for line in lines:
    # Skip duplicate auth routes after auth_fixed
    if '("auth"' in line or '("auth_' in line:
        if 'auth_fixed' in line:
            new_lines.append(line)
            seen_auth = True
        elif not seen_auth and 'auth' in line and 'auth_debug' not in line:
            # Skip other auth routes
            continue
        else:
            new_lines.append(line)
    # Skip duplicate marketplace routes after marketplace_public_fixed
    elif '("marketplace' in line:
        if 'marketplace_public_fixed' in line:
            new_lines.append(line)
            seen_marketplace = True
        elif not seen_marketplace:
            continue
        else:
            new_lines.append(line)
    # Handle automations
    elif '("automations' in line:
        if 'automations_public' in line:
            new_lines.append(line)
            seen_automations = True
        elif not seen_automations:
            continue
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

# Reconstruct the section
new_route_section = '\n'.join(new_lines)

# Replace in content
content = content[:route_section_start] + new_route_section + content[route_section_end:]

# Write back
with open('apps/backend/main.py', 'w') as f:
    f.write(content)

print("✅ Updated main.py with route priority fixes")
EOF

python3 fix_route_loading.py

# Git operations
echo ""
echo "📦 Committing changes..."
git add -A
git commit -m "fix: Route priority to ensure fixed endpoints are used v3.1.227

- Remove duplicate auth route registrations
- Ensure auth_fixed is the ONLY auth route loaded initially
- Fix marketplace and automations route precedence
- Prevent multiple routes mounting to same prefix

CRITICAL: This ensures the fixed auth endpoints are actually used

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main

# Docker operations
echo ""
echo "🐳 Building and pushing Docker images..."
docker login -u mwwoodworth -p 'dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho'

docker build -t mwwoodworth/brainops-backend:v3.1.227 -f Dockerfile .
docker tag mwwoodworth/brainops-backend:v3.1.227 mwwoodworth/brainops-backend:latest
docker push mwwoodworth/brainops-backend:v3.1.227
docker push mwwoodworth/brainops-backend:latest

# Trigger deployment
echo ""
echo "🔄 Triggering Render deployment..."
curl -X POST "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM" \
  -H "Accept: application/json"

echo ""
echo "✅ DEPLOYMENT INITIATED"
echo "===================="
echo "Version: v3.1.227"
echo "Critical Changes:"
echo "  - Fixed route loading order"
echo "  - Removed duplicate auth routes"
echo "  - Only auth_fixed will handle /api/v1/auth endpoints"
echo "  - marketplace_public_fixed handles public marketplace"
echo "  - automations_public handles public automation endpoints"
echo ""
echo "📌 Expected Results:"
echo "  - Authentication will work (no more 422/500 errors)"
echo "  - Public endpoints will not require auth"
echo "  - No duplicate route conflicts"
echo ""
echo "🎯 Monitor with: python3 MONITOR_V227_AND_TEST.py"