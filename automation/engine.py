# WeatherCraft ERP - Automation Engine
# Comprehensive workflow automation and business rule processing

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class AutomationEngine:
    """Core automation engine for workflow execution and business rules"""
    
    def __init__(self, db: Session):
        self.db = db
        self.active_workflows = {}
        self.rule_cache = {}
        
    async def trigger_workflow(self, workflow_id: str, trigger_data: Dict[str, Any]) -> str:
        """Trigger a workflow execution"""
        try:
            # Get workflow definition
            workflow = self._get_workflow(workflow_id)
            if not workflow or not workflow['is_active']:
                raise ValueError(f"Workflow {workflow_id} not found or inactive")
            
            # Check conditions
            if not self._evaluate_conditions(workflow['conditions'], trigger_data):
                logger.info(f"Workflow {workflow_id} conditions not met")
                return None
            
            # Create execution record
            execution_id = self._create_execution(workflow_id, trigger_data)
            
            # Execute workflow asynchronously
            asyncio.create_task(self._execute_workflow(execution_id, workflow, trigger_data))
            
            return execution_id
            
        except Exception as e:
            logger.error(f"Error triggering workflow: {e}")
            raise
    
    async def _execute_workflow(self, execution_id: str, workflow: Dict, context: Dict):
        """Execute workflow actions"""
        try:
            actions = workflow['actions']
            
            for idx, action in enumerate(actions):
                step_id = self._create_step(execution_id, idx + 1, action)
                
                try:
                    # Execute action based on type
                    result = await self._execute_action(action, context)
                    
                    # Update step as completed
                    self._update_step(step_id, 'completed', result)
                    
                    # Update context with result
                    context[f"step_{idx + 1}_result"] = result
                    
                except Exception as e:
                    logger.error(f"Error executing action: {e}")
                    self._update_step(step_id, 'failed', error=str(e))
                    
                    # Check if workflow should continue on error
                    if not action.get('continue_on_error', False):
                        self._complete_execution(execution_id, 'failed', str(e))
                        return
            
            # Mark execution as completed
            self._complete_execution(execution_id, 'completed')
            
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            self._complete_execution(execution_id, 'failed', str(e))
    
    async def _execute_action(self, action: Dict, context: Dict) -> Any:
        """Execute a single workflow action"""
        action_type = action['type']
        
        if action_type == 'email':
            return await self._send_email(action, context)
        elif action_type == 'sms':
            return await self._send_sms(action, context)
        elif action_type == 'create_task':
            return await self._create_task(action, context)
        elif action_type == 'update_entity':
            return await self._update_entity(action, context)
        elif action_type == 'webhook':
            return await self._call_webhook(action, context)
        elif action_type == 'wait':
            return await self._wait(action, context)
        elif action_type == 'condition':
            return await self._evaluate_condition(action, context)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    async def _send_email(self, action: Dict, context: Dict) -> Dict:
        """Send email notification"""
        template_id = action.get('template_id')
        recipient = self._resolve_value(action['recipient'], context)
        
        # Queue email for sending
        query = """
        INSERT INTO notification_queue (
            recipient_email, notification_type, template_id,
            subject, message, data, status
        ) VALUES (
            :recipient, 'email', :template_id,
            :subject, :message, :data, 'pending'
        ) RETURNING id
        """
        
        result = self.db.execute(text(query), {
            'recipient': recipient,
            'template_id': template_id,
            'subject': self._resolve_value(action.get('subject'), context),
            'message': self._resolve_value(action.get('message'), context),
            'data': json.dumps(context)
        })
        
        notification_id = result.scalar()
        self.db.commit()
        
        return {'notification_id': str(notification_id), 'status': 'queued'}
    
    async def _send_sms(self, action: Dict, context: Dict) -> Dict:
        """Send SMS notification"""
        recipient = self._resolve_value(action['recipient'], context)
        message = self._resolve_value(action['message'], context)
        
        # Queue SMS for sending
        query = """
        INSERT INTO notification_queue (
            recipient_phone, notification_type,
            message, data, status
        ) VALUES (
            :recipient, 'sms',
            :message, :data, 'pending'
        ) RETURNING id
        """
        
        result = self.db.execute(text(query), {
            'recipient': recipient,
            'message': message,
            'data': json.dumps(context)
        })
        
        notification_id = result.scalar()
        self.db.commit()
        
        return {'notification_id': str(notification_id), 'status': 'queued'}
    
    async def _create_task(self, action: Dict, context: Dict) -> Dict:
        """Create an automated task"""
        query = """
        INSERT INTO automated_tasks (
            title, description, assigned_to, assigned_role,
            due_date, priority, entity_type, entity_id,
            source_type, status
        ) VALUES (
            :title, :description, :assigned_to, :assigned_role,
            :due_date, :priority, :entity_type, :entity_id,
            'workflow', 'pending'
        ) RETURNING id
        """
        
        due_days = action.get('due_days', 1)
        due_date = datetime.now().date() + timedelta(days=due_days)
        
        result = self.db.execute(text(query), {
            'title': self._resolve_value(action['title'], context),
            'description': self._resolve_value(action.get('description'), context),
            'assigned_to': action.get('assigned_to'),
            'assigned_role': action.get('assigned_role'),
            'due_date': due_date,
            'priority': action.get('priority', 'normal'),
            'entity_type': context.get('entity_type'),
            'entity_id': context.get('entity_id')
        })
        
        task_id = result.scalar()
        self.db.commit()
        
        return {'task_id': str(task_id), 'due_date': str(due_date)}
    
    async def _update_entity(self, action: Dict, context: Dict) -> Dict:
        """Update an entity in the database"""
        entity_type = action['entity_type']
        entity_id = context.get('entity_id') or action.get('entity_id')
        updates = action['updates']
        
        # Build update query dynamically
        table_map = {
            'lead': 'leads',
            'customer': 'customers',
            'job': 'jobs',
            'estimate': 'estimates',
            'invoice': 'invoices',
            'service_ticket': 'service_tickets'
        }
        
        table = table_map.get(entity_type)
        if not table:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        # Build SET clause
        set_clauses = []
        params = {'entity_id': entity_id}
        
        for field, value in updates.items():
            set_clauses.append(f"{field} = :{field}")
            params[field] = self._resolve_value(value, context)
        
        query = f"""
        UPDATE {table}
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE id = :entity_id
        """
        
        self.db.execute(text(query), params)
        self.db.commit()
        
        return {'entity_type': entity_type, 'entity_id': entity_id, 'updated': True}
    
    async def _call_webhook(self, action: Dict, context: Dict) -> Dict:
        """Call external webhook"""
        import aiohttp
        
        url = self._resolve_value(action['url'], context)
        method = action.get('method', 'POST')
        headers = action.get('headers', {})
        payload = self._resolve_value(action.get('payload', {}), context)
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=payload, headers=headers) as response:
                return {
                    'status_code': response.status,
                    'response': await response.text()
                }
    
    async def _wait(self, action: Dict, context: Dict) -> Dict:
        """Wait for specified duration"""
        duration = action.get('duration', 1)
        unit = action.get('unit', 'seconds')
        
        if unit == 'seconds':
            await asyncio.sleep(duration)
        elif unit == 'minutes':
            await asyncio.sleep(duration * 60)
        elif unit == 'hours':
            await asyncio.sleep(duration * 3600)
        
        return {'waited': duration, 'unit': unit}
    
    async def _evaluate_condition(self, action: Dict, context: Dict) -> Dict:
        """Evaluate a condition and branch"""
        condition = action['condition']
        result = self._evaluate_conditions(condition, context)
        
        if result:
            if 'then_actions' in action:
                for then_action in action['then_actions']:
                    await self._execute_action(then_action, context)
        else:
            if 'else_actions' in action:
                for else_action in action['else_actions']:
                    await self._execute_action(else_action, context)
        
        return {'condition_met': result}
    
    def _evaluate_conditions(self, conditions: Dict, context: Dict) -> bool:
        """Evaluate workflow conditions"""
        if not conditions:
            return True
        
        if 'all' in conditions:
            return all(self._evaluate_single_condition(c, context) for c in conditions['all'])
        elif 'any' in conditions:
            return any(self._evaluate_single_condition(c, context) for c in conditions['any'])
        else:
            return self._evaluate_single_condition(conditions, context)
    
    def _evaluate_single_condition(self, condition: Dict, context: Dict) -> bool:
        """Evaluate a single condition"""
        field = condition['field']
        operator = condition['operator']
        value = condition['value']
        
        actual_value = self._get_field_value(field, context)
        
        if operator == 'equals':
            return actual_value == value
        elif operator == 'not_equals':
            return actual_value != value
        elif operator == 'greater_than':
            return actual_value > value
        elif operator == 'less_than':
            return actual_value < value
        elif operator == 'contains':
            return value in str(actual_value)
        elif operator == 'in':
            return actual_value in value
        elif operator == 'not_in':
            return actual_value not in value
        else:
            return False
    
    def _resolve_value(self, value: Any, context: Dict) -> Any:
        """Resolve template variables in values"""
        if isinstance(value, str) and '{{' in value:
            import re
            pattern = r'\{\{(\w+)\}\}'
            
            def replace(match):
                key = match.group(1)
                return str(context.get(key, ''))
            
            return re.sub(pattern, replace, value)
        elif isinstance(value, dict):
            return {k: self._resolve_value(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_value(v, context) for v in value]
        else:
            return value
    
    def _get_field_value(self, field: str, context: Dict) -> Any:
        """Get field value from context"""
        parts = field.split('.')
        value = context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        
        return value
    
    def _get_workflow(self, workflow_id: str) -> Dict:
        """Get workflow definition from database"""
        query = "SELECT * FROM workflows WHERE id = :workflow_id"
        result = self.db.execute(text(query), {'workflow_id': workflow_id})
        row = result.fetchone()
        
        if row:
            workflow = dict(row)
            workflow['conditions'] = json.loads(workflow['conditions']) if workflow['conditions'] else {}
            workflow['actions'] = json.loads(workflow['actions']) if workflow['actions'] else []
            return workflow
        
        return None
    
    def _create_execution(self, workflow_id: str, trigger_data: Dict) -> str:
        """Create workflow execution record"""
        execution_id = str(uuid4())
        execution_number = f"WF-{datetime.now().strftime('%Y%m%d')}-{execution_id[:8].upper()}"
        
        query = """
        INSERT INTO workflow_executions (
            id, workflow_id, execution_number,
            trigger_source, trigger_data, status
        ) VALUES (
            :id, :workflow_id, :execution_number,
            :trigger_source, :trigger_data, 'running'
        )
        """
        
        self.db.execute(text(query), {
            'id': execution_id,
            'workflow_id': workflow_id,
            'execution_number': execution_number,
            'trigger_source': trigger_data.get('source', 'manual'),
            'trigger_data': json.dumps(trigger_data)
        })
        self.db.commit()
        
        return execution_id
    
    def _create_step(self, execution_id: str, step_number: int, action: Dict) -> str:
        """Create workflow step record"""
        step_id = str(uuid4())
        
        query = """
        INSERT INTO workflow_steps (
            id, execution_id, step_number,
            step_name, action_type, status,
            started_at
        ) VALUES (
            :id, :execution_id, :step_number,
            :step_name, :action_type, 'running',
            NOW()
        )
        """
        
        self.db.execute(text(query), {
            'id': step_id,
            'execution_id': execution_id,
            'step_number': step_number,
            'step_name': action.get('name', f"Step {step_number}"),
            'action_type': action['type']
        })
        self.db.commit()
        
        return step_id
    
    def _update_step(self, step_id: str, status: str, result: Any = None, error: str = None):
        """Update workflow step status"""
        query = """
        UPDATE workflow_steps
        SET status = :status,
            completed_at = NOW(),
            output_data = :output_data,
            error_message = :error_message
        WHERE id = :step_id
        """
        
        self.db.execute(text(query), {
            'step_id': step_id,
            'status': status,
            'output_data': json.dumps(result) if result else None,
            'error_message': error
        })
        self.db.commit()
    
    def _complete_execution(self, execution_id: str, status: str, error: str = None):
        """Complete workflow execution"""
        query = """
        UPDATE workflow_executions
        SET status = :status,
            completed_at = NOW(),
            error_message = :error_message
        WHERE id = :execution_id
        """
        
        self.db.execute(text(query), {
            'execution_id': execution_id,
            'status': status,
            'error_message': error
        })
        self.db.commit()


class RuleEngine:
    """Business rule processing engine"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process_entity(self, entity_type: str, entity_id: str, event: str = 'created'):
        """Process business rules for an entity"""
        # Get applicable rules
        rules = self._get_applicable_rules(entity_type, event)
        
        # Get entity data
        entity_data = self._get_entity_data(entity_type, entity_id)
        
        for rule in rules:
            try:
                # Evaluate rule conditions
                if self._evaluate_rule_conditions(rule, entity_data):
                    # Execute rule actions
                    await self._execute_rule_actions(rule, entity_data)
                    
                    # Update rule execution count
                    self._update_rule_stats(rule['id'])
                    
            except Exception as e:
                logger.error(f"Error processing rule {rule['id']}: {e}")
    
    def _get_applicable_rules(self, entity_type: str, event: str) -> List[Dict]:
        """Get rules applicable to entity type and event"""
        query = """
        SELECT * FROM automation_rules
        WHERE entity_type = :entity_type
        AND is_active = TRUE
        ORDER BY priority
        """
        
        result = self.db.execute(text(query), {'entity_type': entity_type})
        rules = []
        
        for row in result:
            rule = dict(row)
            rule['conditions'] = json.loads(rule['conditions']) if rule['conditions'] else {}
            rule['actions'] = json.loads(rule['actions']) if rule['actions'] else []
            rules.append(rule)
        
        return rules
    
    def _get_entity_data(self, entity_type: str, entity_id: str) -> Dict:
        """Get entity data from database"""
        table_map = {
            'lead': 'leads',
            'customer': 'customers',
            'job': 'jobs',
            'estimate': 'estimates',
            'invoice': 'invoices',
            'service_ticket': 'service_tickets'
        }
        
        table = table_map.get(entity_type)
        if not table:
            return {}

        # Table name is from whitelist (table_map) so it's safe
        query = text(f"SELECT * FROM {table} WHERE id = :entity_id")
        result = self.db.execute(query, {'entity_id': entity_id})
        row = result.fetchone()
        
        return dict(row) if row else {}
    
    def _evaluate_rule_conditions(self, rule: Dict, entity_data: Dict) -> bool:
        """Evaluate rule conditions against entity data"""
        conditions = rule['conditions']
        
        if not conditions:
            return True
        
        if 'all' in conditions:
            return all(self._evaluate_condition(c, entity_data) for c in conditions['all'])
        elif 'any' in conditions:
            return any(self._evaluate_condition(c, entity_data) for c in conditions['any'])
        else:
            return self._evaluate_condition(conditions, entity_data)
    
    def _evaluate_condition(self, condition: Dict, data: Dict) -> bool:
        """Evaluate a single condition"""
        field = condition['field']
        operator = condition['operator']
        value = condition['value']
        
        actual_value = data.get(field)
        
        if operator == 'equals':
            return actual_value == value
        elif operator == 'not_equals':
            return actual_value != value
        elif operator == 'greater_than':
            return actual_value > value
        elif operator == 'less_than':
            return actual_value < value
        elif operator == 'contains':
            return value in str(actual_value)
        elif operator == 'in':
            return actual_value in value
        elif operator == 'not_in':
            return actual_value not in value
        elif operator == 'is_null':
            return actual_value is None
        elif operator == 'is_not_null':
            return actual_value is not None
        else:
            return False
    
    async def _execute_rule_actions(self, rule: Dict, entity_data: Dict):
        """Execute rule actions"""
        for action in rule['actions']:
            action_type = action['type']
            
            if action_type == 'assign':
                await self._assign_entity(action, entity_data)
            elif action_type == 'notify':
                await self._send_notification(action, entity_data)
            elif action_type == 'update':
                await self._update_entity(action, entity_data)
            elif action_type == 'create_task':
                await self._create_task(action, entity_data)
    
    async def _assign_entity(self, action: Dict, entity_data: Dict):
        """Assign entity to user"""
        # Implementation would update the appropriate field in the entity
        pass
    
    async def _send_notification(self, action: Dict, entity_data: Dict):
        """Send notification based on rule action"""
        # Implementation would queue notification
        pass
    
    async def _update_entity(self, action: Dict, entity_data: Dict):
        """Update entity fields"""
        # Implementation would update entity in database
        pass
    
    async def _create_task(self, action: Dict, entity_data: Dict):
        """Create automated task"""
        # Implementation would create task in database
        pass
    
    def _update_rule_stats(self, rule_id: str):
        """Update rule execution statistics"""
        query = """
        UPDATE automation_rules
        SET execution_count = execution_count + 1,
            last_executed = NOW()
        WHERE id = :rule_id
        """
        
        self.db.execute(text(query), {'rule_id': rule_id})
        self.db.commit()