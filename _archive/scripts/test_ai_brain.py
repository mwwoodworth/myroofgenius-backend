#!/usr/bin/env python3
"""
Test AI Brain Core functionality
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_brain_core import AIBrainCore

async def test_ai_brain():
    """Test the AI Brain Core"""
    print("🧠 Testing AI Brain Core...")
    print("=" * 60)
    
    # Initialize AI Brain
    brain = AIBrainCore()
    
    print("\n1️⃣ Initializing AI Brain...")
    await brain.initialize()
    print(f"   ✅ Loaded {len(brain.agents)} agents")
    print(f"   ✅ Established {len(brain.neural_pathways)} neural pathways")
    print(f"   ✅ Decision engine: {'Running' if brain.decision_engine_running else 'Stopped'}")
    
    # Test decision making
    print("\n2️⃣ Testing Decision Making...")
    context = {
        "situation": "Customer wants roof estimate",
        "urgency": "high",
        "customer_type": "residential"
    }
    options = [
        {"action": "send_ai_estimate", "priority": 1},
        {"action": "schedule_inspection", "priority": 2},
        {"action": "call_customer", "priority": 3}
    ]
    
    decision = await brain.make_decision(context, options, "high")
    print(f"   Decision: {decision}")
    print(f"   Confidence: {decision.get('confidence', 0) * 100:.1f}%")
    
    # Test task execution
    print("\n3️⃣ Testing Task Execution...")
    result = await brain.execute_task("generate_estimate", {
        "property_type": "residential",
        "roof_size": 2000,
        "material": "asphalt_shingle"
    })
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    # Test agent orchestration
    print("\n4️⃣ Testing Agent Orchestration...")
    agents_by_capability = {}
    for agent_id, agent in brain.agents.items():
        for cap in agent.get("capabilities", []):
            if cap not in agents_by_capability:
                agents_by_capability[cap] = []
            agents_by_capability[cap].append(agent["name"])
    
    print("   Capabilities discovered:")
    for cap, agents in list(agents_by_capability.items())[:10]:
        print(f"   - {cap}: {len(agents)} agents")
    
    # Test learning
    print("\n5️⃣ Testing Learning System...")
    experience = {
        "action": "ai_estimate",
        "context": {"customer_type": "commercial"},
        "result": {"revenue": 45000, "satisfaction": 95}
    }
    outcome = {"success": True, "revenue_impact": 45000}
    
    brain.memory["long_term"].append({
        "experience": experience,
        "outcome": outcome,
        "timestamp": datetime.now().isoformat()
    })
    
    if len(brain.memory["long_term"]) >= 10:
        await brain.extract_patterns()
    
    print(f"   Memory size: {len(brain.memory['long_term'])} experiences")
    print(f"   Patterns extracted: {len(brain.memory.get('patterns', []))}")
    print(f"   Learning rate: {brain.learning_rate:.3f}")
    
    # Test AUREA integration
    print("\n6️⃣ Testing AUREA Integration...")
    command = "generate estimate for 3000 sqft commercial building"
    result = await brain.aurea_execute(command, {"user": "test"})
    print(f"   Command: {command}")
    print(f"   Result: {result}")
    
    # Test neural pathway optimization
    print("\n7️⃣ Testing Neural Pathway Optimization...")
    before = len(brain.neural_pathways)
    await brain.optimize_pathways()
    after = len(brain.neural_pathways)
    print(f"   Pathways before: {before}")
    print(f"   Pathways after: {after}")
    print(f"   Optimization: {'+' if after > before else ''}{after - before} pathways")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ AI BRAIN TEST COMPLETE")
    print(f"   Agents: {len(brain.agents)}")
    print(f"   Neural Pathways: {len(brain.neural_pathways)}")
    print(f"   Decisions Made: {brain.decisions_made}")
    print(f"   Learning Rate: {brain.learning_rate:.3f}")
    print(f"   Status: {'OPERATIONAL' if brain.decision_engine_running else 'STOPPED'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_ai_brain())