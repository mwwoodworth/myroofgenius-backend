#!/usr/bin/env python3
"""
Fix parameter names in auth.py to resolve FastAPI conflicts
"""

# Read the file
with open('fastapi-operator-env/apps/backend/routes/auth.py', 'r') as f:
    content = f.read()

# Replace all occurrences of problematic parameter names
replacements = [
    # Login function
    ('async def login(\n    request: LoginRequest,\n    req: Request,',
     'async def login(\n    login_data: LoginRequest,\n    http_request: Request,'),
    
    # Register function
    ('async def register(\n    request: RegisterRequest,\n    req: Request,',
     'async def register(\n    register_data: RegisterRequest,\n    http_request: Request,'),
    
    # Refresh function
    ('async def refresh_token(\n    request: RefreshRequest,',
     'async def refresh_token(\n    refresh_data: RefreshRequest,'),
     
    # Update all uses of 'request' parameter to appropriate names
    ('authenticate_user(request.email, request.password, db)',
     'authenticate_user(login_data.email, login_data.password, db)'),
     
    ('db.query(User).filter(User.email == request.email).first()',
     'db.query(User).filter(User.email == register_data.email).first()'),
     
    ('email=request.email,',
     'email=register_data.email,'),
     
    ('username=request.username or request.email.split',
     'username=register_data.username or register_data.email.split'),
     
    ('hashed_password=get_password_hash(request.password),',
     'hashed_password=get_password_hash(register_data.password),'),
     
    ('payload = decode_token(request.refresh_token)',
     'payload = decode_token(refresh_data.refresh_token)'),
     
    # Update all uses of 'req' parameter
    ('"ip_address": req.client.host if req.client else "unknown",',
     '"ip_address": http_request.client.host if http_request.client else "unknown",'),
     
    ('"user_agent": req.headers.get("user-agent", "unknown")',
     '"user_agent": http_request.headers.get("user-agent", "unknown")'),
]

# Apply all replacements
for old, new in replacements:
    content = content.replace(old, new)

# Also fix any standalone cases
content = content.replace('request.email', 'login_data.email')
content = content.replace('request.password', 'login_data.password')

# Write back
with open('fastapi-operator-env/apps/backend/routes/auth.py', 'w') as f:
    f.write(content)

print("✅ Fixed parameter names in auth.py")
print("✅ No more 'request' or 'req' parameter conflicts")