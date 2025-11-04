#!/usr/bin/env python3
"""Test AI streaming endpoint"""

import requests
import json

# Test AI streaming
url = "https://brainops-backend-prod.onrender.com/api/v1/ai/ai/stream"
payload = {
    "prompt": "What are the best roofing materials for extreme weather?",
    "provider": "openai",
    "max_tokens": 100,
    "stream": True
}

print("Testing AI Streaming Endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("-" * 50)

try:
    response = requests.post(url, json=payload, stream=True)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("\nStreaming Response:")
        for line in response.iter_lines():
            if line:
                print(line.decode('utf-8'))
                if len(line) > 200:  # Stop after getting some content
                    break
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Test SEO generation
print("\n" + "=" * 50)
print("Testing SEO Content Generation...")
seo_url = "https://brainops-backend-prod.onrender.com/api/v1/ai/ai/seo/generate"
seo_payload = {
    "topic": "Metal Roofing Installation",
    "keywords": ["metal roofing", "installation", "durability", "cost-effective"],
    "target_length": 1000,
    "tone": "professional"
}

try:
    response = requests.post(seo_url, json=seo_payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\nSEO Content Generated:")
        print(f"Title: {result.get('title')}")
        print(f"Meta Description: {result.get('meta_description')}")
        print(f"Readability Score: {result.get('readability_score')}")
        print(f"Keywords Density: {result.get('keywords_density')}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")