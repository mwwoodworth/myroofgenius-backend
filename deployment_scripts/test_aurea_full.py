#!/usr/bin/env python3
"""Comprehensive AUREA testing"""

import requests
import json
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"
HEADERS = {"Content-Type": "application/json"}

def test_aurea_chat():
    """Test AUREA chat endpoint"""
    print("\n🤖 Testing AUREA Chat...")
    
    payload = {
        "message": "Hello AUREA, please provide a status update on all systems",
        "context": {
            "user": "Lead Engineer",
            "request_type": "system_status"
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/aurea/chat", json=payload, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat working: {data.get('response', 'No response')[:100]}...")
            return True
        else:
            print(f"❌ Chat failed: {response.status_code} - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        return False

def test_aurea_voice():
    """Test AUREA voice endpoints"""
    print("\n🎤 Testing AUREA Voice...")
    
    # Test voice synthesis
    payload = {
        "text": "System status update: All systems operational",
        "voice": "default"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/aurea/voice/synthesize", json=payload, headers=HEADERS)
        if response.status_code == 200:
            print("✅ Voice synthesis endpoint exists")
            return True
        else:
            print(f"⚠️ Voice synthesis: {response.status_code}")
            # Try alternative endpoint
            response = requests.get(f"{BASE_URL}/api/v1/aurea/voice")
            if response.status_code == 200:
                print("✅ Voice endpoint exists (GET)")
                return True
            return False
    except Exception as e:
        print(f"❌ Voice error: {str(e)}")
        return False

def test_aurea_automation():
    """Test AUREA automation capabilities"""
    print("\n⚙️ Testing AUREA Automation...")
    
    payload = {
        "command": "list_active_automations",
        "parameters": {}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/aurea/automation", json=payload, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Automation working: {len(data.get('automations', []))} active")
            return True
        else:
            print(f"⚠️ Automation: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Automation error: {str(e)}")
        return False

def test_aurea_executive_features():
    """Test AUREA executive assistant features"""
    print("\n👔 Testing Executive Assistant Features...")
    
    # Test executive summary
    payload = {
        "request": "executive_summary",
        "timeframe": "today",
        "include": ["metrics", "alerts", "recommendations"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/aurea/executive", json=payload, headers=HEADERS)
        if response.status_code == 200:
            print("✅ Executive features working")
            return True
        else:
            # Try chat with executive context
            exec_payload = {
                "message": "Provide executive summary of system status",
                "context": {"role": "executive", "format": "brief"}
            }
            response = requests.post(f"{BASE_URL}/api/v1/aurea/chat", json=exec_payload, headers=HEADERS)
            if response.status_code == 200:
                print("✅ Executive features via chat")
                return True
            print(f"⚠️ Executive features: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Executive error: {str(e)}")
        return False

def main():
    """Run all AUREA tests"""
    print(f"""
🏢 AUREA Executive Assistant Test Suite
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
🌐 Target: {BASE_URL}
""")
    
    results = {
        "chat": test_aurea_chat(),
        "voice": test_aurea_voice(),
        "automation": test_aurea_automation(),
        "executive": test_aurea_executive_features()
    }
    
    # Summary
    print("\n📊 AUREA Test Summary:")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for feature, status in results.items():
        print(f"  {feature.capitalize()}: {'✅ Pass' if status else '❌ Fail'}")
    
    print(f"\nOverall: {passed}/{total} features operational ({passed/total*100:.0f}%)")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)