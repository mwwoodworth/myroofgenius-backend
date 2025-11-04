#!/usr/bin/env python3
"""
Test Vercel Webhook Automation
CLAUDEOS Verification Script
"""

import httpx
import json
import hmac
import hashlib
from datetime import datetime

def test_webhook():
    """Test the webhook endpoint with proper signature"""
    
    webhook_url = "https://brainops-backend-prod.onrender.com/api/v1/webhooks/vercel"
    webhook_secret = "MQikxE5QJWYkTxc6sxMQgV5A"
    
    # Sample Vercel webhook payload
    test_payload = {
        "id": "test_deployment_123",
        "type": "deployment.created",
        "createdAt": int(datetime.utcnow().timestamp() * 1000),
        "payload": {
            "deploymentId": "test_123",
            "name": "myroofgenius-app",
            "url": "https://myroofgenius-test.vercel.app",
            "target": "production"
        },
        "teamId": "team_test",
        "userId": "user_test"
    }
    
    # Convert to JSON
    body = json.dumps(test_payload).encode()
    
    # Generate signature
    signature = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha1
    ).hexdigest()
    
    print("🧪 Testing Vercel Webhook Automation")
    print("=" * 50)
    print(f"Endpoint: {webhook_url}")
    print(f"Event Type: {test_payload['type']}")
    print(f"Signature: {signature}")
    print()
    
    # Send test webhook
    headers = {
        "Content-Type": "application/json",
        "x-vercel-signature": signature
    }
    
    with httpx.Client(timeout=30) as client:
        try:
            resp = client.post(webhook_url, content=body, headers=headers)
            print(f"Response Status: {resp.status_code}")
            
            if resp.status_code == 200:
                print("✅ Webhook processed successfully!")
                print(f"Response: {resp.json()}")
            else:
                print(f"❌ Error: {resp.text}")
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    # Test webhook status endpoint
    print("\n📊 Checking webhook status...")
    try:
        status_resp = client.get(f"{webhook_url}/status")
        if status_resp.status_code == 200:
            print("✅ Webhook status endpoint operational")
            print(f"Status: {json.dumps(status_resp.json(), indent=2)}")
        else:
            print(f"❌ Status check failed: {status_resp.status_code}")
    except Exception as e:
        print(f"❌ Status check error: {e}")

if __name__ == "__main__":
    test_webhook()