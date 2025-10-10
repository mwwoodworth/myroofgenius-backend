#!/usr/bin/env python3
"""
Render API Keys Configuration Guide
Lists all required API keys and provides configuration instructions
"""
import json
from datetime import datetime

print("🔑 RENDER API KEYS CONFIGURATION")
print("=" * 70)
print(f"Timestamp: {datetime.now().isoformat()}")
print("=" * 70)

# Required API Keys
api_keys = {
    "CRITICAL": {
        "ANTHROPIC_API_KEY": {
            "description": "Claude AI integration (AUREA)",
            "required": True,
            "example": "sk-ant-api03-...",
            "features": ["AUREA Assistant", "AI Agents", "Claude Sub-agents"]
        },
        "OPENAI_API_KEY": {
            "description": "GPT-4 integration",
            "required": True,
            "example": "sk-...",
            "features": ["GPT-4 agents", "Embeddings", "Fallback AI"]
        },
        "GEMINI_API_KEY": {
            "description": "Google Gemini integration",
            "required": True,
            "example": "AIza...",
            "features": ["Gemini agents", "Multi-modal AI", "Fallback AI"]
        },
        "ELEVENLABS_API_KEY": {
            "description": "Voice synthesis for AUREA",
            "required": True,
            "example": "sk_...",
            "features": ["Voice responses", "Text-to-speech", "AUREA voice"]
        }
    },
    "PAYMENTS": {
        "STRIPE_SECRET_KEY": {
            "description": "Payment processing",
            "required": True,
            "example": "sk_live_...",
            "features": ["Subscriptions", "Payments", "Billing"]
        },
        "STRIPE_WEBHOOK_SECRET": {
            "description": "Stripe webhook verification",
            "required": True,
            "example": "whsec_...",
            "features": ["Payment webhooks", "Subscription updates"]
        }
    },
    "INTEGRATIONS": {
        "CLICKUP_API_KEY": {
            "description": "ClickUp project management",
            "required": False,
            "example": "pk_...",
            "features": ["Task sync", "Project management"]
        },
        "NOTION_API_KEY": {
            "description": "Notion workspace integration",
            "required": False,
            "example": "secret_...",
            "features": ["Documentation sync", "Knowledge base"]
        },
        "SLACK_TOKEN": {
            "description": "Slack notifications",
            "required": False,
            "example": "xoxb-...",
            "features": ["Notifications", "Team updates"]
        },
        "SENDGRID_API_KEY": {
            "description": "Email service",
            "required": False,
            "example": "SG...",
            "features": ["Email notifications", "Newsletters"]
        }
    },
    "MONITORING": {
        "SENTRY_DSN": {
            "description": "Error tracking",
            "required": False,
            "example": "https://...@sentry.io/...",
            "features": ["Error tracking", "Performance monitoring"]
        },
        "PAPERTRAIL_TOKEN": {
            "description": "Log aggregation",
            "required": False,
            "example": "...",
            "features": ["Centralized logging", "Log search"]
        }
    },
    "FEATURE_FLAGS": {
        "ENABLE_LLM_RESILIENCE": {
            "description": "Multi-LLM failover",
            "required": True,
            "example": "true",
            "features": ["AI failover", "Provider redundancy"]
        },
        "ENABLE_AGENT_EVOLUTION": {
            "description": "Self-improving agents",
            "required": True,
            "example": "true",
            "features": ["Agent evolution", "Performance optimization"]
        },
        "ENABLE_REAL_TIME_DOCS": {
            "description": "Live documentation updates",
            "required": True,
            "example": "true",
            "features": ["Auto documentation", "Real-time updates"]
        },
        "ENABLE_MONITORING": {
            "description": "System monitoring",
            "required": True,
            "example": "true",
            "features": ["Health checks", "Performance monitoring"]
        }
    }
}

