#!/usr/bin/env python3
"""
Debug Integration Issues
"""
import asyncio
import traceback

async def test_mcp_service():
    try:
        from services.mcp_service import mcp_service
        result = await mcp_service.check_all_servers()
        print("✅ MCP Service works:", result)
        return True
    except Exception as e:
        print("❌ MCP Service error:", e)
        traceback.print_exc()
        return False

async def test_ai_service():
    try:
        from services.ai_agent_service import ai_agent_service
        result = await ai_agent_service.check_all_agents()
        print("✅ AI Agent Service works:", result)
        return True
    except Exception as e:
        print("❌ AI Agent Service error:", e)
        traceback.print_exc()
        return False

async def test_monitoring_service():
    try:
        from services.monitoring_service import monitoring_service
        result = await monitoring_service.get_comprehensive_health_report()
        print("✅ Monitoring Service works:", len(str(result)) > 0)
        return True
    except Exception as e:
        print("❌ Monitoring Service error:", e)
        traceback.print_exc()
        return False

async def test_workflow_service():
    try:
        from services.workflow_service import workflow_service
        result = workflow_service.get_templates()
        print("✅ Workflow Service works:", len(result))
        return True
    except Exception as e:
        print("❌ Workflow Service error:", e)
        traceback.print_exc()
        return False

async def main():
    print("🧪 Debugging Integration Services")
    print("=" * 50)
    
    tests = [
        test_mcp_service,
        test_ai_service, 
        test_monitoring_service,
        test_workflow_service
    ]
    
    for test in tests:
        await test()
        print()

if __name__ == "__main__":
    asyncio.run(main())