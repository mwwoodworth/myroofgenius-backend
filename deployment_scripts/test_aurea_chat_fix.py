#!/usr/bin/env python3
"""
Test script to debug and fix AUREA chat validation error
"""

import requests
import json

BACKEND_URL = "https://brainops-backend-prod.onrender.com"

def test_aurea_chat_variations():
    """Test different payload formats to find what AUREA expects"""
    
    # Get auth token first
    login_resp = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json={"email": "test@brainops.com", "password": "TestPassword123!"}
    )
    
    if login_resp.status_code != 200:
        print(f"❌ Login failed: {login_resp.status_code}")
        return
        
    token = login_resp.json().get("access_token")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test variations
    test_payloads = [
        # Variation 1: Simple message
        {"message": "Test message"},
        
        # Variation 2: Message with context
        {"message": "Test message", "context": "integration_test"},
        
        # Variation 3: Messages array (OpenAI style)
        {"messages": [{"role": "user", "content": "Test message"}]},
        
        # Variation 4: Query field
        {"query": "Test message"},
        
        # Variation 5: Input field
        {"input": "Test message"},
        
        # Variation 6: Text field
        {"text": "Test message"},
        
        # Variation 7: Complete chat format
        {
            "message": "Test message",
            "context": "test",
            "session_id": "test-session",
            "user_id": "test-user"
        }
    ]
    
    print("Testing AUREA chat endpoint with different payloads...\n")
    
    for i, payload in enumerate(test_payloads, 1):
        print(f"Test {i}: {list(payload.keys())}")
        
        try:
            resp = requests.post(
                f"{BACKEND_URL}/api/v1/aurea/chat",
                json=payload,
                headers=headers
            )
            
            if resp.status_code == 200:
                print(f"✅ SUCCESS with payload: {json.dumps(payload)}")
                print(f"Response: {resp.json()}\n")
                return payload
            else:
                print(f"❌ Failed: {resp.status_code}")
                try:
                    error_detail = resp.json()
                    print(f"Error: {error_detail}\n")
                except:
                    print(f"Response: {resp.text[:200]}\n")
                    
        except Exception as e:
            print(f"❌ Exception: {str(e)}\n")
    
    print("All variations failed. Checking API docs...")
    
    # Try to get OpenAPI spec
    try:
        docs_resp = requests.get(f"{BACKEND_URL}/docs")
        if docs_resp.status_code == 200:
            print("✅ API docs available at /docs")
        
        openapi_resp = requests.get(f"{BACKEND_URL}/openapi.json")
        if openapi_resp.status_code == 200:
            spec = openapi_resp.json()
            # Look for AUREA chat endpoint
            for path, methods in spec.get("paths", {}).items():
                if "aurea/chat" in path:
                    print(f"\nFound AUREA chat endpoint: {path}")
                    if "post" in methods:
                        schema = methods["post"].get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
                        print(f"Expected schema: {json.dumps(schema, indent=2)}")
    except:
        pass

if __name__ == "__main__":
    test_aurea_chat_variations()