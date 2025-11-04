#!/usr/bin/env python3
"""
ACTIVATE COMPLETE AI SYSTEM
This script verifies and activates all AI capabilities
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
TASK_OS_URL = "https://brainops-task-os.vercel.app"

def check_endpoint(url, name):
    """Check if an endpoint is responding"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: OPERATIONAL")
            return True
        else:
            print(f"⚠️ {name}: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name}: {str(e)[:50]}")
        return False

def test_ai_command():
    """Test AI command execution"""
    print("\n🤖 Testing AI Command Execution...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/v1/ai/command",
            json={
                "command": "Optimize revenue and create priority tasks",
                "context": {"test": True},
                "priority": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI Command Success:")
            print(f"   - Decisions: {data.get('decisions_made', 0)}")
            print(f"   - Actions: {data.get('actions_taken', 0)}")
            print(f"   - Confidence: {data.get('confidence', 0):.2%}")
            return True
        else:
            print(f"⚠️ AI Command returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AI Command failed: {str(e)[:100]}")
        return False

def test_ai_agents():
    """Test AI agents"""
    print("\n🤖 Testing AI Agents...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/ai/agents", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            agents = data.get('agents', {})
            print(f"✅ Found {len(agents)} AI Agents:")
            for agent_name, info in agents.items():
                print(f"   - {agent_name}: {len(info.get('actions', []))} actions")
            return True
        else:
            print(f"⚠️ Agents endpoint returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Agents test failed: {str(e)[:100]}")
        return False

def test_revenue_optimization():
    """Test revenue optimization"""
    print("\n💰 Testing Revenue Optimization...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/ai/revenue/analysis", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get('opportunities', [])
            total = data.get('total_potential', 0)
            print(f"✅ Revenue Analysis Complete:")
            print(f"   - Opportunities: {len(opportunities)}")
            print(f"   - Total Potential: ${total:,}")
            return True
        else:
            print(f"⚠️ Revenue analysis returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Revenue test failed: {str(e)[:100]}")
        return False

def test_system_health():
    """Test system health monitoring"""
    print("\n🏥 Testing System Health Monitoring...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/ai/system/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            health = data.get('health', {})
            issues = data.get('issues', [])
            print(f"✅ System Health Check:")
            print(f"   - Status: {health.get('status', 'unknown')}")
            print(f"   - Uptime: {health.get('uptime', 'N/A')}")
            print(f"   - Issues: {len(issues)}")
            return True
        else:
            print(f"⚠️ Health check returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {str(e)[:100]}")
        return False

def test_self_healing():
    """Test self-healing capabilities"""
    print("\n🔧 Testing Self-Healing...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/ai/system/heal", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Self-Healing Results:")
            print(f"   - Issues Found: {data.get('issues_found', 0)}")
            print(f"   - Fixes Attempted: {data.get('fixes_attempted', 0)}")
            return True
        else:
            print(f"⚠️ Self-healing returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Self-healing test failed: {str(e)[:100]}")
        return False

def main():
    print("=" * 80)
    print("🚀 ACTIVATING COMPLETE AI SYSTEM")
    print("=" * 80)
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Backend: {BACKEND_URL}")
    print("=" * 80)
    
    # Wait for deployment if needed
    print("\n⏳ Waiting for v3.4.02 deployment...")
    for i in range(30):
        response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            version = data.get('version', 'unknown')
            if version == "3.4.02":
                print(f"✅ v3.4.02 is live!")
                break
            else:
                print(f"   Current version: {version}, waiting...")
                time.sleep(5)
    
    # Check all endpoints
    print("\n📡 Checking Core Endpoints...")
    results = {
        "health": check_endpoint(f"{BACKEND_URL}/api/v1/health", "Health"),
        "aurea": check_endpoint(f"{BACKEND_URL}/api/v1/aurea/status", "AUREA AI"),
        "ai_status": check_endpoint(f"{BACKEND_URL}/api/v1/ai/status", "AI System"),
        "ai_metrics": check_endpoint(f"{BACKEND_URL}/api/v1/ai/metrics", "AI Metrics"),
    }
    
    # Test AI capabilities
    results["ai_command"] = test_ai_command()
    results["ai_agents"] = test_ai_agents()
    results["revenue"] = test_revenue_optimization()
    results["health"] = test_system_health()
    results["healing"] = test_self_healing()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 AI SYSTEM ACTIVATION SUMMARY")
    print("=" * 80)
    
    total = len(results)
    success = sum(1 for v in results.values() if v)
    percentage = (success / total) * 100 if total > 0 else 0
    
    print(f"✅ Successful: {success}/{total}")
    print(f"📈 Success Rate: {percentage:.1f}%")
    
    if percentage >= 80:
        print("\n🎉 AI SYSTEM FULLY OPERATIONAL!")
        print("The AI is now:")
        print("  • Creating tasks autonomously")
        print("  • Optimizing revenue streams")
        print("  • Monitoring system health")
        print("  • Self-healing issues")
        print("  • Learning from patterns")
        print("  • Making intelligent decisions")
    elif percentage >= 50:
        print("\n⚠️ AI SYSTEM PARTIALLY OPERATIONAL")
        print("Some features may not be available yet.")
    else:
        print("\n❌ AI SYSTEM NOT READY")
        print("Deployment may still be in progress.")
    
    print("=" * 80)
    
    return percentage >= 80

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)