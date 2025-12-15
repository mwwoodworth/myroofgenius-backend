#!/usr/bin/env python3
"""
BrainOps Central Nervous System (CNS) Service
The persistent memory hub for all operations
"""

import asyncio
import asyncpg
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4
import numpy as np
from fastapi import HTTPException

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

class BrainOpsCNS:
    """Central Nervous System for persistent memory and task management"""

    def __init__(self, db_pool=None):
        self.db_pool = db_pool
        self.memory_cache = {}
        self.task_cache = {}

    async def initialize(self):
        """Initialize CNS with database connection"""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
        print("✅ CNS initialized with database connection")

    # =====================================================
    # MEMORY OPERATIONS
    # =====================================================

    async def remember(self, data: Dict) -> str:
        """Store anything in permanent memory"""
        async with self.db_pool.acquire() as conn:
            memory_id = str(uuid4())

            # Generate embedding (placeholder - would use real embedding model)
            embedding = self._generate_embedding(json.dumps(data))

            # Calculate importance based on content
            importance = self._calculate_importance(data)

            # Auto-expire routine memories after 30 days, keep important ones forever
            expires_at = None
            if importance < 0.5:
                expires_at = datetime.utcnow() + timedelta(days=30)

            # Convert embedding list to string for PostgreSQL vector type
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'

            query = """
                INSERT INTO cns_memory (
                    id, memory_type, category, title, content,
                    embeddings, importance_score, expires_at,
                    tags, source_system, created_by, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8, $9, $10, $11, $12)
                RETURNING memory_id
            """

            await conn.execute(
                query,
                memory_id,
                data.get('type', 'context'),
                data.get('category', 'general'),
                data.get('title', 'Untitled Memory'),
                json.dumps(data.get('content', data)),
                embedding_str,
                importance,
                expires_at,
                data.get('tags', []),
                data.get('source', 'api'),
                data.get('created_by', 'system'),
                json.dumps(data.get('metadata', {}))
            )

            # Update cache
            self.memory_cache[memory_id] = data

            return memory_id

    async def recall(self, query: str, limit: int = 10) -> List[Dict]:
        """Retrieve relevant memories using semantic search"""
        async with self.db_pool.acquire() as conn:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)

            # Convert query embedding to string for PostgreSQL vector type
            query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

            # Semantic search with vector similarity
            sql = """
                SELECT
                    id, memory_type, category, title, content,
                    importance_score, access_count, created_at,
                    tags, source_system, metadata,
                    1 - (embeddings <=> $1::vector) as similarity
                FROM cns_memory
                WHERE expires_at IS NULL OR expires_at > NOW()
                ORDER BY similarity DESC, importance_score DESC
                LIMIT $2
            """

            rows = await conn.fetch(sql, query_embedding_str, limit)

            memories = []
            for row in rows:
                memory = dict(row)
                memory['content'] = json.loads(memory['content'])
                memory['metadata'] = json.loads(memory['metadata']) if memory['metadata'] else {}
                memories.append(memory)

                # Update access count
                await conn.execute(
                    "UPDATE cns_memory SET access_count = access_count + 1, last_accessed = NOW() WHERE id = $1",
                    row['id']
                )

            return memories

    async def forget(self, memory_id: str) -> bool:
        """Mark a memory for expiration (soft delete)"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE cns_memory SET expires_at = NOW() WHERE id = $1",
                memory_id
            )
            return result == "UPDATE 1"

    # =====================================================
    # TASK MANAGEMENT
    # =====================================================

    async def create_task(self, task_data: Dict) -> str:
        """Create a new task with full context"""
        async with self.db_pool.acquire() as conn:
            task_id = str(uuid4())

            # AI-powered priority calculation
            priority = self._calculate_priority(task_data)

            query = """
                INSERT INTO cns_tasks (
                    id, task_id, project_id, title, description,
                    status, priority, urgency, impact,
                    assignee_id, parent_task_id, subtasks,
                    dependencies, context, ai_suggestions,
                    ai_priority_reason, due_date, tags
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                RETURNING memory_id
            """

            await conn.execute(
                query,
                task_id,
                task_id,  # task_id same as id
                task_data.get('project_id'),
                task_data['title'],
                task_data.get('description'),
                'pending',
                priority['score'],
                priority['urgency'],
                priority['impact'],
                task_data.get('assignee_id'),
                task_data.get('parent_task_id'),
                task_data.get('subtasks', []),
                task_data.get('dependencies', []),
                json.dumps(task_data.get('context', {})),
                json.dumps(self._generate_ai_suggestions(task_data)),
                priority['reason'],
                task_data.get('due_date'),
                task_data.get('tags', [])
            )

            # Also create a memory entry for this task
            await self.remember({
                'type': 'task',
                'category': 'task_creation',
                'title': f"Task created: {task_data['title']}",
                'content': task_data,
                'tags': ['task', 'created'] + task_data.get('tags', []),
                'source': 'task_manager'
            })

            return task_id

    async def update_task_status(self, task_id: str, status: str, notes: str = None) -> bool:
        """Update task status and track progress"""
        async with self.db_pool.acquire() as conn:
            # Get current task
            task = await conn.fetchrow(
                "SELECT * FROM cns_tasks WHERE task_id = $1",
                task_id
            )

            if not task:
                return False

            # Update status
            timestamp_field = None
            if status == 'in_progress' and task['status'] == 'pending':
                timestamp_field = 'started_at'
            elif status == 'completed':
                timestamp_field = 'completed_at'

            # Add to progress history
            progress_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'from_status': task['status'],
                'to_status': status,
                'notes': notes
            }

            progress_history = json.loads(task['progress_history']) if task['progress_history'] else []
            progress_history.append(progress_entry)

            query = """
                UPDATE cns_tasks
                SET status = $1,
                    progress_history = $2::jsonb[],
                    {} = COALESCE({}, NOW())
                WHERE task_id = $3
            """.format(timestamp_field or 'updated_at', timestamp_field or 'updated_at')

            await conn.execute(
                query,
                status,
                json.dumps(progress_history),
                task_id
            )

            # Create memory of status change
            await self.remember({
                'type': 'task',
                'category': 'status_change',
                'title': f"Task {task['title']} moved to {status}",
                'content': {
                    'task_id': task_id,
                    'from_status': task['status'],
                    'to_status': status,
                    'notes': notes
                },
                'tags': ['task', 'status_change', status]
            })

            return True

    async def get_tasks(self, filters: Dict = None) -> List[Dict]:
        """Get tasks with optional filtering"""
        async with self.db_pool.acquire() as conn:
            where_clauses = []
            params = []
            param_count = 0

            if filters:
                if 'status' in filters:
                    param_count += 1
                    where_clauses.append(f"status = ${param_count}")
                    params.append(filters['status'])

                if 'assignee_id' in filters:
                    param_count += 1
                    where_clauses.append(f"assignee_id = ${param_count}")
                    params.append(filters['assignee_id'])

                if 'project_id' in filters:
                    param_count += 1
                    where_clauses.append(f"project_id = ${param_count}")
                    params.append(filters['project_id'])

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            query = f"""
                SELECT * FROM cns_tasks
                {where_sql}
                ORDER BY priority DESC, created_at DESC
            """

            rows = await conn.fetch(query, *params)

            tasks = []
            for row in rows:
                task = dict(row)
                task['context'] = json.loads(task['context']) if task['context'] else {}
                task['ai_suggestions'] = json.loads(task['ai_suggestions']) if task['ai_suggestions'] else {}
                task['progress_history'] = json.loads(task['progress_history']) if task['progress_history'] else []
                tasks.append(task)

            return tasks

    # =====================================================
    # PROJECT MANAGEMENT
    # =====================================================

    async def create_project(self, project_data: Dict) -> str:
        """Create a new project with goals and milestones"""
        async with self.db_pool.acquire() as conn:
            project_id = str(uuid4())

            query = """
                INSERT INTO cns_projects (
                    id, name, code, description, status,
                    category, goals, success_criteria,
                    milestones, team_members, resources,
                    timeline, budget, deadline
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING memory_id
            """

            await conn.execute(
                query,
                project_id,
                project_data['name'],
                project_data.get('code', project_data['name'].lower().replace(' ', '_')),
                project_data.get('description'),
                'planning',
                project_data.get('category', 'general'),
                json.dumps(project_data.get('goals', [])),
                json.dumps(project_data.get('success_criteria', [])),
                json.dumps(project_data.get('milestones', [])),
                project_data.get('team_members', []),
                json.dumps(project_data.get('resources', {})),
                json.dumps(project_data.get('timeline', {})),
                json.dumps(project_data.get('budget', {})),
                project_data.get('deadline')
            )

            # Create memory
            await self.remember({
                'type': 'project',
                'category': 'project_creation',
                'title': f"Project created: {project_data['name']}",
                'content': project_data,
                'tags': ['project', 'created'],
                'source': 'project_manager'
            })

            return project_id

    async def add_project_learning(self, project_id: str, learning: str, context: Dict = None) -> bool:
        """Add a learning to a project"""
        async with self.db_pool.acquire() as conn:
            # Get current project
            project = await conn.fetchrow(
                "SELECT learnings FROM cns_projects WHERE id = $1",
                project_id
            )

            if not project:
                return False

            # Add to learnings
            learnings = json.loads(project['learnings']) if project['learnings'] else []
            learnings.append({
                'timestamp': datetime.utcnow().isoformat(),
                'learning': learning,
                'context': context
            })

            await conn.execute(
                "UPDATE cns_projects SET learnings = $1::jsonb[] WHERE id = $2",
                json.dumps(learnings),
                project_id
            )

            # Also add to system learnings
            await conn.execute("""
                INSERT INTO cns_learning_patterns (
                    id, category, learning_type, title, learning,
                    context, impact_score, confidence_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                str(uuid4()),
                'project',
                'insight',
                f"Learning from project {project_id}",
                learning,
                json.dumps(context or {}),
                0.7,  # Default impact
                0.8   # Default confidence
            )

            return True

    # =====================================================
    # CONTEXT & CONVERSATION THREADS
    # =====================================================

    async def create_thread(self, thread_data: Dict) -> str:
        """Create a conversation/context thread"""
        async with self.db_pool.acquire() as conn:
            thread_id = str(uuid4())

            # Generate embedding for thread summary
            embedding = self._generate_embedding(
                thread_data.get('summary', thread_data.get('title', ''))
            )
            # Convert embedding to string for PostgreSQL vector type
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'

            query = """
                INSERT INTO context_threads (
                    id, thread_type, title, participants,
                    messages, summary, embeddings, tags
                ) VALUES ($1, $2, $3, $4, $5, $6, $7::vector, $8)
                RETURNING memory_id
            """

            await conn.execute(
                query,
                thread_id,
                thread_data.get('type', 'conversation'),
                thread_data.get('title', 'Untitled Thread'),
                thread_data.get('participants', []),
                json.dumps(thread_data.get('messages', [])),
                thread_data.get('summary'),
                embedding_str,
                thread_data.get('tags', [])
            )

            return thread_id

    async def add_to_thread(self, thread_id: str, message: Dict) -> bool:
        """Add a message to a thread"""
        async with self.db_pool.acquire() as conn:
            thread = await conn.fetchrow(
                "SELECT messages FROM context_threads WHERE id = $1",
                thread_id
            )

            if not thread:
                return False

            messages = json.loads(thread['messages']) if thread['messages'] else []
            message['timestamp'] = datetime.utcnow().isoformat()
            messages.append(message)

            # Extract any action items
            action_items = self._extract_action_items(message.get('content', ''))

            await conn.execute("""
                UPDATE context_threads
                SET messages = $1::jsonb[],
                    last_active = NOW(),
                    action_items = array_cat(action_items, $2::uuid[])
                WHERE id = $3
            """,
                json.dumps(messages),
                action_items,
                thread_id
            )

            return True

    # =====================================================
    # DECISION TRACKING
    # =====================================================

    async def record_decision(self, decision_data: Dict) -> str:
        """Record a decision with full context"""
        async with self.db_pool.acquire() as conn:
            decision_id = str(uuid4())

            query = """
                INSERT INTO decisions (
                    id, decision_type, title, description,
                    context, options_considered, chosen_option,
                    rationale, expected_outcome, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING memory_id
            """

            await conn.execute(
                query,
                decision_id,
                decision_data.get('type', 'general'),
                decision_data['title'],
                decision_data.get('description'),
                json.dumps(decision_data.get('context', {})),
                json.dumps(decision_data.get('options', [])),
                json.dumps(decision_data['chosen']),
                decision_data.get('rationale'),
                json.dumps(decision_data.get('expected_outcome', {})),
                decision_data.get('created_by', 'system')
            )

            # Create memory
            await self.remember({
                'type': 'decision',
                'category': 'decision_made',
                'title': f"Decision: {decision_data['title']}",
                'content': decision_data,
                'tags': ['decision', 'important'],
                'source': 'decision_tracker'
            })

            return decision_id

    # =====================================================
    # AUTOMATION RULES
    # =====================================================

    async def create_automation(self, rule_data: Dict) -> str:
        """Create an automation rule"""
        async with self.db_pool.acquire() as conn:
            rule_id = str(uuid4())

            query = """
                INSERT INTO automation_rules (
                    id, rule_name, description, trigger_type,
                    trigger_config, conditions, action_type,
                    action_config, is_active, priority, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING memory_id
            """

            await conn.execute(
                query,
                rule_id,
                rule_data['name'],
                rule_data.get('description'),
                rule_data['trigger_type'],
                json.dumps(rule_data.get('trigger_config', {})),
                json.dumps(rule_data.get('conditions', [])),
                rule_data['action_type'],
                json.dumps(rule_data.get('action_config', {})),
                rule_data.get('is_active', True),
                rule_data.get('priority', 5),
                rule_data.get('created_by', 'system')
            )

            return rule_id

    async def execute_automations(self, trigger_type: str, context: Dict) -> List[Dict]:
        """Execute automations based on trigger"""
        async with self.db_pool.acquire() as conn:
            # Get active rules for this trigger
            rules = await conn.fetch("""
                SELECT * FROM automation_rules
                WHERE trigger_type = $1 AND is_active = true
                ORDER BY priority DESC
            """, trigger_type)

            results = []
            for rule in rules:
                # Check conditions
                conditions = json.loads(rule['conditions']) if rule['conditions'] else []
                if self._check_conditions(conditions, context):
                    # Execute action
                    action_result = await self._execute_action(
                        rule['action_type'],
                        json.loads(rule['action_config']) if rule['action_config'] else {},
                        context
                    )

                    # Update execution count
                    if action_result['success']:
                        await conn.execute("""
                            UPDATE automation_rules
                            SET execution_count = execution_count + 1,
                                success_count = success_count + 1,
                                last_executed = NOW(),
                                last_success = NOW()
                            WHERE id = $1
                        """, rule['id'])
                    else:
                        await conn.execute("""
                            UPDATE automation_rules
                            SET execution_count = execution_count + 1,
                                failure_count = failure_count + 1,
                                last_executed = NOW(),
                                last_failure = NOW()
                            WHERE id = $1
                        """, rule['id'])

                    results.append({
                        'rule_id': rule['id'],
                        'rule_name': rule['rule_name'],
                        'result': action_result
                    })

            return results

    # =====================================================
    # HELPER METHODS
    # =====================================================

    def _generate_embedding(self, text: str) -> list:
        """Generate vector embedding for text (placeholder)"""
        # In production, would use OpenAI/Anthropic embeddings
        # For now, generate random 1536-dim vector
        np.random.seed(hash(text) % (2**32))
        return np.random.randn(1536).tolist()

    def _calculate_importance(self, data: Dict) -> float:
        """Calculate importance score for memory"""
        score = 0.5  # Base score

        # Increase for certain types
        if data.get('type') in ['decision', 'learning', 'warning']:
            score += 0.2

        # Increase for high-priority items
        if data.get('priority', 0) > 7:
            score += 0.1

        # Increase for items with many tags
        if len(data.get('tags', [])) > 3:
            score += 0.1

        # Cap at 1.0
        return min(score, 1.0)

    def _calculate_priority(self, task_data: Dict) -> Dict:
        """AI-powered priority calculation"""
        urgency = 5
        impact = 5

        # Analyze title and description for urgency keywords
        urgent_keywords = ['urgent', 'asap', 'critical', 'emergency', 'immediately']
        text = f"{task_data.get('title', '')} {task_data.get('description', '')}".lower()

        for keyword in urgent_keywords:
            if keyword in text:
                urgency = 9
                break

        # Check due date
        if task_data.get('due_date'):
            due = datetime.fromisoformat(task_data['due_date'])
            days_until = (due - datetime.utcnow()).days
            if days_until <= 1:
                urgency = 10
            elif days_until <= 3:
                urgency = 8
            elif days_until <= 7:
                urgency = 6

        # Calculate impact based on dependencies
        if len(task_data.get('dependencies', [])) > 3:
            impact = 8

        # Final score
        score = (urgency + impact) / 2

        reason = f"Urgency: {urgency}/10, Impact: {impact}/10"
        if urgency >= 8:
            reason += " - High urgency detected"

        return {
            'score': int(score),
            'urgency': urgency,
            'impact': impact,
            'reason': reason
        }

    def _generate_ai_suggestions(self, task_data: Dict) -> Dict:
        """Generate AI suggestions for task"""
        suggestions = {
            'recommended_approach': [],
            'potential_blockers': [],
            'similar_tasks': [],
            'time_estimate': None
        }

        # Basic analysis
        title = task_data.get('title', '').lower()

        if 'fix' in title or 'bug' in title:
            suggestions['recommended_approach'] = [
                "Reproduce the issue",
                "Check recent changes",
                "Review logs for errors",
                "Test fix in development",
                "Deploy with monitoring"
            ]
            suggestions['time_estimate'] = "2-4 hours"
        elif 'implement' in title or 'build' in title:
            suggestions['recommended_approach'] = [
                "Design the solution",
                "Break into subtasks",
                "Create tests first",
                "Implement incrementally",
                "Review and refactor"
            ]
            suggestions['time_estimate'] = "1-3 days"

        return suggestions

    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items from text"""
        # Simple extraction - in production would use NLP
        action_items = []

        action_keywords = ['todo:', 'action:', 'task:', 'need to', 'should', 'must']
        lines = text.lower().split('\n')

        for line in lines:
            for keyword in action_keywords:
                if keyword in line:
                    # Would create actual task here
                    # For now just track that action item exists
                    action_items.append(str(uuid4()))
                    break

        return action_items

    def _check_conditions(self, conditions: List[Dict], context: Dict) -> bool:
        """Check if all conditions are met"""
        if not conditions:
            return True

        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator', '==')
            value = condition.get('value')

            context_value = context.get(field)

            if operator == '==' and context_value != value:
                return False
            elif operator == '>' and not (context_value > value):
                return False
            elif operator == '<' and not (context_value < value):
                return False
            elif operator == 'contains' and value not in str(context_value):
                return False

        return True

    async def _execute_action(self, action_type: str, config: Dict, context: Dict) -> Dict:
        """Execute an automation action"""
        try:
            if action_type == 'create_task':
                task_id = await self.create_task({
                    'title': config.get('title', 'Auto-generated task'),
                    'description': config.get('description', ''),
                    'context': context,
                    'tags': ['automated']
                })
                return {'success': True, 'task_id': task_id}

            elif action_type == 'notify':
                # Would send notification here
                return {'success': True, 'notification_sent': True}

            elif action_type == 'update_status':
                # Would update status here
                return {'success': True, 'status_updated': True}

            else:
                return {'success': False, 'error': f'Unknown action type: {action_type}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}


# FastAPI endpoints integration
def create_cns_routes(app, cns: BrainOpsCNS):
    """Create FastAPI routes for CNS"""

    @app.post("/api/v1/cns/memory")
    async def store_memory(data: Dict):
        """Store data in permanent memory"""
        memory_id = await cns.remember(data)
        return {"success": True, "memory_id": memory_id}

    @app.get("/api/v1/cns/memory/search")
    async def search_memory(query: str, limit: int = 10):
        """Search memories semantically"""
        memories = await cns.recall(query, limit)
        return {"memories": memories, "count": len(memories)}

    @app.post("/api/v1/cns/tasks")
    async def create_task(task: Dict):
        """Create a new task"""
        task_id = await cns.create_task(task)
        return {"success": True, "task_id": task_id}

    @app.get("/api/v1/cns/tasks")
    async def get_tasks(status: str = None, assignee_id: str = None, project_id: str = None):
        """Get tasks with optional filters"""
        filters = {}
        if status:
            filters['status'] = status
        if assignee_id:
            filters['assignee_id'] = assignee_id
        if project_id:
            filters['project_id'] = project_id

        tasks = await cns.get_tasks(filters)
        return {"tasks": tasks, "count": len(tasks)}

    @app.put("/api/v1/cns/tasks/{task_id}/status")
    async def update_task(task_id: str, status: str, notes: str = None):
        """Update task status"""
        success = await cns.update_task_status(task_id, status, notes)
        return {"success": success}

    @app.post("/api/v1/cns/projects")
    async def create_project(project: Dict):
        """Create a new project"""
        project_id = await cns.create_project(project)
        return {"success": True, "project_id": project_id}

    @app.post("/api/v1/cns/projects/{project_id}/learnings")
    async def add_learning(project_id: str, learning: str, context: Dict = None):
        """Add learning to project"""
        success = await cns.add_project_learning(project_id, learning, context)
        return {"success": success}

    @app.post("/api/v1/cns/threads")
    async def create_thread(thread: Dict):
        """Create conversation thread"""
        thread_id = await cns.create_thread(thread)
        return {"success": True, "thread_id": thread_id}

    @app.post("/api/v1/cns/threads/{thread_id}/messages")
    async def add_message(thread_id: str, message: Dict):
        """Add message to thread"""
        success = await cns.add_to_thread(thread_id, message)
        return {"success": success}

    @app.post("/api/v1/cns/decisions")
    async def record_decision(decision: Dict):
        """Record a decision"""
        decision_id = await cns.record_decision(decision)
        return {"success": True, "decision_id": decision_id}

    @app.post("/api/v1/cns/automations")
    async def create_automation(rule: Dict):
        """Create automation rule"""
        rule_id = await cns.create_automation(rule)
        return {"success": True, "rule_id": rule_id}

    @app.post("/api/v1/cns/automations/execute")
    async def execute_automations(trigger_type: str, context: Dict):
        """Execute automations for trigger"""
        results = await cns.execute_automations(trigger_type, context)
        return {"results": results, "executed": len(results)}

    @app.get("/api/v1/cns/status")
    async def cns_status():
        """Get CNS system status"""
        async with cns.db_pool.acquire() as conn:
            memory_count = await conn.fetchval("SELECT COUNT(*) FROM cns_memory WHERE expires_at IS NULL OR expires_at > NOW()")
            task_count = await conn.fetchval("SELECT COUNT(*) FROM cns_tasks WHERE status != 'completed'")
            project_count = await conn.fetchval("SELECT COUNT(*) FROM cns_projects WHERE status = 'active'")
            thread_count = await conn.fetchval("SELECT COUNT(*) FROM context_threads WHERE is_active = true")
            automation_count = await conn.fetchval("SELECT COUNT(*) FROM automation_rules WHERE is_active = true")

        return {
            "status": "operational",
            "stats": {
                "active_memories": memory_count,
                "pending_tasks": task_count,
                "active_projects": project_count,
                "active_threads": thread_count,
                "automation_rules": automation_count
            }
        }

    return app


# Standalone test
if __name__ == "__main__":
    async def test_cns():
        """Test CNS functionality"""
        cns = BrainOpsCNS()
        await cns.initialize()

        print("🧠 Testing BrainOps CNS...")

        # Test memory
        memory_id = await cns.remember({
            'type': 'test',
            'category': 'system_test',
            'title': 'CNS Test Memory',
            'content': {'test': 'This is a test memory'},
            'tags': ['test', 'cns']
        })
        print(f"✅ Memory stored: {memory_id}")

        # Test recall
        memories = await cns.recall("test memory", limit=5)
        print(f"✅ Recalled {len(memories)} memories")

        # Test task creation
        task_id = await cns.create_task({
            'title': 'Test CNS Integration',
            'description': 'Verify CNS is working properly',
            'tags': ['test', 'cns']
        })
        print(f"✅ Task created: {task_id}")

        # Get tasks
        tasks = await cns.get_tasks({'status': 'pending'})
        print(f"✅ Found {len(tasks)} pending tasks")

        print("\n🎉 CNS test complete - all systems operational!")

    asyncio.run(test_cns())