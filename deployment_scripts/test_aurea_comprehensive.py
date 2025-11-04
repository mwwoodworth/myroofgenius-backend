#!/usr/bin/env python3
"""
Comprehensive AUREA Testing Suite
Tests various commands and response types
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "https://brainops-backend-prod.onrender.com"
AUREA_ENDPOINT = f"{BASE_URL}/api/v1/aurea-simple/command"

# Test questions covering different categories
TEST_COMMANDS = [
    # Revenue & Business
    {
        "category": "Revenue",
        "command": "Show me today's revenue",
        "voice_enabled": False
    },
    {
        "category": "Revenue",
        "command": "What's our revenue this week?",
        "voice_enabled": False
    },
    {
        "category": "Revenue", 
        "command": "How much money did we make this month?",
        "voice_enabled": False
    },
    
    # Tasks & Productivity
    {
        "category": "Tasks",
        "command": "What are my urgent tasks?",
        "voice_enabled": False
    },
    {
        "category": "Tasks",
        "command": "Create a task to call Johnson about the roof estimate",
        "voice_enabled": False
    },
    {
        "category": "Tasks",
        "command": "Show me all pending tasks",
        "voice_enabled": False
    },
    
    # Email & Communication
    {
        "category": "Email",
        "command": "Draft an email to update the client on project status",
        "voice_enabled": False
    },
    {
        "category": "Email",
        "command": "Send email to team about tomorrow's meeting",
        "voice_enabled": False
    },
    
    # System Status
    {
        "category": "Status",
        "command": "Give me a complete system status update",
        "voice_enabled": False
    },
    {
        "category": "Status",
        "command": "How is the business doing today?",
        "voice_enabled": False
    },
    
    # Voice & Greeting
    {
        "category": "Greeting",
        "command": "Hello AUREA, how are you?",
        "voice_enabled": True  # Test with voice
    },
    {
        "category": "Greeting",
        "command": "Good morning AUREA",
        "voice_enabled": False
    },
    
    # Complex Queries
    {
        "category": "Complex",
        "command": "Analyze our top performing projects and suggest improvements",
        "voice_enabled": False
    },
    {
        "category": "Complex",
        "command": "What should I focus on today to maximize revenue?",
        "voice_enabled": False
    },
    {
        "category": "Complex",
        "command": "Schedule a roof inspection for next Tuesday at 2pm",
        "voice_enabled": False
    },
    
    # Edge Cases
    {
        "category": "Edge",
        "command": "Help",
        "voice_enabled": False
    },
    {
        "category": "Edge",
        "command": "Cancel",
        "voice_enabled": False
    },
    {
        "category": "Edge",
        "command": "Show me the weather",  # Out of scope
        "voice_enabled": False
    }
]

def test_aurea_command(command_data):
    """Test a single AUREA command"""
    try:
        response = requests.post(
            AUREA_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json=command_data,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "error": response.text
            }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "error": str(e)
        }

def main():
    """Run comprehensive AUREA tests"""
    print("🧪 AUREA Comprehensive Testing Suite")
    print("=" * 60)
    print(f"Testing {len(TEST_COMMANDS)} different commands")
    print(f"Endpoint: {AUREA_ENDPOINT}")
    print("=" * 60)
    
    results = {
        "total": len(TEST_COMMANDS),
        "successful": 0,
        "failed": 0,
        "categories": {},
        "voice_tests": 0,
        "voice_urls": 0
    }
    
    # Run all tests
    for i, test in enumerate(TEST_COMMANDS, 1):
        print(f"\n[{i}/{len(TEST_COMMANDS)}] Testing: {test['command']}")
        print(f"Category: {test['category']} | Voice: {test['voice_enabled']}")
        
        # Small delay to avoid rate limiting
        if i > 1:
            time.sleep(0.5)
        
        result = test_aurea_command(test)
        
        # Track category results
        category = test['category']
        if category not in results['categories']:
            results['categories'][category] = {"success": 0, "total": 0}
        results['categories'][category]['total'] += 1
        
        if result['success']:
            results['successful'] += 1
            results['categories'][category]['success'] += 1
            
            data = result['data']
            print(f"✅ Success!")
            print(f"Response: {data.get('response', 'No response')[:100]}...")
            
            # Check voice
            if test['voice_enabled']:
                results['voice_tests'] += 1
                if data.get('voice_url'):
                    results['voice_urls'] += 1
                    print(f"🎤 Voice URL: {data['voice_url']}")
            
            # Check actions
            if data.get('actions_taken'):
                print(f"Actions: {data['actions_taken']}")
        else:
            results['failed'] += 1
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {results['total']}")
    print(f"✅ Successful: {results['successful']} ({results['successful']/results['total']*100:.1f}%)")
    print(f"❌ Failed: {results['failed']}")
    print(f"🎤 Voice Tests: {results['voice_tests']} (URLs returned: {results['voice_urls']})")
    
    print("\n📈 Results by Category:")
    for category, stats in results['categories'].items():
        success_rate = stats['success'] / stats['total'] * 100
        print(f"  {category}: {stats['success']}/{stats['total']} ({success_rate:.0f}%)")
    
    # Test response time
    print("\n⚡ Response Time Test:")
    start = time.time()
    test_aurea_command({"command": "Quick test", "voice_enabled": False})
    response_time = (time.time() - start) * 1000
    print(f"Average response time: {response_time:.0f}ms")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"aurea_test_report_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "response_time_ms": response_time
        }, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    print("\n✅ Testing complete!")

if __name__ == "__main__":
    main()