import requests
import json

# Test Create Memory endpoint directly
base_url = "https://brainops-backend-prod.onrender.com/api/v1"

# Login first
login_data = {
    "email": "test@brainops.com",
    "password": "TestPassword123\!"
}
login_resp = requests.post(f"{base_url}/auth/login", json=login_data)
if login_resp.status_code == 200:
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create memory
    memory_data = {
        "title": "Test Memory",
        "content": "Test content",
        "memory_type": "general",
        "role": "user",
        "meta_data": {},
        "tags": []
    }
    
    resp = requests.post(f"{base_url}/memory/create", headers=headers, json=memory_data)
    print(f"Status: {resp.status_code}")
    if resp.status_code \!= 200:
        print(f"Response: {resp.text}")
    else:
        print(f"Success: {json.dumps(resp.json(), indent=2)}")
else:
    print(f"Login failed: {login_resp.status_code}")
    print(f"Response: {login_resp.text}")
ENDFILE < /dev/null
