#!/usr/bin/env python3
"""
Start All AI Orchestration Agents
This script launches the complete agent network for system self-awareness.
"""

import asyncio
import asyncpg
import logging
import sys
import os
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection - loaded from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

async def ensure_tables_exist():
    """Ensure all required tables exist"""
    logger.info("Verifying database tables...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Check if tables exist
        table_count = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                'agent_registry', 'agent_memory', 'agent_communications',
                'system_state', 'orchestration_workflows', 'workflow_executions',
                'agent_tasks', 'system_events', 'learning_episodes'
            )
        """)
        
        if table_count < 9:
            logger.error(f"Only {table_count}/9 orchestration tables exist!")
            logger.info("Run 'python initialize.py setup' first to create tables")
            return False
            
        logger.info(f"✅ All {table_count} orchestration tables verified")
        return True
        
    finally:
        await conn.close()

async def start_all_agents():
    """Start all AI agents"""
    logger.info("🚀 Starting AI Orchestration System...")
    
    # Verify tables exist
    if not await ensure_tables_exist():
        logger.error("Database tables not ready. Exiting.")
        return
    
    # Import agents
    from agents.system_architect import system_architect
    from agents.database_agent import database_agent
    from agents.myroofgenius_agent import myroofgenius_agent
    from agents.weathercraft_agent import weathercraft_agent
    
    # Create tasks for each agent
    tasks = []
    
    # Core agents
    logger.info("Starting SystemArchitect agent...")
    tasks.append(asyncio.create_task(system_architect.run()))
    
    logger.info("Starting DatabaseAgent...")
    tasks.append(asyncio.create_task(database_agent.run()))
    
    # Domain-specific agents
    logger.info("Starting MyRoofGeniusAgent...")
    tasks.append(asyncio.create_task(myroofgenius_agent.run()))
    
    logger.info("Starting WeatherCraftAgent...")
    tasks.append(asyncio.create_task(weathercraft_agent.run()))
    
    logger.info("✅ All 4 agents started successfully!")
    logger.info("=" * 60)
    logger.info("🧠 AI ORCHESTRATION SYSTEM ACTIVE")
    logger.info("Agents are now:")
    logger.info("  • Monitoring system health")
    logger.info("  • Managing database operations")
    logger.info("  • Optimizing revenue generation")
    logger.info("  • Managing CenterPoint data & operations")
    logger.info("  • Learning and adapting continuously")
    logger.info("=" * 60)
    
    # Wait for all agents (they run forever)
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Shutting down agents...")
        for task in tasks:
            task.cancel()
        logger.info("👋 All agents stopped")

async def check_agent_status():
    """Check the status of all agents"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Check agents
        agents = await conn.fetch("""
            SELECT 
                agent_name, 
                specialization,
                status, 
                last_active,
                EXTRACT(EPOCH FROM (NOW() - last_active)) as seconds_since_active
            FROM agent_registry 
            ORDER BY agent_name
        """)
        
        if agents:
            logger.info("\n📊 Agent Status Report:")
            logger.info("-" * 50)
            for agent in agents:
                status_emoji = {
                    'idle': '💤',
                    'thinking': '🤔',
                    'acting': '⚡',
                    'learning': '📚',
                    'communicating': '💬'
                }.get(agent['status'], '❓')
                
                seconds = agent['seconds_since_active'] or 999999
                if seconds < 60:
                    active_str = "Active now"
                elif seconds < 300:
                    active_str = f"Active {int(seconds/60)}m ago"
                else:
                    active_str = "Inactive"
                
                logger.info(f"{status_emoji} {agent['agent_name']:<20} | {agent['specialization']:<20} | {active_str}")
        else:
            logger.info("No agents registered yet")
        
        # Check memories
        memory_count = await conn.fetchval("SELECT COUNT(*) FROM agent_memory")
        recent_memories = await conn.fetchval("""
            SELECT COUNT(*) FROM agent_memory 
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)
        
        # Check communications
        comm_count = await conn.fetchval("SELECT COUNT(*) FROM agent_communications")
        recent_comms = await conn.fetchval("""
            SELECT COUNT(*) FROM agent_communications
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)
        
        logger.info("-" * 50)
        logger.info(f"🧠 Total Memories: {memory_count} ({recent_memories} in last hour)")
        logger.info(f"💬 Total Communications: {comm_count} ({recent_comms} in last hour)")
        logger.info("-" * 50)
        
    finally:
        await conn.close()

async def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        await check_agent_status()
    else:
        await start_all_agents()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Orchestration system shutdown complete")