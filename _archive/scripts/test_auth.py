import requests
import json

url = "https://brainops-backend-prod.onrender.com/api/v1/auth/login"
data = {
    "email": "test@brainops.com",
    "password": "TestPassword123!"
}

response = requests.post(url, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

if response.status_code == 200:
    token_data = response.json()
    print(f"✅ Auth successful! Access token: {token_data.get('access_token', '')[:50]}...")
else:
    print(f"❌ Auth failed")
