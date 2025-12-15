#!/usr/bin/env python3

import re

# Read the current .env file
with open('/home/mwwoodworth/code/fastapi-operator-env/.env', 'r') as f:
    content = f.read()

# Define replacements
replacements = {
    # Update database URLs with correct password
    r'postgresql://postgres\.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@': 'postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@',
    
    # Update SUPABASE_DB_PASSWORD
    r'SUPABASE_DB_PASSWORD=Mww00dw0rth@2O1S\$': 'SUPABASE_DB_PASSWORD=<DB_PASSWORD_REDACTED>',
    
    # Update SUPABASE_SERVICE_ROLE_KEY
    r'SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9\.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNzA1ODk1MjAwLCJleHAiOjIwNjI2MTkyMDB9\.Tq5YfA5r8VqMEz_k7sYPcdmwhBVq0wGZBxq7Q3RXrAo': 
    'SUPABASE_SERVICE_ROLE_KEY=<JWT_REDACTED>'
}

# Apply replacements
for pattern, replacement in replacements.items():
    content = re.sub(pattern, replacement, content)

# Write the updated content back
with open('/home/mwwoodworth/code/fastapi-operator-env/.env', 'w') as f:
    f.write(content)

print("✅ Backend .env file updated with correct credentials")