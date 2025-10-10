#\!/usr/bin/env python3
import requests
import json
from datetime import datetime

# Supabase configuration
SUPABASE_URL = "https://yomagoqdmxszqtdwuhab.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTgzMzI3NiwiZXhwIjoyMDY1NDA5Mjc2fQ.7C3guJ_0moYGkdyeFmJ9cd2BmduB5NnU00erIIxH3gQ"

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
