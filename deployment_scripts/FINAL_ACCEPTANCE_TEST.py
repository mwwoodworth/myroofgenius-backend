#!/usr/bin/env python3
"""
BrainOps Final Acceptance Tests
Comprehensive validation of all AI subsystems
"""

import requests
import json
import asyncio
from datetime import datetime, timezone
import sys

BASE_URL = "https://brainops-backend-prod.onrender.com"

def get_auth_token():
    """Get authentication token"""
    auth_data = {"email": "admin@brainops.com", "password": "AdminPassword123!"}
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json=auth_data)
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None

async def run_acceptance_tests():
    """Run all acceptance tests"""
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {}
    
    print("=" * 60)
    print("BRAINOPS AI SUBSYSTEMS - FINAL ACCEPTANCE TESTS")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    # 1. AI Board Tests
    print("\n1️⃣ AI BOARD TESTS")
    print("-" * 40)
    
    # Test status
    resp = requests.get(f"{BASE_URL}/api/v1/ai-board/status", headers=headers)
    print(f"GET /ai-board/status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Status: {data.get('status')}")
        print(f"  Agents: {data.get('agents')}")
        results["ai_board_status"] = "✅ PASS"
    else:
        results["ai_board_status"] = "❌ FAIL"
    
    # Test agents
    resp = requests.get(f"{BASE_URL}/api/v1/ai-board/agents", headers=headers)
    print(f"GET /ai-board/agents: {resp.status_code}")
    if resp.status_code == 200:
        agents = resp.json()
        print(f"  Agents found: {list(agents.keys()) if isinstance(agents, dict) else len(agents)}")
        results["ai_board_agents"] = "✅ PASS"
    else:
        results["ai_board_agents"] = "❌ FAIL"
    
    # Test metrics
    resp = requests.get(f"{BASE_URL}/api/v1/ai-board/metrics", headers=headers)
    print(f"GET /ai-board/metrics: {resp.status_code}")
    results["ai_board_metrics"] = "✅ PASS" if resp.status_code == 200 else "❌ FAIL"
    
    # Test task creation
    task_data = {"type": "smoke", "payload": {"ping": True}, "priority": "low"}
    resp = requests.post(f"{BASE_URL}/api/v1/ai-board/tasks", headers=headers, json=task_data)
    print(f"POST /ai-board/tasks: {resp.status_code}")
    if resp.status_code == 200:
        task_id = resp.json().get("task_id")
        print(f"  Task ID: {task_id}")
        results["ai_board_tasks_create"] = "✅ PASS"
    else:
        results["ai_board_tasks_create"] = "❌ FAIL"
    
    # Test task list
    resp = requests.get(f"{BASE_URL}/api/v1/ai-board/tasks", headers=headers)
    print(f"GET /ai-board/tasks: {resp.status_code}")
    results["ai_board_tasks_list"] = "✅ PASS" if resp.status_code == 200 else "❌ FAIL"
    
    # 2. Memory Tests
    print("\n2️⃣ MEMORY TESTS")
    print("-" * 40)
    
    # Test memory ready
    resp = requests.get(f"{BASE_URL}/api/v1/memory/ready", headers=headers)
    print(f"GET /memory/ready: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  DB Status: {data.get('db')}")
        print(f"  Latency: {data.get('latency_ms')}ms")
        results["memory_ready"] = "✅ PASS"
    else:
        results["memory_ready"] = "❌ FAIL"
    
    # Test memory write
    audit_key = f"audit-{datetime.now(timezone.utc).timestamp()}"
    value_data = json.dumps({"test": True, "timestamp": datetime.now(timezone.utc).isoformat()})
    write_params = {"key": audit_key, "value": value_data}
    resp = requests.post(f"{BASE_URL}/api/v1/memory/persistent/write", headers=headers, params=write_params)
    print(f"POST /memory/persistent/write: {resp.status_code}")
    results["memory_write"] = "✅ PASS" if resp.status_code == 200 else "❌ FAIL"
    
    # Test memory read
    resp = requests.get(f"{BASE_URL}/api/v1/memory/persistent/read", headers=headers, params={"key": audit_key})
    print(f"GET /memory/persistent/read: {resp.status_code}")
    results["memory_read"] = "✅ PASS" if resp.status_code == 200 else "❌ FAIL"
    
    # Test memory search
    resp = requests.get(f"{BASE_URL}/api/v1/ai-board/memory/search", headers=headers, params={"q": audit_key})
    print(f"GET /ai-board/memory/search: {resp.status_code}")
    results["memory_search"] = "✅ PASS" if resp.status_code == 200 else "❌ FAIL"
    
    # 3. AI Provider Tests
    print("\n3️⃣ AI PROVIDER TESTS")
    print("-" * 40)
    
    # Test provider status
    resp = requests.get(f"{BASE_URL}/api/v1/ai/keys/status", headers=headers)
    print(f"GET /ai/keys/status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        providers = data.get("providers", {})
        for provider, status in providers.items():
            verified = "✅" if status else "❌"
            print(f"  {provider}: {verified}")
        results["ai_providers"] = "✅ PASS"
    else:
        results["ai_providers"] = "❌ FAIL"
    
    # 4. Orchestration Tests
    print("\n4️⃣ ORCHESTRATION TESTS")
    print("-" * 40)
    
    # Test workflow list
    resp = requests.get(f"{BASE_URL}/api/v1/langgraphos/workflows", headers=headers)
    print(f"GET /langgraphos/workflows: {resp.status_code}")
    results["workflows_list"] = "✅ PASS" if resp.status_code == 200 else "❌ FAIL"
    
    # Test workflow execution
    workflow_data = {"test_mode": True}
    resp = requests.post(f"{BASE_URL}/api/v1/langgraphos/workflows/memory_sync/run", 
                         headers=headers, json=workflow_data)
    print(f"POST /langgraphos/workflows/memory_sync/run: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Status: {data.get('status')}")
        results["workflow_execution"] = "✅ PASS"
    else:
        results["workflow_execution"] = "❌ FAIL"
    
    # 5. AUREA Tests
    print("\n5️⃣ AUREA TESTS")
    print("-" * 40)
    
    # Test AUREA chat
    chat_data = {"message": "Store note TEST123 and confirm retrieval"}
    resp = requests.post(f"{BASE_URL}/api/v1/aurea/chat", headers=headers, json=chat_data)
    print(f"POST /aurea/chat: {resp.status_code}")
    if resp.status_code == 200:
        print(f"  Response received")
        results["aurea_chat"] = "✅ PASS"
    else:
        results["aurea_chat"] = "❌ FAIL"
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed = sum(1 for v in results.values() if "PASS" in v)
    failed = total_tests - passed
    
    for test, result in results.items():
        print(f"{result} {test}")
    
    print("-" * 60)
    print(f"Total: {total_tests} | Passed: {passed} | Failed: {failed}")
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 ALL TESTS PASSED - SYSTEM 100% OPERATIONAL")
        return True
    else:
        print(f"\n⚠️ SYSTEM {success_rate:.1f}% OPERATIONAL")
        return False

if __name__ == "__main__":
    result = asyncio.run(run_acceptance_tests())
    sys.exit(0 if result else 1)