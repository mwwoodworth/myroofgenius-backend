import asyncpg
import asyncio
from config import get_database_url
from dotenv import load_dotenv
import os
import uuid

async def populate_tables():
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env.local')
    load_dotenv(dotenv_path=dotenv_path)
    db_url = get_database_url()
    conn = await asyncpg.connect(db_url)
    try:
        # Create the workflow
        workflow_id = await conn.fetchval("""
            INSERT INTO workflows (name, description)
            VALUES ('estimate_generation', 'Generates an estimate for a customer')
            ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
            RETURNING id
        """)

        # Create the workflow steps
        steps = [
            ('fetch_customer', 'Fetch customer data from the database', 1, '_fetch_customer'),
            ('analyze_property', 'Analyze property with AI', 2, '_analyze_property'),
            ('generate_pricing', 'Generate pricing for the estimate', 3, '_generate_pricing'),
            ('create_estimate', 'Create the estimate record in the database', 4, '_create_estimate')
        ]

        for name, description, step_order, function_name in steps:
            await conn.execute("""
                INSERT INTO workflow_steps (workflow_id, name, description, step_order, function_name)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (workflow_id, step_order) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    function_name = EXCLUDED.function_name
            """, workflow_id, name, description, step_order, function_name)

        print("Workflow 'estimate_generation' and its steps created successfully.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(populate_tables())
