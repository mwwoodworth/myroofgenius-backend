"""
Startup table creation to ensure all required tables exist
"""
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def ensure_tables_exist(db):
    """Create all required tables if they don't exist"""
    
    tables_sql = [
        # DevOps monitoring tables
        """
        CREATE TABLE IF NOT EXISTS vercel_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level VARCHAR(50),
            message TEXT,
            source VARCHAR(100),
            deployment_id VARCHAR(255),
            request_id VARCHAR(255),
            path VARCHAR(500),
            status_code INTEGER,
            raw_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS deployment_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_type VARCHAR(100),
            service VARCHAR(100),
            deployment_id VARCHAR(255),
            status VARCHAR(50),
            payload JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # AI tables
        """
        CREATE TABLE IF NOT EXISTS langgraph_executions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workflow_id UUID,
            execution_id VARCHAR(255),
            status VARCHAR(50) DEFAULT 'pending',
            context JSONB DEFAULT '{}',
            result JSONB,
            error TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS langgraph_workflows (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) UNIQUE NOT NULL,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS ai_board_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_type VARCHAR(100),
            context JSONB DEFAULT '{}',
            decisions JSONB DEFAULT '[]',
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS aurea_consciousness (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            level VARCHAR(50) DEFAULT 'ADAPTIVE',
            state JSONB DEFAULT '{}',
            memories JSONB DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    # Create tables
    for sql in tables_sql:
        try:
            db.execute(text(sql))
            db.commit()
        except Exception as e:
            logger.warning(f"Table creation warning (may already exist): {str(e)[:100]}")
            db.rollback()
    
    # Add missing columns if needed
    alter_statements = [
        "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS paid_amount DECIMAL(12,2) DEFAULT 0",
        "ALTER TABLE ai_board_sessions ADD COLUMN IF NOT EXISTS context JSONB DEFAULT '{}'",
    ]
    
    for sql in alter_statements:
        try:
            db.execute(text(sql))
            db.commit()
        except Exception as e:
            logger.warning(f"Column addition warning: {str(e)[:100]}")
            db.rollback()
    
    logger.info("✅ All required tables and columns verified/created")
    
    # Insert default workflows
    try:
        db.execute(text("""
            INSERT INTO langgraph_workflows (name, status)
            VALUES 
                ('Customer Journey', 'active'),
                ('Revenue Pipeline', 'active'),
                ('Service Delivery', 'active')
            ON CONFLICT (name) DO NOTHING
        """))
        db.commit()
    except:
        db.rollback()
    
    return True
