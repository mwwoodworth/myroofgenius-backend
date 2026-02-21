#!/usr/bin/env python3
"""
Startup Test - Verify FastAPI app can start with integration layer
"""
import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all new modules can be imported"""
    logger.info("🔍 Testing module imports...")
    
    try:
        # Test service imports
        from services.mcp_service import mcp_service
        logger.info("✅ MCP Service imported successfully")
        
        from services.ai_agent_service import ai_agent_service
        logger.info("✅ AI Agent Service imported successfully")
        
        from services.monitoring_service import monitoring_service
        logger.info("✅ Monitoring Service imported successfully")
        
        from services.workflow_service import workflow_service
        logger.info("✅ Workflow Service imported successfully")
        
        # Test router import
        from routers.integration import router as integration_router
        logger.info("✅ Integration Router imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def test_app_creation():
    """Test that FastAPI app can be created"""
    logger.info("🚀 Testing FastAPI app creation...")
    
    try:
        # Import main app
        from main import app
        logger.info("✅ FastAPI app created successfully")
        
        # Check if integration routes are registered
        routes = [route.path for route in app.routes]
        integration_routes = [r for r in routes if '/integration/' in r]
        
        logger.info(f"📋 Found {len(integration_routes)} integration routes")
        for route in integration_routes[:5]:  # Show first 5
            logger.info(f"   - {route}")
        
        if len(integration_routes) > 5:
            logger.info(f"   ... and {len(integration_routes) - 5} more")
        
        return len(integration_routes) > 0
        
    except Exception as e:
        logger.error(f"❌ App creation failed: {e}")
        return False

def test_service_initialization():
    """Test that services can be initialized"""
    logger.info("⚙️ Testing service initialization...")
    
    try:
        from services.mcp_service import mcp_service
        from services.ai_agent_service import ai_agent_service
        from services.monitoring_service import monitoring_service
        from services.workflow_service import workflow_service
        
        # Test basic service methods
        mcp_status = mcp_service.get_server_status()
        logger.info(f"✅ MCP Service status: {len(mcp_status['servers'])} servers configured")
        
        agent_status = ai_agent_service.get_agent_status()
        logger.info(f"✅ AI Agent Service: {len(agent_status['agents'])} agents configured")
        
        templates = workflow_service.get_templates()
        logger.info(f"✅ Workflow Service: {len(templates)} templates available")
        
        logger.info("✅ Monitoring Service initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        return False

def main():
    """Run startup tests"""
    logger.info("🧪 STARTING INTEGRATION STARTUP TESTS")
    logger.info("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("FastAPI App Creation", test_app_creation),
        ("Service Initialization", test_service_initialization),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n🔍 Running: {test_name}")
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status}: {test_name}")
        except Exception as e:
            logger.error(f"💥 ERROR in {test_name}: {e}")
            results.append((test_name, "ERROR"))
    
    # Print summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 STARTUP TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = len([r for r in results if r[1] == "PASS"])
    total = len(results)
    
    logger.info(f"Total Tests: {total}")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {total - passed}")
    logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
    
    for test_name, status in results:
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "💥"
        logger.info(f"  {status_icon} {test_name}: {status}")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED! Integration layer is ready to use.")
    else:
        logger.info(f"\n⚠️ {total - passed} tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)