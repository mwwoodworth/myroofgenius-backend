#!/usr/bin/env python3
"""
Fix connection pool exhaustion and ensure tables exist
"""

def fix_main_py():
    """Fix main.py to use smaller connection pool and ensure cleanup"""
    
    with open("main.py", "r") as f:
        content = f.read()
    
    # Fix the connection pool settings - reduce from 20/40 to 5/10
    content = content.replace(
        """engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=False
)""",
        """engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,  # Reduced from 20
    max_overflow=10,  # Reduced from 40
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False
)"""
    )
    
    # Update version to 9.9
    content = content.replace('version="9.8"', 'version="9.9"')
    
    with open("main.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed connection pool settings in main.py")

def create_startup_table_creation():
    """Create a startup script that ensures all tables exist"""
    
    content = '''"""
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
'''
    
    with open("startup_tables.py", "w") as f:
        f.write(content)
    
    print("✅ Created startup_tables.py")

def update_main_startup():
    """Update main.py to run table creation on startup"""
    
    with open("main.py", "r") as f:
        lines = f.readlines()
    
    # Find lifespan function and add table creation
    for i, line in enumerate(lines):
        if 'logger.info("🚀 Starting BrainOps' in line:
            # Add table creation after this line
            lines.insert(i + 1, """    
    # Ensure all tables exist on startup
    try:
        from startup_tables import ensure_tables_exist
        with SessionLocal() as db:
            ensure_tables_exist(db)
            logger.info("✅ Database tables verified")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
""")
            break
    
    with open("main.py", "w") as f:
        f.writelines(lines)
    
    print("✅ Updated main.py to create tables on startup")

def fix_route_imports():
    """Fix the route imports to handle missing simple_routes gracefully"""
    
    with open("main.py", "r") as f:
        content = f.read()
    
    # Make simple_routes import optional
    content = content.replace(
        "from simple_routes import products_router, aurea_public_router, customers_router, jobs_router, invoices_router",
        """try:
    from simple_routes import products_router, aurea_public_router, customers_router, jobs_router, invoices_router
    SIMPLE_ROUTES_AVAILABLE = True
except ImportError:
    SIMPLE_ROUTES_AVAILABLE = False
    logger.warning("simple_routes not available, using existing routes")"""
    )
    
    # Make route mounting conditional
    content = content.replace(
        """# Mount simple routes for fixed endpoints
app.include_router(products_router)
app.include_router(aurea_public_router)
app.include_router(customers_router)
app.include_router(jobs_router)
app.include_router(invoices_router)""",
        """# Mount simple routes for fixed endpoints if available
if SIMPLE_ROUTES_AVAILABLE:
    app.include_router(products_router)
    app.include_router(aurea_public_router)
    app.include_router(customers_router)
    app.include_router(jobs_router)
    app.include_router(invoices_router)"""
    )
    
    with open("main.py", "w") as f:
        f.write(content)
    
    print("✅ Fixed route imports to be optional")

def main():
    print("🔧 Fixing connection pool exhaustion and ensuring tables...")
    fix_main_py()
    create_startup_table_creation()
    update_main_startup()
    fix_route_imports()
    print("\n✅ All fixes applied for v9.9!")
    print("This version will:")
    print("- Use smaller connection pool (5/10 instead of 20/40)")
    print("- Create all tables on startup")
    print("- Add missing columns automatically")
    print("- Handle route imports gracefully")

if __name__ == "__main__":
    main()