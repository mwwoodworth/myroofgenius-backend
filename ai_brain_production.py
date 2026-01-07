#!/usr/bin/env python3
"""
AI Brain Production Core - Full 34 Agent System with 1122 Neural Pathways
This is the REAL production system that orchestrates everything
"""

import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from core.agent_execution_manager import AgentExecutionManager

class AIBrainProduction:
    """Production AI Brain orchestrating 34 agents with full neural network"""

    def __init__(self):
        self.conn_str = os.getenv("DATABASE_URL")
        if not self.conn_str:
            raise RuntimeError("DATABASE_URL environment variable is required")
        self.agents = {}
        self.neural_pathways = {}
        self.active_tasks = {}
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        
        # Performance tracking
        self.decisions_made = 0
        self.tasks_executed = 0
        self.learning_rate = 0.5
        self.success_rate = 100.0
        self.decision_engine_running = False
        
        # Memory systems
        self.short_term_memory = []  # Last 100 operations
        self.long_term_memory = []   # Patterns and learnings
        self.working_memory = {}      # Current context
        
        # Thread pool for parallel agent execution
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.agent_executor = AgentExecutionManager()
        
    def connect_db(self):
        """Get database connection"""
        return psycopg2.connect(self.conn_str)
    
    async def initialize(self):
        """Initialize the complete AI Brain system"""
        logger.info("🧠 Initializing Production AI Brain...")
        
        # Load all 34 agents
        await self.load_all_agents()
        
        # Load all 1122 neural pathways
        await self.load_neural_pathways()
        
        # Start decision engine
        await self.start_decision_engine()
        
        # Initialize AUREA as master
        await self.initialize_aurea()
        
        # Start background processes
        asyncio.create_task(self.neural_pulse())  # Continuous neural activity
        asyncio.create_task(self.memory_consolidation())  # Memory management
        asyncio.create_task(self.performance_monitor())  # System monitoring
        
        logger.info(f"✅ AI Brain initialized: {len(self.agents)} agents, {len(self.neural_pathways)} pathways")
        return True
    
    async def load_all_agents(self):
        """Load all 34 agents from database"""
        conn = self.connect_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT id, name, type, model, status, capabilities, config, metadata,
                       total_executions as tasks_completed, success_rate
                FROM ai_agents
                WHERE status = 'active'
                ORDER BY
                    CASE type
                        WHEN 'orchestrator' THEN 1
                        WHEN 'guardian' THEN 2
                        WHEN 'executor' THEN 3
                        WHEN 'analyzer' THEN 4
                        WHEN 'specialist' THEN 5
                        ELSE 6
                    END
            """)
            
            agents = cur.fetchall()
            
            for agent in agents:
                self.agents[agent['id']] = {
                    'name': agent['name'],
                    'type': agent['type'],
                    'model': agent['model'],
                    'status': 'ready',
                    'capabilities': agent['capabilities'] or [],
                    'config': agent['config'] or {},
                    'metadata': agent['metadata'] or {},
                    'tasks_completed': agent['tasks_completed'] or 0,
                    'success_rate': float(agent['success_rate'] or 100),
                    'current_task': None,
                    'last_active': datetime.now()
                }
            
            logger.info(f"📊 Loaded {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Error loading agents: {e}")
        finally:
            conn.close()
    
    async def load_neural_pathways(self):
        """Load all neural pathways connecting agents"""
        conn = self.connect_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT 
                    p.id,
                    p.source_agent_id,
                    p.target_agent_id,
                    p.pathway_type,
                    p.strength,
                    p.activation_threshold,
                    p.usage_count,
                    s.name as source_name,
                    t.name as target_name
                FROM ai_neural_pathways_v2 p
                JOIN ai_agents s ON p.source_agent_id = s.id
                JOIN ai_agents t ON p.target_agent_id = t.id
                WHERE p.strength > 0
            """)
            
            pathways = cur.fetchall()
            
            for pathway in pathways:
                key = f"{pathway['source_agent_id']}->{pathway['target_agent_id']}"
                self.neural_pathways[key] = {
                    'id': pathway['id'],
                    'source': pathway['source_agent_id'],
                    'target': pathway['target_agent_id'],
                    'source_name': pathway['source_name'],
                    'target_name': pathway['target_name'],
                    'type': pathway['pathway_type'],
                    'strength': pathway['strength'],
                    'threshold': float(pathway['activation_threshold'] or 0.5),
                    'usage_count': pathway['usage_count'] or 0,
                    'last_activated': None
                }
            
            logger.info(f"🧬 Loaded {len(self.neural_pathways)} neural pathways")
            
        except Exception as e:
            logger.error(f"Error loading pathways: {e}")
        finally:
            conn.close()
    
    async def start_decision_engine(self):
        """Start the central decision-making engine"""
        self.decision_engine_running = True
        logger.info("⚡ Decision engine started")
        
        # Log session start
        conn = self.connect_db()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO ai_board_sessions 
                (session_type, board_members, agenda, status, context, metadata, started_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (
                'autonomous_operations',
                [],  # Will be populated with active agents
                ['system_optimization', 'task_execution', 'learning'],
                'active',
                json.dumps({'mode': 'production', 'brain_version': '3.0'}),
                json.dumps({'session_id': self.session_id})
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Session logging error: {e}")
        finally:
            conn.close()
    
    async def initialize_aurea(self):
        """Initialize AUREA as the master controller"""
        aurea_id = None
        for agent_id, agent in self.agents.items():
            if agent['name'] == 'AUREA':
                aurea_id = agent_id
                break
        
        if aurea_id:
            self.agents[aurea_id]['status'] = 'master_controller'
            self.agents[aurea_id]['metadata']['authority'] = 'maximum'
            logger.info("👑 AUREA initialized as master controller")
    
    async def make_decision(self, context: Dict, options: List, urgency: str = "normal"):
        """Make a decision using multi-agent consensus"""
        start_time = time.time()
        self.decisions_made += 1
        
        # Select consulting agents based on context
        consulting_agents = await self.select_consulting_agents(context, urgency)
        
        # Gather opinions from each agent
        opinions = await self.gather_agent_opinions(consulting_agents, context, options)
        
        # Build consensus
        decision = await self.build_consensus(opinions, urgency)
        
        # Log decision
        await self.log_decision(context, options, decision, consulting_agents)
        
        # Update metrics
        decision_time = (time.time() - start_time) * 1000
        self.working_memory['last_decision_time'] = decision_time
        
        return decision
    
    async def select_consulting_agents(self, context: Dict, urgency: str) -> List[str]:
        """Select which agents to consult based on context"""
        consulting = []
        
        # Always include orchestrators
        for agent_id, agent in self.agents.items():
            if agent['type'] == 'orchestrator':
                consulting.append(agent_id)
        
        # Add specialists based on context
        if 'revenue' in str(context).lower():
            for agent_id, agent in self.agents.items():
                if 'RevenueAgent' in agent['name'] or 'SalesAgent' in agent['name']:
                    consulting.append(agent_id)
        
        if 'customer' in str(context).lower():
            for agent_id, agent in self.agents.items():
                if 'CustomerAgent' in agent['name']:
                    consulting.append(agent_id)
        
        if urgency in ['critical', 'high']:
            # Add guardians for critical decisions
            for agent_id, agent in self.agents.items():
                if agent['type'] == 'guardian':
                    consulting.append(agent_id)
                    break
        
        return list(set(consulting))[:5]  # Limit to 5 agents for speed
    
    async def gather_agent_opinions(self, agent_ids: List[str], context: Dict, options: List) -> List[Dict]:
        """Gather opinions from multiple agents"""
        opinions: List[Dict] = []
        tasks = []

        for agent_id in agent_ids:
            if agent_id in self.agents:
                tasks.append(self._fetch_agent_opinion(agent_id, context, options))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Agent opinion error: {result}")
                continue
            if result:
                opinions.append(result)

        return opinions

    async def _fetch_agent_opinion(self, agent_id: str, context: Dict, options: List) -> Dict:
        """Ask a specific agent for a decision opinion."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise RuntimeError(f"Agent {agent_id} not found")

        task_prompt = (
            "Review the decision context and options. "
            "Return JSON with keys: preferred_option, confidence, reasoning."
        )
        execution = await self.agent_executor.execute_agent(
            agent['name'],
            task_prompt,
            {
                "context": context,
                "options": options,
                "agent_role": agent.get("type"),
                "agent_capabilities": agent.get("capabilities", [])
            },
            retry_on_failure=False
        )

        output = execution.get("result") if execution else {}
        return await self._normalize_opinion(agent, output, context, options)

    async def _normalize_opinion(self, agent: Dict, output: Any, context: Dict, options: List) -> Dict:
        """Normalize agent output into a structured opinion."""
        preferred = None
        confidence = None
        reasoning = None

        if isinstance(output, dict):
            preferred = output.get("preferred_option") or output.get("decision") or output.get("chosen")
            confidence = output.get("confidence") or output.get("probability")
            reasoning = output.get("reasoning") or output.get("analysis") or output.get("summary")
        else:
            reasoning = str(output)

        if preferred is None or confidence is None:
            return await self._derive_opinion_with_ai(agent['name'], context, options, output)

        try:
            confidence_val = float(confidence)
            if confidence_val > 1:
                confidence_val = confidence_val / 100.0
        except (TypeError, ValueError):
            return await self._derive_opinion_with_ai(agent['name'], context, options, output)

        return {
            "agent_id": agent.get("id"),
            "agent_name": agent.get("name"),
            "preferred_option": self._match_option(preferred, options),
            "confidence": max(0.0, min(confidence_val, 1.0)),
            "reasoning": reasoning or "No reasoning provided"
        }

    async def _derive_opinion_with_ai(self, agent_name: str, context: Dict, options: List, output: Any) -> Dict:
        """Use real AI to derive a structured opinion when agent output is incomplete."""
        from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError, AIProviderCallError

        prompt = (
            f"You are {agent_name}. Analyze the decision context and pick the best option.\n\n"
            f"Context:\n{json.dumps(context, default=str)}\n\n"
            f"Options:\n{json.dumps(options, default=str)}\n\n"
            f"Raw agent output:\n{json.dumps(output, default=str)}\n\n"
            "Return JSON with: preferred_option (must match one of the options), confidence (0-1), reasoning."
        )

        try:
            result = await ai_service.generate_json(prompt)
        except (AIServiceNotConfiguredError, AIProviderCallError) as exc:
            raise RuntimeError(f"AI provider unavailable for opinion synthesis: {exc}") from exc

        preferred = result.get("preferred_option")
        confidence = result.get("confidence")
        reasoning = result.get("reasoning")

        try:
            confidence_val = float(confidence)
            if confidence_val > 1:
                confidence_val = confidence_val / 100.0
        except (TypeError, ValueError):
            confidence_val = 0.5

        return {
            "agent_id": agent_name,
            "agent_name": agent_name,
            "preferred_option": self._match_option(preferred, options),
            "confidence": max(0.0, min(confidence_val, 1.0)),
            "reasoning": reasoning or "No reasoning provided"
        }

    def _match_option(self, preferred: Any, options: List) -> Any:
        """Match preferred option to one of the provided options."""
        if preferred is None or not options:
            return preferred

        for option in options:
            if option == preferred:
                return option

        preferred_str = str(preferred).strip().lower()
        for option in options:
            if preferred_str == str(option).strip().lower():
                return option

        return preferred
    
    async def build_consensus(self, opinions: List[Dict], urgency: str) -> Dict:
        """Build consensus from agent opinions"""
        if not opinions:
            return {
                'decision': 'no_action',
                'confidence': 0.0,
                'reasoning': 'No agent opinions available'
            }
        
        # Count votes for each option
        vote_counts = {}
        total_confidence = 0
        
        for opinion in opinions:
            option = opinion.get('preferred_option')
            if option:
                option_key = str(option)
                if option_key not in vote_counts:
                    vote_counts[option_key] = {'count': 0, 'confidence': 0, 'option': option}
                vote_counts[option_key]['count'] += 1
                vote_counts[option_key]['confidence'] += opinion['confidence']
                total_confidence += opinion['confidence']
        
        if not vote_counts:
            return {
                'decision': opinions[0].get('preferred_option', 'no_action'),
                'confidence': opinions[0].get('confidence', 0.5),
                'reasoning': 'Single agent decision'
            }
        
        # Select option with highest weighted vote
        best_option = max(vote_counts.values(), key=lambda x: x['confidence'])
        
        return {
            'decision': best_option['option'],
            'confidence': best_option['confidence'] / best_option['count'],
            'reasoning': f"Consensus from {len(opinions)} agents with {urgency} urgency",
            'agents_consulted': [o['agent_name'] for o in opinions]
        }
    
    async def log_decision(self, context: Dict, options: List, decision: Dict, agents: List[str]):
        """Log decision to database"""
        conn = self.connect_db()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO ai_board_decisions 
                (decision_type, context, options, selected_option, confidence, reasoning, agents_consulted)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                context.get('type', 'general'),
                json.dumps(context),
                json.dumps(options),
                json.dumps(decision.get('decision')),
                decision.get('confidence', 0),
                decision.get('reasoning', ''),
                decision.get('agents_consulted', [])
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging decision: {e}")
        finally:
            conn.close()
    
    async def execute_task(self, task_type: str, parameters: Dict) -> Dict:
        """Execute a task using the best available agent"""
        self.tasks_executed += 1
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # Find best agent for task
        best_agent = await self.find_best_agent(task_type, parameters)
        
        if not best_agent:
            return {
                'success': False,
                'error': 'No suitable agent found',
                'task_id': task_id
            }
        
        # Log task start
        await self.log_task_start(task_id, task_type, best_agent, parameters)

        try:
            # Execute task with real agent
            result = await self.agent_execute(best_agent, task_type, parameters)
        except Exception as exc:
            error_result = {
                "success": False,
                "task_id": task_id,
                "agent": self.agents.get(best_agent, {}).get("name"),
                "task_type": task_type,
                "error": str(exc),
                "data": {"parameters": parameters}
            }
            await self.log_task_completion(task_id, error_result)
            await self.activate_pathways(best_agent, False)
            raise

        # Log task completion
        await self.log_task_completion(task_id, result)

        # Activate neural pathways
        await self.activate_pathways(best_agent, result['success'])

        return result
    
    async def find_best_agent(self, task_type: str, parameters: Dict) -> Optional[str]:
        """Find the best agent for a specific task"""
        candidates = []
        
        for agent_id, agent in self.agents.items():
            # Check if agent has relevant capabilities
            for capability in agent['capabilities']:
                if capability.lower() in task_type.lower() or task_type.lower() in capability.lower():
                    candidates.append({
                        'id': agent_id,
                        'name': agent['name'],
                        'score': agent['success_rate'] * (1 if agent['status'] == 'ready' else 0.5)
                    })
                    break
        
        if not candidates:
            # Use AUREA as fallback
            for agent_id, agent in self.agents.items():
                if agent['name'] == 'AUREA':
                    return agent_id
        
        # Select best candidate
        if candidates:
            best = max(candidates, key=lambda x: x['score'])
            return best['id']
        
        return None
    
    async def agent_execute(self, agent_id: str, task_type: str, parameters: Dict) -> Dict:
        """Execute task with specific agent"""
        agent = self.agents[agent_id]
        
        # Mark agent as busy
        agent['status'] = 'executing'
        agent['current_task'] = task_type
        start_time = time.time()
        result: Dict[str, Any] = {
            'success': False,
            'task_id': f"task_{uuid.uuid4().hex[:8]}",
            'agent': agent['name'],
            'task_type': task_type,
            'output': {},
            'data': {
                'parameters': parameters,
                'execution_time_ms': None,
                'confidence': None,
                'method': None
            }
        }

        try:
            task_prompt = (
                parameters.get("task")
                or parameters.get("command")
                or parameters.get("prompt")
                or task_type
            )

            execution = await self.agent_executor.execute_agent(
                agent['name'],
                task_prompt,
                {
                    "task_type": task_type,
                    "parameters": parameters,
                    "agent_metadata": agent.get("metadata", {})
                },
                retry_on_failure=True
            )

            success = execution.get("status") == "completed"
            output = execution.get("result") if execution else {}

            duration_ms = (time.time() - start_time) * 1000
            result = {
                'success': success,
                'task_id': execution.get("execution_id") if execution else result["task_id"],
                'agent': agent['name'],
                'task_type': task_type,
                'output': output,
                'data': {
                    'parameters': parameters,
                    'execution_time_ms': duration_ms,
                    'confidence': output.get("confidence") if isinstance(output, dict) else None,
                    'method': output.get("method") if isinstance(output, dict) else None
                }
            }

        finally:
            # Update agent status
            agent['status'] = 'ready'
            agent['current_task'] = None
            completed = agent.get('tasks_completed', 0)
            agent['tasks_completed'] = completed + 1
            if 'success_rate' in agent:
                prior_rate = float(agent.get('success_rate') or 0)
                agent['success_rate'] = ((prior_rate * completed) + (100 if result.get('success') else 0)) / max(completed + 1, 1)

        return result
    
    async def log_task_start(self, task_id: str, task_type: str, agent_id: str, parameters: Dict):
        """Log task execution start"""
        conn = self.connect_db()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO ai_task_executions 
                (task_id, task_type, agent_id, parameters, status, started_at)
                VALUES (%s, %s, %s, %s, 'executing', NOW())
            """, (task_id, task_type, agent_id, json.dumps(parameters)))
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging task start: {e}")
        finally:
            conn.close()
    
    async def log_task_completion(self, task_id: str, result: Dict):
        """Log task completion"""
        conn = self.connect_db()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                UPDATE ai_task_executions 
                SET status = %s, 
                    result = %s,
                    completed_at = NOW(),
                    duration_ms = EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000
                WHERE task_id = %s
            """, (
                'completed' if result['success'] else 'failed',
                json.dumps(result),
                task_id
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging task completion: {e}")
        finally:
            conn.close()
    
    async def activate_pathways(self, agent_id: str, success: bool):
        """Activate neural pathways based on agent activity"""
        # Find pathways involving this agent
        for pathway_key, pathway in self.neural_pathways.items():
            if pathway['source'] == agent_id or pathway['target'] == agent_id:
                # Strengthen successful pathways
                if success:
                    pathway['strength'] = min(100, pathway['strength'] + 1)
                    pathway['usage_count'] += 1
                    pathway['last_activated'] = datetime.now()
    
    async def neural_pulse(self):
        """Background process for continuous neural activity"""
        while True:
            try:
                # Periodic pathway optimization
                await asyncio.sleep(60)  # Every minute
                
                # Decay unused pathways
                for pathway in self.neural_pathways.values():
                    if pathway['last_activated']:
                        time_since = (datetime.now() - pathway['last_activated']).seconds
                        if time_since > 3600:  # 1 hour
                            pathway['strength'] = max(10, pathway['strength'] - 1)
                
                # Strengthen frequently used pathways
                for pathway in self.neural_pathways.values():
                    if pathway['usage_count'] > 100:
                        pathway['strength'] = min(100, pathway['strength'] + 5)
                
            except Exception as e:
                logger.error(f"Neural pulse error: {e}")
                await asyncio.sleep(60)
    
    async def memory_consolidation(self):
        """Background process for memory management"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Move short-term to long-term memory
                if len(self.short_term_memory) > 100:
                    # Extract patterns
                    patterns = await self.extract_patterns()
                    self.long_term_memory.extend(patterns)
                    
                    # Clear old short-term memory
                    self.short_term_memory = self.short_term_memory[-50:]
                
                # Log patterns to database
                if patterns:
                    await self.log_patterns(patterns)
                
            except Exception as e:
                logger.error(f"Memory consolidation error: {e}")
                await asyncio.sleep(300)
    
    async def extract_patterns(self) -> List[Dict]:
        """Extract patterns from short-term memory"""
        patterns = []
        
        # Analyze recent operations
        if self.short_term_memory:
            # Group by operation type
            operation_counts = {}
            for memory in self.short_term_memory:
                op_type = memory.get('type', 'unknown')
                operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
            
            # Identify patterns
            for op_type, count in operation_counts.items():
                if count > 5:  # Threshold for pattern
                    patterns.append({
                        'type': 'frequency_pattern',
                        'operation': op_type,
                        'frequency': count,
                        'confidence': min(0.9, count / len(self.short_term_memory))
                    })
        
        return patterns
    
    async def log_patterns(self, patterns: List[Dict]):
        """Log discovered patterns to database"""
        conn = self.connect_db()
        cur = conn.cursor()
        
        try:
            for pattern in patterns:
                cur.execute("""
                    INSERT INTO ai_learning_patterns 
                    (pattern_type, pattern_data, confidence, frequency)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    pattern['type'],
                    json.dumps(pattern),
                    pattern['confidence'],
                    pattern.get('frequency', 1)
                ))
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging patterns: {e}")
        finally:
            conn.close()
    
    async def performance_monitor(self):
        """Background process for system monitoring"""
        while True:
            try:
                await asyncio.sleep(120)  # Every 2 minutes
                
                # Calculate metrics
                uptime = (datetime.now() - self.start_time).total_seconds() / 3600
                decisions_per_hour = self.decisions_made / max(uptime, 1)
                tasks_per_hour = self.tasks_executed / max(uptime, 1)
                
                # Log metrics
                logger.info(f"""
                📊 AI Brain Performance:
                - Uptime: {uptime:.1f} hours
                - Decisions: {self.decisions_made} ({decisions_per_hour:.1f}/hour)
                - Tasks: {self.tasks_executed} ({tasks_per_hour:.1f}/hour)
                - Active Agents: {sum(1 for a in self.agents.values() if a['status'] != 'offline')}
                - Success Rate: {self.success_rate:.1f}%
                """)
                
            except Exception as e:
                logger.error(f"Performance monitor error: {e}")
                await asyncio.sleep(120)
    
    async def orchestrate_workflow(self, workflow: Dict) -> Dict:
        """Orchestrate complex multi-agent workflow"""
        workflow_id = f"wf_{uuid.uuid4().hex[:8]}"
        results = []
        
        # Parse workflow steps
        steps = workflow.get('steps', [])
        parallel = workflow.get('parallel', False)
        
        if parallel:
            # Execute steps in parallel
            futures = []
            for step in steps:
                future = self.executor.submit(
                    asyncio.run,
                    self.execute_task(step['task'], step.get('params', {}))
                )
                futures.append(future)
            
            # Gather results
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    results.append({'success': False, 'error': str(e)})
        else:
            # Execute steps sequentially
            for step in steps:
                result = await self.execute_task(step['task'], step.get('params', {}))
                results.append(result)
                
                # Check if we should continue
                if not result.get('success') and not workflow.get('continue_on_error'):
                    break
        
        # Log workflow completion
        success_count = sum(1 for r in results if r.get('success'))
        
        return {
            'workflow_id': workflow_id,
            'status': 'completed' if success_count == len(steps) else 'partial',
            'results': results,
            'summary': {
                'total_steps': len(steps),
                'completed': len(results),
                'successful': success_count,
                'success_rate': (success_count / len(steps) * 100) if steps else 0
            }
        }
    
    async def aurea_execute(self, command: str, context: Dict) -> Dict:
        """Execute AUREA master controller command"""
        # Find AUREA
        aurea_id = None
        for agent_id, agent in self.agents.items():
            if agent['name'] == 'AUREA':
                aurea_id = agent_id
                break
        
        if not aurea_id:
            return {'error': 'AUREA not found'}
        
        # Parse command intent
        command_lower = command.lower()
        
        if 'optimize' in command_lower:
            return await self.optimize_system()
        elif 'status' in command_lower:
            return await self.get_system_status()
        elif 'execute' in command_lower:
            # Extract task from command
            return await self.execute_task('general', {'command': command})
        else:
            return await self._interpret_aurea_command(command, context)

    async def _interpret_aurea_command(self, command: str, context: Dict) -> Dict:
        """Use real AI to interpret and route AUREA commands."""
        from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError, AIProviderCallError

        prompt = (
            "You are AUREA, the master controller of BrainOps AI OS. "
            "Interpret the command and choose an action.\n\n"
            f"Command: {command}\n"
            f"Context: {json.dumps(context, default=str)}\n\n"
            "Return JSON with keys: action (execute_task|make_decision|report_status|optimize_system|respond), "
            "task_type, parameters, options, response."
        )

        try:
            result = await ai_service.generate_json(prompt)
        except (AIServiceNotConfiguredError, AIProviderCallError) as exc:
            raise RuntimeError(f"AUREA AI provider unavailable: {exc}") from exc

        action = (result.get("action") or "respond").lower()
        if action == "execute_task":
            task_type = result.get("task_type") or "general"
            params = result.get("parameters") or {"command": command}
            task_result = await self.execute_task(task_type, params)
            return {
                "command": command,
                "status": "executed",
                "agent": "AUREA",
                "result": task_result,
                "timestamp": datetime.now().isoformat()
            }

        if action == "make_decision":
            options = result.get("options") or []
            decision = await self.make_decision(context or {}, options, urgency=context.get("urgency", "normal") if isinstance(context, dict) else "normal")
            return {
                "command": command,
                "status": "executed",
                "agent": "AUREA",
                "result": decision,
                "timestamp": datetime.now().isoformat()
            }

        if action == "optimize_system":
            return await self.optimize_system()
        if action == "report_status":
            return await self.get_system_status()

        return {
            "command": command,
            "status": "executed",
            "agent": "AUREA",
            "result": result.get("response") or "Command processed",
            "timestamp": datetime.now().isoformat()
        }
    
    async def optimize_system(self) -> Dict:
        """Optimize entire AI system"""
        optimizations = {
            'pathways_optimized': 0,
            'agents_optimized': 0,
            'memory_consolidated': 0
        }
        
        # Optimize pathways
        for pathway in self.neural_pathways.values():
            if pathway['usage_count'] > 50 and pathway['strength'] < 80:
                pathway['strength'] = min(100, pathway['strength'] + 10)
                optimizations['pathways_optimized'] += 1
        
        # Optimize agent configurations
        for agent in self.agents.values():
            if agent['success_rate'] < 80 and agent['tasks_completed'] > 10:
                # Flag for retraining
                agent['metadata']['needs_optimization'] = True
                optimizations['agents_optimized'] += 1
        
        # Consolidate memory
        if len(self.short_term_memory) > 50:
            patterns = await self.extract_patterns()
            self.long_term_memory.extend(patterns)
            self.short_term_memory = self.short_term_memory[-25:]
            optimizations['memory_consolidated'] = len(patterns)
        
        return {
            'status': 'optimized',
            'optimizations': optimizations,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            'status': 'operational',
            'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600,
            'agents': {
                'total': len(self.agents),
                'active': sum(1 for a in self.agents.values() if a['status'] != 'offline'),
                'by_type': self._count_agents_by_type()
            },
            'neural_network': {
                'pathways': len(self.neural_pathways),
                'average_strength': sum(p['strength'] for p in self.neural_pathways.values()) / len(self.neural_pathways) if self.neural_pathways else 0,
                'active_connections': sum(1 for p in self.neural_pathways.values() if p['last_activated'])
            },
            'performance': {
                'decisions_made': self.decisions_made,
                'tasks_executed': self.tasks_executed,
                'success_rate': self.success_rate,
                'learning_rate': self.learning_rate
            },
            'memory': {
                'short_term': len(self.short_term_memory),
                'long_term': len(self.long_term_memory),
                'working': len(self.working_memory)
            }
        }
    
    def _count_agents_by_type(self) -> Dict[str, int]:
        """Count agents by type"""
        counts = {}
        for agent in self.agents.values():
            agent_type = agent['type']
            counts[agent_type] = counts.get(agent_type, 0) + 1
        return counts

# Export class
__all__ = ['AIBrainProduction']
