"""
CLAUDEOS Automation System
Complete automation framework for all operations
"""

import asyncio
import json
from datetime import datetime, UTC, timedelta
from typing import Dict, Any, List, Optional
import asyncpg
import aioredis
from enum import Enum
import httpx
import yaml
from dataclasses import dataclass

class AutomationTrigger(Enum):
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    EVENT = "event"
    MANUAL = "manual"
    CONDITION = "condition"

@dataclass
class AutomationRule:
    id: str
    name: str
    trigger: AutomationTrigger
    conditions: Dict
    actions: List[Dict]
    enabled: bool = True
    cooldown: int = 0  # seconds
    last_run: Optional[datetime] = None

class CLAUDEOSAutomation:
    def __init__(self, db_pool: asyncpg.Pool, redis: aioredis.Redis):
        self.db_pool = db_pool
        self.redis = redis
        self.rules = {}
        self.running_automations = set()
        self.automation_history = []
        
    async def initialize(self):
        """Initialize automation system"""
        await self.create_tables()
        await self.load_automation_rules()
        await self.start_automation_engine()
    
    async def create_tables(self):
        """Create automation tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS automation_rules (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    trigger_type VARCHAR(50),
                    trigger_config JSONB,
                    conditions JSONB,
                    actions JSONB,
                    enabled BOOLEAN DEFAULT true,
                    cooldown INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS automation_executions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    rule_id UUID REFERENCES automation_rules(id),
                    trigger_data JSONB,
                    status VARCHAR(50),
                    result JSONB,
                    error TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_automation_rules_enabled 
                ON automation_rules(enabled);
                
                CREATE INDEX IF NOT EXISTS idx_automation_executions_rule_id 
                ON automation_executions(rule_id);
            """)
    
    async def load_automation_rules(self):
        """Load automation rules from database"""
        async with self.db_pool.acquire() as conn:
            rules = await conn.fetch("""
                SELECT * FROM automation_rules WHERE enabled = true
            """)
            
            for rule in rules:
                self.rules[rule['id']] = AutomationRule(
                    id=str(rule['id']),
                    name=rule['name'],
                    trigger=AutomationTrigger(rule['trigger_type']),
                    conditions=rule['conditions'],
                    actions=rule['actions'],
                    enabled=rule['enabled'],
                    cooldown=rule['cooldown']
                )
    
    async def start_automation_engine(self):
        """Start the automation engine"""
        tasks = [
            asyncio.create_task(self.webhook_listener()),
            asyncio.create_task(self.schedule_runner()),
            asyncio.create_task(self.event_listener()),
            asyncio.create_task(self.condition_monitor()),
            asyncio.create_task(self.automation_health_monitor())
        ]
        await asyncio.gather(*tasks)
    
    async def webhook_listener(self):
        """Listen for webhook triggers"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe('webhooks:*')
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                webhook_data = json.loads(message['data'])
                await self.process_webhook_trigger(webhook_data)
    
    async def process_webhook_trigger(self, webhook_data: Dict):
        """Process webhook-triggered automations"""
        for rule_id, rule in self.rules.items():
            if rule.trigger != AutomationTrigger.WEBHOOK:
                continue
            
            # Check if webhook matches rule conditions
            if self.matches_webhook_conditions(webhook_data, rule.conditions):
                await self.execute_automation(rule, webhook_data)
    
    def matches_webhook_conditions(self, webhook_data: Dict, conditions: Dict) -> bool:
        """Check if webhook data matches rule conditions"""
        for key, expected in conditions.items():
            actual = webhook_data
            for part in key.split('.'):
                actual = actual.get(part, {})
            
            if isinstance(expected, dict):
                if '$in' in expected and actual not in expected['$in']:
                    return False
                if '$eq' in expected and actual != expected['$eq']:
                    return False
                if '$contains' in expected and expected['$contains'] not in str(actual):
                    return False
            elif actual != expected:
                return False
        
        return True
    
    async def schedule_runner(self):
        """Run scheduled automations"""
        while True:
            try:
                current_time = datetime.now(UTC)
                
                for rule_id, rule in self.rules.items():
                    if rule.trigger != AutomationTrigger.SCHEDULE:
                        continue
                    
                    schedule = rule.conditions.get('schedule', {})
                    if self.should_run_schedule(schedule, current_time):
                        await self.execute_automation(rule, {'triggered_at': current_time.isoformat()})
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Schedule runner error: {e}")
    
    def should_run_schedule(self, schedule: Dict, current_time: datetime) -> bool:
        """Check if schedule should run"""
        schedule_type = schedule.get('type')
        
        if schedule_type == 'cron':
            # Implement cron expression evaluation
            return self.evaluate_cron(schedule.get('expression'), current_time)
        elif schedule_type == 'interval':
            interval = schedule.get('interval', 3600)
            last_run = schedule.get('last_run')
            if not last_run:
                return True
            return (current_time - last_run).total_seconds() >= interval
        
        return False
    
    async def event_listener(self):
        """Listen for system events"""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe('events:*')
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                event_data = json.loads(message['data'])
                await self.process_event_trigger(event_data)
    
    async def process_event_trigger(self, event_data: Dict):
        """Process event-triggered automations"""
        for rule_id, rule in self.rules.items():
            if rule.trigger != AutomationTrigger.EVENT:
                continue
            
            event_type = event_data.get('type')
            expected_events = rule.conditions.get('events', [])
            
            if event_type in expected_events:
                await self.execute_automation(rule, event_data)
    
    async def condition_monitor(self):
        """Monitor conditions for automation triggers"""
        while True:
            try:
                for rule_id, rule in self.rules.items():
                    if rule.trigger != AutomationTrigger.CONDITION:
                        continue
                    
                    if await self.evaluate_conditions(rule.conditions):
                        await self.execute_automation(rule, {'condition_met': True})
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Condition monitor error: {e}")
    
    async def evaluate_conditions(self, conditions: Dict) -> bool:
        """Evaluate automation conditions"""
        condition_type = conditions.get('type')
        
        if condition_type == 'metric':
            return await self.evaluate_metric_condition(conditions)
        elif condition_type == 'database':
            return await self.evaluate_database_condition(conditions)
        elif condition_type == 'api':
            return await self.evaluate_api_condition(conditions)
        
        return False
    
    async def evaluate_metric_condition(self, conditions: Dict) -> bool:
        """Evaluate metric-based condition"""
        metric = conditions.get('metric')
        operator = conditions.get('operator', 'gt')
        threshold = conditions.get('threshold')
        
        # Get current metric value
        value = await self.get_metric_value(metric)
        
        operators = {
            'gt': lambda x, y: x > y,
            'gte': lambda x, y: x >= y,
            'lt': lambda x, y: x < y,
            'lte': lambda x, y: x <= y,
            'eq': lambda x, y: x == y
        }
        
        return operators.get(operator, lambda x, y: False)(value, threshold)
    
    async def execute_automation(self, rule: AutomationRule, trigger_data: Dict):
        """Execute automation rule"""
        # Check cooldown
        if rule.last_run and rule.cooldown > 0:
            elapsed = (datetime.now(UTC) - rule.last_run).total_seconds()
            if elapsed < rule.cooldown:
                return
        
        # Check if already running
        if rule.id in self.running_automations:
            return
        
        self.running_automations.add(rule.id)
        
        execution_id = await self.start_execution(rule.id, trigger_data)
        
        try:
            results = []
            for action in rule.actions:
                result = await self.execute_action(action, trigger_data)
                results.append(result)
            
            await self.complete_execution(execution_id, results)
            rule.last_run = datetime.now(UTC)
            
        except Exception as e:
            await self.fail_execution(execution_id, str(e))
            
        finally:
            self.running_automations.discard(rule.id)
    
    async def execute_action(self, action: Dict, context: Dict) -> Dict:
        """Execute a single automation action"""
        action_type = action.get('type')
        
        actions = {
            'webhook': self.execute_webhook_action,
            'database': self.execute_database_action,
            'notification': self.execute_notification_action,
            'deployment': self.execute_deployment_action,
            'scaling': self.execute_scaling_action,
            'remediation': self.execute_remediation_action
        }
        
        handler = actions.get(action_type)
        if handler:
            return await handler(action, context)
        
        return {'error': f'Unknown action type: {action_type}'}
    
    async def execute_webhook_action(self, action: Dict, context: Dict) -> Dict:
        """Execute webhook action"""
        url = action.get('url')
        method = action.get('method', 'POST')
        headers = action.get('headers', {})
        payload = self.render_template(action.get('payload', {}), context)
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=payload
            )
            
            return {
                'status_code': response.status_code,
                'response': response.text
            }
    
    async def execute_database_action(self, action: Dict, context: Dict) -> Dict:
        """Execute database action"""
        query = action.get('query')
        params = action.get('params', [])
        
        # Render parameters with context
        rendered_params = [
            self.render_template(param, context) if isinstance(param, str) else param
            for param in params
        ]
        
        async with self.db_pool.acquire() as conn:
            if action.get('operation') == 'select':
                result = await conn.fetch(query, *rendered_params)
                return {'rows': [dict(r) for r in result]}
            else:
                result = await conn.execute(query, *rendered_params)
                return {'affected': result}
    
    async def execute_notification_action(self, action: Dict, context: Dict) -> Dict:
        """Execute notification action"""
        channels = action.get('channels', ['slack'])
        message = self.render_template(action.get('message'), context)
        
        results = {}
        for channel in channels:
            if channel == 'slack':
                results['slack'] = await self.send_slack_notification(message)
            elif channel == 'email':
                results['email'] = await self.send_email_notification(
                    action.get('recipients', []),
                    action.get('subject'),
                    message
                )
            elif channel == 'sms':
                results['sms'] = await self.send_sms_notification(
                    action.get('phone_numbers', []),
                    message
                )
        
        return results
    
    async def execute_deployment_action(self, action: Dict, context: Dict) -> Dict:
        """Execute deployment action"""
        service = action.get('service')
        operation = action.get('operation')
        
        if service == 'vercel':
            return await self.execute_vercel_deployment(operation, action)
        elif service == 'render':
            return await self.execute_render_deployment(operation, action)
        
        return {'error': f'Unknown service: {service}'}
    
    async def execute_scaling_action(self, action: Dict, context: Dict) -> Dict:
        """Execute scaling action"""
        service = action.get('service')
        scale_type = action.get('scale_type')
        value = action.get('value')
        
        if scale_type == 'horizontal':
            return await self.scale_horizontally(service, value)
        elif scale_type == 'vertical':
            return await self.scale_vertically(service, value)
        
        return {'error': f'Unknown scale type: {scale_type}'}
    
    async def execute_remediation_action(self, action: Dict, context: Dict) -> Dict:
        """Execute remediation action"""
        issue_type = context.get('issue_type')
        
        remediations = {
            'high_memory': self.remediate_high_memory,
            'high_cpu': self.remediate_high_cpu,
            'database_connection': self.remediate_database_connection,
            'deployment_failure': self.remediate_deployment_failure
        }
        
        handler = remediations.get(issue_type)
        if handler:
            return await handler(context)
        
        return {'error': f'No remediation for: {issue_type}'}
    
    def render_template(self, template: Any, context: Dict) -> Any:
        """Render template with context"""
        if isinstance(template, str):
            for key, value in context.items():
                template = template.replace(f'{{{{{key}}}}}', str(value))
            return template
        elif isinstance(template, dict):
            return {k: self.render_template(v, context) for k, v in template.items()}
        elif isinstance(template, list):
            return [self.render_template(item, context) for item in template]
        return template
    
    async def start_execution(self, rule_id: str, trigger_data: Dict) -> str:
        """Start automation execution"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO automation_executions 
                (rule_id, trigger_data, status, started_at)
                VALUES ($1, $2, 'running', $3)
                RETURNING id
            """, rule_id, json.dumps(trigger_data), datetime.now(UTC))
            
            return str(result['id'])
    
    async def complete_execution(self, execution_id: str, results: List[Dict]):
        """Complete automation execution"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE automation_executions
                SET status = 'completed',
                    result = $1,
                    completed_at = $2
                WHERE id = $3
            """, json.dumps(results), datetime.now(UTC), execution_id)
    
    async def fail_execution(self, execution_id: str, error: str):
        """Fail automation execution"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE automation_executions
                SET status = 'failed',
                    error = $1,
                    completed_at = $2
                WHERE id = $3
            """, error, datetime.now(UTC), execution_id)
    
    async def automation_health_monitor(self):
        """Monitor automation system health"""
        while True:
            try:
                stats = await self.get_automation_stats()
                
                # Check failure rate
                if stats['failure_rate'] > 0.1:
                    await self.send_alert('High automation failure rate')
                
                # Check stuck automations
                if stats['stuck_count'] > 0:
                    await self.cleanup_stuck_automations()
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"Health monitor error: {e}")
    
    async def get_automation_stats(self) -> Dict:
        """Get automation statistics"""
        async with self.db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_executions,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    COUNT(*) FILTER (WHERE status = 'running' 
                        AND started_at < NOW() - INTERVAL '1 hour') as stuck_count
                FROM automation_executions
                WHERE started_at > NOW() - INTERVAL '24 hours'
            """)
            
            return {
                'total': stats['total_executions'],
                'failed': stats['failed'],
                'failure_rate': stats['failed'] / max(stats['total_executions'], 1),
                'stuck_count': stats['stuck_count']
            }

# Initialize automation system
async def setup_claudeos_automation(app):
    """Set up CLAUDEOS automation"""
    db_pool = await asyncpg.create_pool(os.getenv('DATABASE_URL'))
    redis = await aioredis.from_url(os.getenv('REDIS_URL'))
    
    automation = CLAUDEOSAutomation(db_pool, redis)
    await automation.initialize()
    
    app.state.claudeos = automation
    
    return automation