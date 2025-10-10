#!/usr/bin/env python3
from context_bridge import bridge

# Load and display current context
context = bridge.get_context()
status = bridge.get_status()

print("🧠 CURRENT CONTEXT:")
print("-" * 50)
for key, data in context.items():
    print(f"{key}: {data.get('value')}")
print("-" * 50)
print(f"System Status: {status}")