print("\n📋 CONFIGURATION STEPS:")
print("\n1. LOGIN TO RENDER DASHBOARD:")
print("   - Go to https://dashboard.render.com")
print("   - Select 'brainops-backend' service")
print("   - Navigate to 'Environment' tab")

print("\n2. ADD CRITICAL API KEYS:")
for category, keys in api_keys.items():
    if category == "CRITICAL":
        print(f"\n   {category} (Required for basic functionality):")
        for key, config in keys.items():
            print(f"   - {key}")
            print(f"     Description: {config['description']}")
            print(f"     Example: {config['example']}")

print("\n3. ADD PAYMENT KEYS:")
for key, config in api_keys["PAYMENTS"].items():
    print(f"   - {key}")
    print(f"     Description: {config['description']}")
    print(f"     Example: {config['example']}")

print("\n4. OPTIONAL INTEGRATIONS:")
for key, config in api_keys["INTEGRATIONS"].items():
    print(f"   - {key} {'(Optional)' if not config['required'] else ''}")
    print(f"     Description: {config['description']}")

print("\n5. ENABLE FEATURE FLAGS:")
for key, config in api_keys["FEATURE_FLAGS"].items():
    print(f"   - {key} = {config['example']}")
    print(f"     Purpose: {config['description']}")

print("\n📊 IMPACT ANALYSIS:")
print("\nWithout API keys, these features will NOT work:")
missing_features = set()
for category, keys in api_keys.items():
    for key, config in keys.items():
        if config.get('required', False):
            missing_features.update(config['features'])

for feature in sorted(missing_features):
    print(f"   ❌ {feature}")

print("\n✅ VERIFICATION STEPS:")
print("1. After adding keys, trigger a manual deployment")
print("2. Check health endpoint: https://brainops-backend-prod.onrender.com/api/v1/health")
print("3. Test AI endpoints:")
print("   - POST /api/v1/ai/claude/chat")
print("   - POST /api/v1/ai/gemini/chat")
print("   - POST /api/v1/ai/openai/chat")
print("4. Test AUREA: GET /api/v1/aurea/status")

print("\n🔐 SECURITY NOTES:")
print("   - Never commit API keys to git")
print("   - Use Render's secret files for sensitive data")
print("   - Rotate keys regularly")
print("   - Monitor key usage in provider dashboards")

# Create environment template
env_template = []
for category, keys in api_keys.items():
    env_template.append(f"# {category}")
    for key, config in keys.items():
        if config.get('required', False) or category == "FEATURE_FLAGS":
            env_template.append(f"{key}={config['example']}")
    env_template.append("")

with open("/home/mwwoodworth/code/render_env_template.txt", "w") as f:
    f.write("\n".join(env_template))

# Create JSON configuration
config_json = {
    "service": "brainops-backend",
    "required_keys": [],
    "optional_keys": [],
    "feature_flags": []
}

for category, keys in api_keys.items():
    for key, config in keys.items():
        entry = {
            "key": key,
            "description": config['description'],
            "features": config['features']
        }
        if category == "FEATURE_FLAGS":
            config_json["feature_flags"].append(entry)
        elif config.get('required', False):
            config_json["required_keys"].append(entry)
        else:
            config_json["optional_keys"].append(entry)

with open("/home/mwwoodworth/code/render_api_keys.json", "w") as f:
    json.dump(config_json, f, indent=2)

print("\n📄 FILES CREATED:")
print("   - render_env_template.txt (copy-paste ready)")
print("   - render_api_keys.json (complete configuration)")

print("\n🚨 CURRENT STATUS:")
print("   - Backend is running but AI features are disabled")
print("   - Authentication works but some features are limited")
print("   - Public endpoints are fully functional")
print("   - AUREA and AI agents need API keys to function")

print("\n🎯 ACTION REQUIRED:")
print("   1. Add all CRITICAL API keys to Render")
print("   2. Add PAYMENT keys for billing features")
print("   3. Enable all FEATURE_FLAGS")
print("   4. Trigger manual deployment")
print("   5. Verify AI endpoints are working")