#!/usr/bin/env python3

import requests
import json
import time

# Backend API URL  
base_url = "https://brainops-backend-prod.onrender.com"

# Test credentials
test_account = {"email": "admin@brainops.com", "password": "AdminPassword123!"}

def test_integrations():
    print("Testing All Integration Endpoints...\n")
    
    # 1. Login first
    print("1. Logging in...")
    response = requests.post(f"{base_url}/api/v1/auth/login", json=test_account, timeout=10)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    auth_token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {auth_token}'}
    print("✅ Login successful")
    
    # Wait for deployment to complete
    print("\n⏳ Waiting 30s for deployment to complete...")
    time.sleep(30)
    
    # 2. Test all integration status endpoints
    print("\n2. Testing Integration Status Endpoints...")
    integrations = [
        ("GitHub", "/api/v1/integrations/github/status"),
        ("Slack", "/api/v1/integrations/slack/status"),
        ("Stripe", "/api/v1/integrations/stripe/status"),
        ("ClickUp", "/api/v1/integrations/clickup/status"),
        ("ElevenLabs", "/api/v1/integrations/elevenlabs/status")
    ]
    
    for name, endpoint in integrations:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ {name} Status:")
                print(f"   Connected: {data.get('connected', False)}")
                print(f"   API Key Configured: {data.get('api_key_configured', False)}")
                if data.get('connected'):
                    # Show additional info
                    if 'username' in data:
                        print(f"   Username: {data.get('username')}")
                    if 'workspace' in data:
                        print(f"   Workspace: {data.get('workspace')}")
                    if 'subscription' in data:
                        print(f"   Subscription: {data.get('subscription')}")
            else:
                print(f"\n❌ {name}: {response.status_code}")
        except Exception as e:
            print(f"\n❌ {name} Error: {e}")
    
    # 3. Test automation endpoints
    print("\n\n3. Testing Automation Endpoints...")
    automation_endpoints = [
        ("GET", "/api/v1/automations/types", None, "Automation Types"),
        ("GET", "/api/v1/automations/history", None, "Automation History"),
        ("GET", "/api/v1/automations/types/daily_seo_analysis", None, "SEO Analysis Details")
    ]
    
    for method, endpoint, data, description in automation_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=5)
            else:
                response = requests.post(f"{base_url}{endpoint}", json=data, headers=headers, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ {description}:")
                if 'automation_types' in result:
                    print(f"   Total types: {result.get('total', 0)}")
                    print(f"   Categories: {', '.join(result.get('categories', []))}")
                elif 'history' in result:
                    print(f"   Total runs: {result.get('total', 0)}")
                    if result.get('statistics'):
                        stats = result['statistics']
                        print(f"   Success rate: {stats.get('success_rate', 0)}%")
                elif 'type' in result:
                    print(f"   Type: {result.get('type')}")
                    print(f"   Category: {result.get('category')}")
                    print(f"   Schedule: {result.get('schedule')}")
            else:
                print(f"\n❌ {description}: {response.status_code}")
        except Exception as e:
            print(f"\n❌ {description} Error: {e}")
    
    # 4. Test AUREA voice endpoints
    print("\n\n4. Testing AUREA Voice Endpoints...")
    voice_endpoints = [
        ("GET", "/api/v1/aurea/voice/status", None, "Voice Status"),
        ("GET", "/api/v1/aurea/voice/voices", None, "Available Voices"),
        ("POST", "/api/v1/aurea/voice/synthesize", {
            "text": "Hello, this is a test of the AUREA voice system.",
            "voice": "elevenlabs-conversational"
        }, "Voice Synthesis")
    ]
    
    for method, endpoint, data, description in voice_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=5)
            else:
                response = requests.post(f"{base_url}{endpoint}", json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ {description}:")
                if 'voice_enabled' in result:
                    print(f"   Voice enabled: {result.get('voice_enabled')}")
                    print(f"   Continuous voice: {result.get('continuous_voice')}")
                    if result.get('elevenlabs'):
                        print(f"   ElevenLabs connected: {result['elevenlabs'].get('connected')}")
                elif 'voices' in result:
                    print(f"   Available voices: {len(result.get('voices', []))}")
                    for voice in result.get('voices', [])[:3]:
                        print(f"   - {voice.get('name')} ({voice.get('id')})")
                elif 'audio_base64' in result:
                    print(f"   Audio generated: Yes")
                    print(f"   Duration estimate: {result.get('duration_estimate', 0):.1f}s")
            else:
                print(f"\n❌ {description}: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text[:200]}")
        except Exception as e:
            print(f"\n❌ {description} Error: {e}")
    
    print("\n\n✅ Integration test complete!")

if __name__ == "__main__":
    test_integrations()