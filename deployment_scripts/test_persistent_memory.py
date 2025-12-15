#\!/usr/bin/env python3
import requests
import json
from datetime import datetime

# Supabase configuration
SUPABASE_URL = "https://yomagoqdmxszqtdwuhab.supabase.co"
SUPABASE_KEY = "<JWT_REDACTED>"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("🔍 Testing Persistent Memory System...")
print("=" * 50)

# Test memory read
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/copilot_messages?select=*&order=created_at.desc&limit=5",
        headers=headers
    )
    if response.status_code == 200:
        memories = response.json()
        print(f"✅ Persistent Memory Access: {len(memories)} recent entries found")
        if memories:
            print(f"   Latest: {memories[0].get('title', 'No title')[:50]}...")
    else:
        print(f"❌ Memory read failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error accessing memory: {str(e)}")

print("\n📊 Persistent Memory Status: CONFIGURED")
