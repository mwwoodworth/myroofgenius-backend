#!/usr/bin/env python3
"""
CLAUDEOS SESSION INITIALIZER
Runs at the start of every session to ensure:
1. Memory context is loaded
2. Operational procedures are enforced
3. AI orchestration is connected
4. Learning systems are active
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
import aiohttp
import sys
import os

# Add backend path
sys.path.append('/home/mwwoodworth/code/fastapi-operator-env/apps/backend')

from PERSISTENT_MEMORY_OPERATIONAL_FRAMEWORK import PersistentMemoryFramework
from MEMORY_AI_ORCHESTRATION_INTEGRATION import MemoryAwareAIOrchestrator

# Configuration
BACKEND_URL = "https://brainops-backend-prod.onrender.com"
SUPABASE_URL = "https://yomagoqdmxszqtdwuhab.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTgzMzI3NiwiZXhwIjoyMDY1NDA5Mjc2fQ.7C3guJ_0moYGkdyeFmJ9cd2BmduB5NnU00erIIxH3gQ"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SessionInitializer")


class ClaudeOSSessionInitializer:
    """Initializes ClaudeOS with full memory context and procedures"""
    
    def __init__(self):
        self.session = None
        self.memory_framework = None
        self.ai_orchestrator = None
        self.session_context = {}
        self.procedures = {}
        self.active_monitors = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.initialize_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def initialize_session(self):
        """Initialize a new ClaudeOS session with full context"""
        
        logger.info("🎆 CLAUDEOS SESSION INITIALIZATION STARTING...")
        
        # Create session record
        session_id = f"session_{datetime.utcnow().timestamp()}"
        self.session_context['session_id'] = session_id
        self.session_context['started_at'] = datetime.utcnow().isoformat()
        
        # Initialize components in order
        await self.load_system_status()
        await self.load_operational_procedures()
        await self.load_recent_context()
        await self.initialize_memory_framework()
        await self.initialize_ai_orchestration()
        await self.establish_monitoring()
        await self.run_startup_checks()
        
        # Store session initialization
        await self.store_session_init()
        
        logger.info("✅ CLAUDEOS SESSION INITIALIZED SUCCESSFULLY!")
        await self.display_session_summary()
        
    async def load_system_status(self):
        """Load current system status from backend"""
        
        logger.info("📊 Loading system status...")
        
        try:
            # Check backend health
            async with self.session.get(f"{BACKEND_URL}/api/v1/health") as response:
                if response.status == 200:
                    health = await response.json()
                    self.session_context['backend_status'] = {
                        "status": "operational",
                        "version": health.get('version'),
                        "routes_loaded": health.get('routes_loaded', 0)
                    }
                else:
                    self.session_context['backend_status'] = {
                        "status": "error",
                        "error": await response.text()
                    }
                    
            # Check frontend status
            async with self.session.get("https://myroofgenius.com", allow_redirects=True) as response:
                self.session_context['frontend_status'] = {
                    "status": "operational" if response.status == 200 else "error",
                    "status_code": response.status
                }
                
        except Exception as e:
            logger.error(f"Error loading system status: {str(e)}")
            self.session_context['system_error'] = str(e)
            
    async def load_operational_procedures(self):
        """Load all operational procedures from memory"""
        
        logger.info("📋 Loading operational procedures...")
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Query for procedures
        params = {
            "memory_type": "eq.operational_procedure",
            "is_active": "eq.true",
            "select": "*",
            "order": "created_at.desc"
        }
        
        try:
            async with self.session.get(
                f"{SUPABASE_URL}/rest/v1/memory_entries",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    procedures = await response.json()
                    
                    for proc in procedures:
                        content = proc.get('content', {})
                        if isinstance(content, str):
                            try:
                                content = json.loads(content)
                            except:
                                continue
                                
                        if 'name' in content:
                            self.procedures[content['name']] = content
                            
                    logger.info(f"Loaded {len(self.procedures)} operational procedures")
                    
        except Exception as e:
            logger.error(f"Error loading procedures: {str(e)}")
            
    async def load_recent_context(self):
        """Load recent memory context"""
        
        logger.info("🧠 Loading recent memory context...")
        
        # Load recent deployments
        deployments = await self.query_memory("deployment_log", limit=5)
        self.session_context['recent_deployments'] = deployments
        
        # Load recent errors
        errors = await self.query_memory("error_pattern", limit=10)
        self.session_context['recent_errors'] = errors
        
        # Load recent learnings
        learnings = await self.query_memory("learning_insight", limit=10)
        self.session_context['recent_learnings'] = learnings
        
        # Load recent decisions
        decisions = await self.query_memory("decision_record", limit=5)
        self.session_context['recent_decisions'] = decisions
        
        logger.info(f"Loaded {sum(len(v) for v in self.session_context.values() if isinstance(v, list))} memory items")
        
    async def query_memory(self, memory_type: str, limit: int = 10) -> list:
        """Query memory entries by type"""
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        params = {
            "memory_type": f"eq.{memory_type}",
            "select": "title,content,tags,created_at,importance_score",
            "order": "created_at.desc",
            "limit": limit
        }
        
        try:
            async with self.session.get(
                f"{SUPABASE_URL}/rest/v1/memory_entries",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"Memory query error: {str(e)}")
            
        return []
        
    async def initialize_memory_framework(self):
        """Initialize the persistent memory framework"""
        
        logger.info("🌐 Initializing memory framework...")
        
        self.memory_framework = PersistentMemoryFramework()
        # Note: Framework initializes its own background tasks
        
        # Store framework reference in context
        self.session_context['memory_framework'] = "initialized"
        
    async def initialize_ai_orchestration(self):
        """Initialize AI orchestration with memory integration"""
        
        logger.info("🤖 Initializing AI orchestration...")
        
        self.ai_orchestrator = MemoryAwareAIOrchestrator()
        # Note: Orchestrator initializes its own background tasks
        
        # Store orchestrator reference in context
        self.session_context['ai_orchestration'] = "initialized"
        
    async def establish_monitoring(self):
        """Establish monitoring for procedures and compliance"""
        
        logger.info("👀 Establishing monitoring...")
        
        # Start procedure compliance monitor
        monitor_task = asyncio.create_task(self.procedure_compliance_monitor())
        self.active_monitors.append(monitor_task)
        
        # Start performance monitor
        perf_task = asyncio.create_task(self.performance_monitor())
        self.active_monitors.append(perf_task)
        
        # Start learning effectiveness monitor
        learning_task = asyncio.create_task(self.learning_effectiveness_monitor())
        self.active_monitors.append(learning_task)
        
        self.session_context['monitors_active'] = len(self.active_monitors)
        
    async def run_startup_checks(self):
        """Run startup checks to ensure everything is ready"""
        
        logger.info("🏁 Running startup checks...")
        
        checks = {
            "memory_framework": self.memory_framework is not None,
            "ai_orchestration": self.ai_orchestrator is not None,
            "procedures_loaded": len(self.procedures) > 0,
            "backend_operational": self.session_context.get('backend_status', {}).get('status') == 'operational',
            "monitors_active": len(self.active_monitors) > 0
        }
        
        self.session_context['startup_checks'] = checks
        all_passed = all(checks.values())
        
        if all_passed:
            logger.info("✅ All startup checks passed!")
        else:
            failed = [k for k, v in checks.items() if not v]
            logger.warning(f"⚠️  Failed checks: {failed}")
            
    async def store_session_init(self):
        """Store session initialization in memory"""
        
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        memory_entry = {
            "title": f"Session Initialized: {self.session_context['session_id']}",
            "content": json.dumps(self.session_context),
            "memory_type": "system_event",
            "tags": ["session", "initialization", "startup"],
            "meta_data": {
                "session_id": self.session_context['session_id'],
                "procedures_loaded": len(self.procedures),
                "monitors_active": len(self.active_monitors)
            },
            "importance_score": 0.8,
            "owner_id": "system",
            "owner_type": "system"
        }
        
        try:
            async with self.session.post(
                f"{SUPABASE_URL}/rest/v1/memory_entries",
                headers=headers,
                json=memory_entry
            ) as response:
                if response.status in [200, 201]:
                    logger.info("💾 Session initialization stored in memory")
                    
        except Exception as e:
            logger.error(f"Failed to store session init: {str(e)}")
            
    async def display_session_summary(self):
        """Display session initialization summary"""
        
        print("\n" + "="*80)
        print("🤖 CLAUDEOS SESSION INITIALIZED")
        print("="*80)
        
        print(f"\n🌐 SESSION CONTEXT:")
        print(f"  - Session ID: {self.session_context['session_id']}")
        print(f"  - Backend: {self.session_context.get('backend_status', {}).get('status', 'unknown')}")
        print(f"  - Frontend: {self.session_context.get('frontend_status', {}).get('status', 'unknown')}")
        
        print(f"\n📋 OPERATIONAL PROCEDURES:")
        for name in self.procedures:
            print(f"  - {name}")
            
        print(f"\n🧠 MEMORY CONTEXT:")
        print(f"  - Recent Deployments: {len(self.session_context.get('recent_deployments', []))}")
        print(f"  - Recent Errors: {len(self.session_context.get('recent_errors', []))}")
        print(f"  - Recent Learnings: {len(self.session_context.get('recent_learnings', []))}")
        print(f"  - Recent Decisions: {len(self.session_context.get('recent_decisions', []))}")
        
        print(f"\n👀 ACTIVE MONITORS: {len(self.active_monitors)}")
        
        print(f"\n🎆 READY FOR OPERATIONS!")
        print("="*80 + "\n")
        
    # Monitoring coroutines
    async def procedure_compliance_monitor(self):
        """Monitor compliance with operational procedures"""
        
        while True:
            try:
                # Check recent operations for procedure compliance
                recent_ops = await self.query_memory("deployment_log", limit=20)
                
                non_compliant = []
                for op in recent_ops:
                    content = op.get('content', {})
                    if isinstance(content, str):
                        try:
                            content = json.loads(content)
                        except:
                            continue
                            
                    if not content.get('followed_procedure', True):
                        non_compliant.append(op)
                        
                if non_compliant:
                    logger.warning(f"Found {len(non_compliant)} non-compliant operations")
                    # Store compliance issue
                    await self.store_compliance_issue(non_compliant)
                    
                await asyncio.sleep(180)  # 3 minutes
                
            except Exception as e:
                logger.error(f"Compliance monitor error: {str(e)}")
                await asyncio.sleep(60)
                
    async def performance_monitor(self):
        """Monitor system performance"""
        
        while True:
            try:
                # Check system health
                async with self.session.get(f"{BACKEND_URL}/api/v1/health") as response:
                    if response.status == 200:
                        health = await response.json()
                        
                        # Store performance metrics
                        await self.store_performance_metrics(health)
                        
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Performance monitor error: {str(e)}")
                await asyncio.sleep(60)
                
    async def learning_effectiveness_monitor(self):
        """Monitor learning effectiveness"""
        
        while True:
            try:
                # Analyze recent learnings
                learnings = await self.query_memory("learning_insight", limit=50)
                
                if learnings:
                    # Calculate learning metrics
                    metrics = self.calculate_learning_metrics(learnings)
                    
                    # Store learning effectiveness
                    await self.store_learning_effectiveness(metrics)
                    
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Learning monitor error: {str(e)}")
                await asyncio.sleep(300)
                
    # Helper methods
    async def store_compliance_issue(self, non_compliant: list):
        """Store compliance issue in memory"""
        # Implementation would store compliance issues
        pass
        
    async def store_performance_metrics(self, health: dict):
        """Store performance metrics in memory"""
        # Implementation would store performance data
        pass
        
    async def store_learning_effectiveness(self, metrics: dict):
        """Store learning effectiveness metrics"""
        # Implementation would store learning metrics
        pass
        
    def calculate_learning_metrics(self, learnings: list) -> dict:
        """Calculate metrics from recent learnings"""
        
        return {
            "total_learnings": len(learnings),
            "high_importance": len([l for l in learnings if l.get('importance_score', 0) > 0.8]),
            "patterns_identified": len(set(l.get('tags', [])[0] for l in learnings if l.get('tags'))),
            "time_range": "last_hour"
        }
        
    async def get_context_for_task(self, task: str) -> dict:
        """Get full context for a specific task"""
        
        context = {
            "task": task,
            "session_id": self.session_context['session_id'],
            "procedures": self.procedures,
            "recent_context": {
                "deployments": self.session_context.get('recent_deployments', [])[:3],
                "errors": self.session_context.get('recent_errors', [])[:3],
                "learnings": self.session_context.get('recent_learnings', [])[:3]
            },
            "system_status": {
                "backend": self.session_context.get('backend_status', {}),
                "frontend": self.session_context.get('frontend_status', {})
            }
        }
        
        # Get task-specific memory
        if self.memory_framework:
            task_memory = await self.memory_framework.get_contextual_guidance(task)
            context['task_guidance'] = task_memory
            
        return context


async def initialize_claudeos_session():
    """Main entry point for session initialization"""
    
    async with ClaudeOSSessionInitializer() as initializer:
        # Session is initialized in __aenter__
        
        # Return the initializer for use in the session
        return initializer


if __name__ == "__main__":
    # Run initialization
    asyncio.run(initialize_claudeos_session())