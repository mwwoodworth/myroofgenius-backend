#!/usr/bin/env python3

# Read the current .env file
with open('/home/mwwoodworth/code/fastapi-operator-env/.env', 'r') as f:
    lines = f.readlines()

# Process each line
updated_lines = []
for line in lines:
    # Update DB URLs
    if line.startswith('DB_URL=') or line.startswith('DATABASE_URL=') or line.startswith('SUPABASE_DB_URL='):
        if 'Mww00dw0rth%402O1S%24' in line:
            line = line.replace('Mww00dw0rth%402O1S%24', 'Brain0ps2O2S')
    
    updated_lines.append(line)

# Write the updated content back
with open('/home/mwwoodworth/code/fastapi-operator-env/.env', 'w') as f:
    f.writelines(updated_lines)

print("✅ Backend .env file database URLs updated")