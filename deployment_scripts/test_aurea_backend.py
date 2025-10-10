#!/usr/bin/env python3
"""
Test AUREA Backend Response Quality
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://brainops-backend-prod.onrender.com"

def test_aurea_chat():
    """Test AUREA chat responses"""
    print("🤖 Testing AUREA Chat Quality")
    print("=" * 60)
    
    # Test questions
    test_messages = [
        "What is the weather today?",
        "How do I calculate the square footage of a roof?",
        "What's the best roofing material for Florida?",
        "Can you help me create an estimate for a 2500 sq ft roof?",
        "What are the latest trends in roofing technology?"
    ]
    
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
                headers={"Content-Type": "application/json"},
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
                    "FIXME"
                ]
                
                is_template = any(indicator in aurea_response for indicator in template_indicators)
                
                print(f"🤖 AUREA: {aurea_response[:200]}...")
                
                if is_template:
                    print("⚠️  WARNING: Response appears to be a template/placeholder")
                else:
                    print("✅ Response appears to be genuine AI")
                    
                # Check response quality
                if len(aurea_response) < 50:
                    print("⚠️  WARNING: Response is very short")
                
            else:
                print(f"❌ Error: Status {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print("AUREA backend is responding, but check response quality above.")
    print("If responses are templates, the issue is on the backend.")

if __name__ == "__main__":
    test_aurea_chat()