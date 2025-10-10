#!/usr/bin/env python3
"""
Configure Vercel Log Drain for MyRoofGenius
Vercel requires configuration through their dashboard or CLI
"""
import json
from datetime import datetime

print("📊 VERCEL LOG DRAIN CONFIGURATION GUIDE")
print("=" * 70)
print(f"Timestamp: {datetime.now().isoformat()}")
print("=" * 70)

# Log drain configuration
log_drain_config = {
    "service": "Papertrail",
    "host": "logs.papertrailapp.com",
    "port": 34302,
    "project": "MyRoofGenius",
    "environment": ["production", "preview"],
    "format": "json"
}

print("\n🔧 CONFIGURATION STEPS:")
print("\n1. USING VERCEL CLI:")
print("   ```bash")
print("   # Install Vercel CLI if not already installed")
print("   npm i -g vercel")
print("")
print("   # Login to Vercel")
print("   vercel login")
print("")
print("   # Link project")
print("   vercel link")
print("")
print("   # Add log drain")
print("   vercel log-drain add syslog://logs.papertrailapp.com:34302")
print("   ```")

print("\n2. USING VERCEL DASHBOARD:")
print("   - Go to https://vercel.com/dashboard")
print("   - Select 'MyRoofGenius' project")
print("   - Navigate to Settings → Log Drains")
print("   - Click 'Add Log Drain'")
print("   - Select 'Syslog' as the type")
print("   - Enter configuration:")
print(f"     - URL: syslog://{log_drain_config['host']}:{log_drain_config['port']}")
print("     - Environments: Production, Preview")
print("     - Format: JSON")

print("\n3. ENVIRONMENT VARIABLES (if using HTTP drain):")
env_vars = {
    "NEXT_PUBLIC_LOG_DRAIN_URL": f"https://{log_drain_config['host']}:{log_drain_config['port']}",
    "LOG_DRAIN_PROJECT": log_drain_config['project'],
    "LOG_DRAIN_ENABLED": "true"
}

print("\n   Add these to Vercel environment variables:")
for key, value in env_vars.items():
    print(f"   {key}={value}")

print("\n4. VERIFY CONFIGURATION:")
print("   ```bash")
print("   # List configured log drains")
print("   vercel log-drain ls")
print("")
print("   # Test log drain")
print("   vercel logs --follow")
print("   ```")

print("\n5. PAPERTRAIL CONFIGURATION:")
print("   - Login to Papertrail")
print("   - Create a new system for 'MyRoofGenius-Vercel'")
print("   - Note the provided syslog endpoint")
print("   - Add filters for:")
print("     - Error tracking: 'error OR failed OR exception'")
print("     - Performance: 'slow OR timeout OR performance'")
print("     - Security: 'auth OR unauthorized OR forbidden'")

print("\n📋 LOG DRAIN BENEFITS:")
print("   ✅ Centralized logging across backend and frontend")
print("   ✅ Real-time error monitoring")
print("   ✅ Performance tracking")
print("   ✅ Deployment logs")
print("   ✅ Function execution logs")
print("   ✅ Build logs")

print("\n🔍 MONITORING SETUP:")
print("   1. Create Papertrail alerts for:")
print("      - 5xx errors")
print("      - Build failures")
print("      - Function timeouts")
print("      - Memory limit exceeded")
print("")
print("   2. Configure alert destinations:")
print("      - Email: admin@myroofgenius.com")
print("      - Slack: #dev-alerts")
print("      - PagerDuty: critical-incidents")

print("\n📊 EXAMPLE LOG QUERIES:")
queries = [
    "program:vercel status:500",
    "program:vercel error -build",
    "program:vercel timeout",
    "program:vercel 'out of memory'",
    "program:vercel auth failed"
]

print("   Useful Papertrail search queries:")
for query in queries:
    print(f"   - {query}")

print("\n✅ EXPECTED OUTCOME:")
print("   - All Vercel logs streamed to Papertrail")
print("   - Unified logging with backend (Render)")
print("   - Real-time error detection")
print("   - Performance monitoring")
print("   - Deployment tracking")

print("\n📝 DOCUMENTATION:")
print("   - Vercel Log Drains: https://vercel.com/docs/observability/log-drains")
print("   - Papertrail Setup: https://www.papertrail.com/help/vercel/")
print("   - Troubleshooting: https://vercel.com/docs/cli/logs")

print("\n🚨 IMPORTANT NOTES:")
print("   1. Log drains are project-specific")
print("   2. They apply to all deployments (production + preview)")
print("   3. Logs are streamed in real-time")
print("   4. Historical logs are not sent to new drains")
print("   5. Multiple log drains can be configured")

# Create a JSON config file for reference
config_data = {
    "vercel_project": "myroofgenius-live",
    "log_drain": {
        "type": "syslog",
        "url": f"syslog://{log_drain_config['host']}:{log_drain_config['port']}",
        "environments": ["production", "preview"],
        "format": "json"
    },
    "papertrail": {
        "system_name": "MyRoofGenius-Vercel",
        "filters": [
            "error OR failed OR exception",
            "slow OR timeout OR performance",
            "auth OR unauthorized OR forbidden"
        ],
        "alerts": [
            {"name": "5xx Errors", "query": "status:5*"},
            {"name": "Build Failures", "query": "build failed"},
            {"name": "Timeouts", "query": "timeout OR 'timed out'"}
        ]
    }
}

with open("/home/mwwoodworth/code/vercel_log_drain_config.json", "w") as f:
    json.dump(config_data, f, indent=2)

print("\n✅ Configuration guide created!")
print("📄 JSON config saved to: vercel_log_drain_config.json")
print("\n🎯 ACTION REQUIRED:")
print("   1. Execute the Vercel CLI commands above")
print("   2. OR configure via Vercel dashboard")
print("   3. Verify in Papertrail that logs are arriving")