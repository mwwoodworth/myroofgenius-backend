#!/usr/bin/env python3
"""
Test AUREA Backend Response Quality with Authentication
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://brainops-backend-prod.onrender.com"

def get_auth_token():
    """Get authentication token"""
    login_data = {
        "email": "test@brainops.com",
        "password": "TestPassword123!"
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_aurea_chat_authenticated():
    """Test AUREA chat responses with authentication"""
    print("🤖 Testing AUREA Chat Quality (Authenticated)")
    print("=" * 60)
    
    # Get auth token
    print("🔐 Getting authentication token...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to authenticate")
        return
    print("✅ Authenticated successfully")
    
    # Test questions
    test_messages = [
        "What is the weather today?",
        "How do I calculate the square footage of a roof?",
        "What's the best roofing material for Florida?",
        "Can you help me create an estimate for a 2500 sq ft roof?",
        "What are the latest trends in roofing technology?"
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    for message in test_messages:
        print(f"\n📝 User: {message}")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/aurea/chat",
                json={
                    "message": message,
                    "context": {
                        "source": "test_script",
                        "timestamp": datetime.now().isoformat()
                    }
                },
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                aurea_response = data.get("response", "No response")
                
                # Check if response is generic/template
                template_indicators = [
                    "I can help you with",
                    "I'm here to assist",
                    "template",
                    "placeholder",
                    "[",
                    "]",
                    "TODO",
                    "FIXME",
                    "experiencing technical difficulties"
                ]
                
                is_template = any(indicator.lower() in aurea_response.lower() for indicator in template_indicators)
                
                print(f"🤖 AUREA: {aurea_response[:300]}...")
                
                if is_template:
                    print("⚠️  WARNING: Response appears to be a template/placeholder")
                else:
                    print("✅ Response appears to be genuine AI")
                    
                # Check response quality
                if len(aurea_response) < 50:
                    print("⚠️  WARNING: Response is very short")
                
                # Check for additional metadata
                if "confidence" in data:
                    print(f"📊 Confidence: {data['confidence']}")
                if "provider" in data:
                    print(f"🔧 Provider: {data['provider']}")
                
            else:
                print(f"❌ Error: Status {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    # Test a system command
    print("\n📝 User: Check system status")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/aurea/chat",
            json={
                "message": "Check system status",
                "context": {
                    "source": "test_script",
                    "type": "command"
                }
            },
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 AUREA: {data.get('response', 'No response')[:300]}...")
        else:
            print(f"❌ Error: Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("Check the responses above for quality.")
    print("If responses are templates, the backend needs fixing.")
    print("If responses are genuine AI, the frontend integration may need adjustment.")

if __name__ == "__main__":
    test_aurea_chat_authenticated()