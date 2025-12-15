#!/usr/bin/env python3
"""
Initialize the AI Orchestration System
This script sets up the database tables and starts the core agents.
"""

import asyncio
import asyncpg
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"

async def create_tables():
    """Create all orchestration tables"""
    logger.info("Creating orchestration tables...")
    
    # Read SQL file
    sql_file = Path(__file__).parent / "setup_tables.sql"
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    # Execute SQL
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Split and execute statements one by one
        statements = sql.split(';')
        for statement in statements:
            if statement.strip():
                try:
                    await conn.execute(statement)
                except Exception as e:
                    if "already exists" not in str(e):
                        logger.error(f"Error executing statement: {e}")
                        logger.error(f"Statement: {statement[:100]}...")
        
        logger.info("✅ Tables created successfully")
        
        # Verify tables
        table_count = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                'agent_registry', 'agent_memory', 'agent_communications',
                'system_state', 'orchestration_workflows', 'workflow_executions',
                'agent_tasks', 'system_events', 'learning_episodes'
            )
        """)
        
        logger.info(f"✅ Verified {table_count} orchestration tables exist")
        
    finally:
        await conn.close()

async def start_agents():
    """Start the core agents"""
    logger.info("Starting AI agents...")
    
    # Import agents
    from agents.system_architect import system_architect
    from agents.database_agent import database_agent
    
    # Create tasks for each agent
    tasks = []
    
    # Start SystemArchitect
    logger.info("Starting SystemArchitect agent...")
    tasks.append(asyncio.create_task(system_architect.run()))
    
    # Start DatabaseAgent
    logger.info("Starting DatabaseAgent...")
    tasks.append(asyncio.create_task(database_agent.run()))
    
    logger.info("✅ All agents started")
    
    # Wait for all agents (they run forever)
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Shutting down agents...")
        for task in tasks:
            task.cancel()

async def check_system_status():
    """Quick system status check"""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Check agents
        agents = await conn.fetch("""
            SELECT agent_name, status, last_active 
            FROM agent_registry 
            ORDER BY last_active DESC
        """)
        
        if agents:
            logger.info(f"\n📊 Active Agents:")
            for agent in agents:
                logger.info(f"  - {agent['agent_name']}: {agent['status']} (last active: {agent['last_active']})")
        else:
            logger.info("No agents registered yet")
        
        # Check system state
        states = await conn.fetch("""
            SELECT component, health_status, last_check
            FROM system_state
            ORDER BY last_check DESC
        """)
        
        if states:
            logger.info(f"\n📊 System Components:")
            for state in states:
                status_emoji = {
                    'healthy': '✅',
                    'warning': '⚠️',
                    'error': '❌',
                    'critical': '🔴'
                }.get(state['health_status'], '❓')
                logger.info(f"  {status_emoji} {state['component']}: {state['health_status']}")
        
        # Check recent memories
        memory_count = await conn.fetchval("""
            SELECT COUNT(*) FROM agent_memory
        """)
        logger.info(f"\n🧠 Total Memories: {memory_count}")
        
        # Check recent communications
        comm_count = await conn.fetchval("""
            SELECT COUNT(*) FROM agent_communications
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)
        logger.info(f"💬 Recent Communications (last hour): {comm_count}")
        
    finally:
        await conn.close()

async def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("🚀 AI ORCHESTRATION SYSTEM INITIALIZATION")
    logger.info("=" * 60)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            # Just create tables
            await create_tables()
            logger.info("✅ Setup complete. Run 'python initialize.py start' to start agents")
            
        elif command == "status":
            # Check status
            await check_system_status()
            
        elif command == "start":
            # Create tables and start agents
            await create_tables()
            await start_agents()
            
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Usage: python initialize.py [setup|status|start]")
    else:
        # Default: setup and start
        await create_tables()
        await start_agents()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Orchestration system shutdown complete")