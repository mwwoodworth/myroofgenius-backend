#!/usr/bin/env python3

import re

# Read the current .env file
with open('/home/mwwoodworth/code/fastapi-operator-env/.env', 'r') as f:
    content = f.read()

# Define replacements
replacements = {
    # Update database URLs with correct password
    r'postgresql://postgres\.yomagoqdmxszqtdwuhab:Mww00dw0rth%402O1S\$@': 'postgresql://postgres.yomagoqdmxszqtdwuhab:Brain0ps2O2S@',
    
    # Update SUPABASE_DB_PASSWORD
    r'SUPABASE_DB_PASSWORD=Mww00dw0rth@2O1S\$': 'SUPABASE_DB_PASSWORD=Brain0ps2O2S',
    
    # Update SUPABASE_SERVICE_ROLE_KEY
    r'SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNzA1ODk1MjAwLCJleHAiOjIwNjI2MTkyMDB9\.Tq5YfA5r8VqMEz_k7sYPcdmwhBVq0wGZBxq7Q3RXrAo': 
    'SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTgzMzI3NiwiZXhwIjoyMDY1NDA5Mjc2fQ.7C3guJ_0moYGkdyeFmJ9cd2BmduB5NnU00erIIxH3gQ'
}

# Apply replacements
for pattern, replacement in replacements.items():
    content = re.sub(pattern, replacement, content)

# Write the updated content back
with open('/home/mwwoodworth/code/fastapi-operator-env/.env', 'w') as f:
    f.write(content)

print("✅ Backend .env file updated with correct credentials")