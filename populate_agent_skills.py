import asyncpg
import asyncio
from config import get_database_url
from dotenv import load_dotenv
import os

async def populate_skills():
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
    load_dotenv(dotenv_path=dotenv_path)
    db_url = get_database_url()
    conn = await asyncpg.connect(db_url)
    try:
        agent_skills = {
            'EstimationAgent': ['estimation', 'pricing', 'costing'],
            'IntelligentScheduler': ['scheduling', 'calendar', 'time management'],
            'CustomerIntelligence': ['crm', 'customer analysis', 'lead scoring'],
            'InvoicingAgent': ['invoicing', 'billing', 'payments'],
            'WorkflowAutomation': ['workflow', 'automation', 'orchestration'],
            'RevenueOptimizer': ['revenue', 'analytics', 'forecasting'],
            'SystemMonitor': ['monitoring', 'health check', 'system status']
        }

        for agent_name, skills in agent_skills.items():
            await conn.execute("""
                UPDATE ai_agents
                SET skills = $1
                WHERE name = $2
            """, skills, agent_name)

        print("Successfully populated 'skills' for existing agents.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(populate_skills())
