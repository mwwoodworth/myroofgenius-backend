#!/usr/bin/env python3

import requests
import json

# Backend API URL
base_url = "https://brainops-backend-prod.onrender.com"

# Test credentials
test_account = {"email": "admin@brainops.com", "password": "AdminPassword123!"}

def test_aurea_voice():
    print("Testing AUREA Voice Integration...\n")
    
    # 1. Login first
    print("1. Logging in...")
    response = requests.post(f"{base_url}/api/v1/auth/login", json=test_account)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    auth_token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {auth_token}'}
    print("✅ Login successful")
    
    # 2. Check AUREA status
    print("\n2. Checking AUREA status...")
    response = requests.get(f"{base_url}/api/v1/aurea/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ AUREA Status:")
        print(f"   Active: {data.get('active', False)}")
        print(f"   Version: {data.get('version', 'unknown')}")
        print(f"   Voice enabled: {data.get('voice_enabled', False)}")
    else:
        print(f"❌ Status check failed: {response.status_code}")
    
    # 3. Check voice capabilities
    print("\n3. Checking voice capabilities...")
    response = requests.get(f"{base_url}/api/v1/aurea/capabilities", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("✅ AUREA Capabilities:")
        capabilities = data.get('capabilities', {})
        print(f"   Voice synthesis: {capabilities.get('voice_synthesis', False)}")
        print(f"   Voice commands: {capabilities.get('voice_commands', False)}")
        print(f"   Continuous voice: {capabilities.get('continuous_voice', False)}")
        print(f"   Multi-language: {capabilities.get('multi_language', False)}")
    else:
        print(f"❌ Capabilities check failed: {response.status_code}")
    
    # 4. Test voice synthesis endpoint
    print("\n4. Testing voice synthesis...")
    voice_data = {
        "text": "Hello, this is AUREA testing voice synthesis capabilities.",
        "voice": "elevenlabs-conversational"
    }
    response = requests.post(f"{base_url}/api/v1/aurea/voice/synthesize", json=voice_data, headers=headers)
    if response.status_code == 200:
        print("✅ Voice synthesis endpoint working")
    elif response.status_code == 404:
        print("❌ Voice synthesis endpoint not found")
    else:
        print(f"❌ Voice synthesis failed: {response.status_code}")
    
    # 5. Check ElevenLabs integration
    print("\n5. Checking ElevenLabs integration...")
    response = requests.get(f"{base_url}/api/v1/integrations/elevenlabs/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("✅ ElevenLabs integration:")
        print(f"   Connected: {data.get('connected', False)}")
        print(f"   API key configured: {data.get('api_key_configured', False)}")
    elif response.status_code == 404:
        print("⚠️  ElevenLabs integration endpoint not found")
    else:
        print(f"❌ ElevenLabs check failed: {response.status_code}")
    
    # 6. Test AUREA commands
    print("\n6. Testing AUREA voice commands...")
    command_data = {
        "command": "What is the status of my roofing projects?",
        "voice_response": True
    }
    response = requests.post(f"{base_url}/api/v1/aurea/command", json=command_data, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print("✅ Voice command processed")
        print(f"   Response: {data.get('response', 'No response')[:100]}...")
    elif response.status_code == 404:
        print("❌ Voice command endpoint not found")
    else:
        print(f"❌ Voice command failed: {response.status_code}")
    
    print("\n✅ AUREA voice integration test complete!")

if __name__ == "__main__":
    test_aurea_voice()