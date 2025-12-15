# WeatherCraft ERP - Workflow Orchestration API
# Complete workflow management and automation endpoints

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime
from uuid import uuid4
# asyncpg not needed - using SQLAlchemy

# Database setup (avoiding circular import from main)
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.yomagoqdmxszqtdwuhab:<DB_PASSWORD_REDACTED>@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# These services might not be available yet
try:
    from automation.engine import AutomationEngine, RuleEngine
except ImportError:
    AutomationEngine = None
    RuleEngine = None

try:
    from services.notifications import NotificationService
except ImportError:
    NotificationService = None

logger = logging.getLogger(__name__)

# Use the SQLAlchemy get_db defined above, not asyncpg
# Remove duplicate async get_db function

router = APIRouter()

# ============================================================================
# WORKFLOW MANAGEMENT
# ============================================================================

@router.post("/workflows")
async def create_workflow(
    workflow: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new workflow definition"""
    try:
        workflow_id = str(uuid4())
        
        query = """
        INSERT INTO workflows (
            id, name, description, category,
            trigger_type, trigger_config,
            conditions, actions,
            is_active, created_by
        ) VALUES (
            :id, :name, :description, :category,
            :trigger_type, :trigger_config,
            :conditions, :actions,
            :is_active, :created_by
        )
        """
        
        db.execute(text(query), {
            'id': workflow_id,
            'name': workflow['name'],
            'description': workflow.get('description'),
            'category': workflow.get('category'),
            'trigger_type': workflow['trigger_type'],
            'trigger_config': json.dumps(workflow.get('trigger_config', {})),
            'conditions': json.dumps(workflow.get('conditions', {})),
            'actions': json.dumps(workflow['actions']),
            'is_active': workflow.get('is_active', True),
            'created_by': workflow.get('created_by')
        })
        
        db.commit()
        
        return {
            'workflow': {
                'id': workflow_id,
                'name': workflow['name'],
                'status': 'created'
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows")
async def get_workflows(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get workflows with filtering"""
    try:
        query = """
        SELECT
            w.*,
            0 as execution_count,
            NULL as last_execution
        FROM workflows w
        WHERE 1=1
        """
        
        params = {}
        
        if category:
            query += " AND w.category = :category"
            params['category'] = category
            
        if is_active is not None:
            query += " AND w.is_active = :is_active"
            params['is_active'] = is_active
            
        query += """
        ORDER BY w.created_at DESC
        LIMIT :limit OFFSET :skip
        """
        
        params['limit'] = limit
        params['skip'] = skip
        
        result = db.execute(text(query), params)
        workflows = []

        for row in result:
            # Use _mapping to convert row to dict properly
            workflow = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)

            # Handle JSON fields that might be strings or already dicts
            for field in ['conditions', 'actions', 'trigger_config']:
                value = workflow.get(field)
                if value:
                    if isinstance(value, str):
                        try:
                            workflow[field] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            workflow[field] = {} if field != 'actions' else []
                    elif isinstance(value, dict) or isinstance(value, list):
                        workflow[field] = value
                    else:
                        workflow[field] = {} if field != 'actions' else []
                else:
                    workflow[field] = {} if field != 'actions' else []

            workflows.append(workflow)
        
        return {'workflows': workflows}
        
    except Exception as e:
        logger.error(f"Error fetching workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    trigger_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manually trigger workflow execution"""
    try:
        engine = AutomationEngine(db)
        
        # Trigger workflow asynchronously
        execution_id = await engine.trigger_workflow(workflow_id, trigger_data)
        
        if execution_id:
            return {
                'execution': {
                    'id': execution_id,
                    'workflow_id': workflow_id,
                    'status': 'started'
                }
            }
        else:
            return {
                'message': 'Workflow conditions not met',
                'workflow_id': workflow_id
            }
            
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflows/{workflow_id}/executions")
async def get_workflow_executions(
    workflow_id: str,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get execution history for a workflow"""
    try:
        query = """
        SELECT 
            we.*,
            COUNT(ws.id) as total_steps,
            SUM(CASE WHEN ws.status = 'completed' THEN 1 ELSE 0 END) as completed_steps,
            SUM(CASE WHEN ws.status = 'failed' THEN 1 ELSE 0 END) as failed_steps
        FROM workflow_executions we
        LEFT JOIN workflow_steps ws ON we.id = ws.execution_id
        WHERE we.workflow_id = :workflow_id
        """
        
        params = {'workflow_id': workflow_id}
        
        if status:
            query += " AND we.status = :status"
            params['status'] = status
            
        query += """
        GROUP BY we.id
        ORDER BY we.started_at DESC
        LIMIT :limit OFFSET :skip
        """
        
        params['limit'] = limit
        params['skip'] = skip
        
        result = db.execute(text(query), params)
        executions = []
        
        for row in result:
            execution = dict(row)
            execution['trigger_data'] = json.loads(execution['trigger_data']) if execution['trigger_data'] else {}
            execution['context_data'] = json.loads(execution['context_data']) if execution['context_data'] else {}
            executions.append(execution)
        
        return {'executions': executions}
        
    except Exception as e:
        logger.error(f"Error fetching executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions/{execution_id}/steps")
async def get_execution_steps(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed steps for a workflow execution"""
    try:
        query = """
        SELECT * FROM workflow_steps
        WHERE execution_id = :execution_id
        ORDER BY step_number
        """
        
        result = db.execute(text(query), {'execution_id': execution_id})
        steps = []
        
        for row in result:
            step = dict(row)
            step['input_data'] = json.loads(step['input_data']) if step['input_data'] else {}
            step['output_data'] = json.loads(step['output_data']) if step['output_data'] else {}
            steps.append(step)
        
        return {'steps': steps}
        
    except Exception as e:
        logger.error(f"Error fetching execution steps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AUTOMATION RULES
# ============================================================================

@router.post("/automation-rules")
async def create_automation_rule(
    rule: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new automation rule"""
    try:
        rule_id = str(uuid4())
        
        query = """
        INSERT INTO automation_rules (
            id, name, description, rule_type,
            entity_type, conditions, actions,
            is_active, priority
        ) VALUES (
            :id, :name, :description, :rule_type,
            :entity_type, :conditions, :actions,
            :is_active, :priority
        )
        """
        
        db.execute(text(query), {
            'id': rule_id,
            'name': rule['name'],
            'description': rule.get('description'),
            'rule_type': rule.get('rule_type', 'notification'),
            'entity_type': rule['entity_type'],
            'conditions': json.dumps(rule['conditions']),
            'actions': json.dumps(rule['actions']),
            'is_active': rule.get('is_active', True),
            'priority': rule.get('priority', 100)
        })
        
        db.commit()
        
        return {
            'rule': {
                'id': rule_id,
                'name': rule['name'],
                'status': 'created'
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating automation rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/automation-rules")
async def get_automation_rules(
    entity_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get automation rules"""
    try:
        query = """
        SELECT * FROM automation_rules
        WHERE 1=1
        """
        
        params = {}
        
        if entity_type:
            query += " AND entity_type = :entity_type"
            params['entity_type'] = entity_type
            
        if is_active is not None:
            query += " AND is_active = :is_active"
            params['is_active'] = is_active
            
        query += " ORDER BY priority, created_at DESC"
        
        result = db.execute(text(query), params)
        rules = []
        
        for row in result:
            rule = dict(row)
            rule['conditions'] = json.loads(rule['conditions']) if rule['conditions'] else {}
            rule['actions'] = json.loads(rule['actions']) if rule['actions'] else []
            rules.append(rule)
        
        return {'rules': rules}
        
    except Exception as e:
        logger.error(f"Error fetching automation rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/automation-rules/process")
async def process_entity_rules(
    entity_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process automation rules for an entity"""
    try:
        engine = RuleEngine(db)
        
        # Process rules asynchronously
        background_tasks.add_task(
            engine.process_entity,
            entity_data['entity_type'],
            entity_data['entity_id'],
            entity_data.get('event', 'updated')
        )
        
        return {
            'message': 'Rules processing initiated',
            'entity_type': entity_data['entity_type'],
            'entity_id': entity_data['entity_id']
        }
        
    except Exception as e:
        logger.error(f"Error processing rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# NOTIFICATION MANAGEMENT
# ============================================================================

@router.post("/notifications/send")
async def send_notification(
    notification: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send a notification"""
    try:
        service = NotificationService(db)
        
        # Queue notification
        query = """
        INSERT INTO notification_queue (
            recipient_email, recipient_phone,
            notification_type, subject, message,
            data, status, scheduled_for
        ) VALUES (
            :recipient_email, :recipient_phone,
            :notification_type, :subject, :message,
            :data, 'pending', NOW()
        ) RETURNING id
        """
        
        result = db.execute(text(query), {
            'recipient_email': notification.get('email'),
            'recipient_phone': notification.get('phone'),
            'notification_type': notification['type'],
            'subject': notification.get('subject'),
            'message': notification['message'],
            'data': json.dumps(notification.get('data', {}))
        })
        
        notification_id = result.scalar()
        db.commit()
        
        # Process immediately in background
        background_tasks.add_task(service.process_queue)
        
        return {
            'notification': {
                'id': str(notification_id),
                'status': 'queued'
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications/queue")
async def get_notification_queue(
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get notification queue status"""
    try:
        query = """
        SELECT * FROM notification_queue
        WHERE 1=1
        """
        
        params = {}
        
        if status:
            query += " AND status = :status"
            params['status'] = status
            
        query += " ORDER BY scheduled_for DESC LIMIT :limit"
        params['limit'] = limit
        
        result = db.execute(text(query), params)
        notifications = [dict(row) for row in result]
        
        # Get summary
        summary_query = """
        SELECT 
            status,
            COUNT(*) as count
        FROM notification_queue
        WHERE created_at >= CURRENT_DATE
        GROUP BY status
        """
        
        summary_result = db.execute(text(summary_query))
        summary = {row['status']: row['count'] for row in summary_result}
        
        return {
            'notifications': notifications,
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Error fetching notification queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CAMPAIGN MANAGEMENT
# ============================================================================

@router.post("/campaigns")
async def create_campaign(
    campaign: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a nurture campaign"""
    try:
        campaign_id = str(uuid4())
        
        query = """
        INSERT INTO nurture_campaigns (
            id, name, description,
            target_criteria, email_sequence,
            is_active
        ) VALUES (
            :id, :name, :description,
            :target_criteria, :email_sequence,
            :is_active
        )
        """
        
        db.execute(text(query), {
            'id': campaign_id,
            'name': campaign['name'],
            'description': campaign.get('description'),
            'target_criteria': json.dumps(campaign.get('target_criteria', {})),
            'email_sequence': json.dumps(campaign['email_sequence']),
            'is_active': campaign.get('is_active', True)
        })
        
        db.commit()
        
        return {
            'campaign': {
                'id': campaign_id,
                'name': campaign['name'],
                'status': 'created'
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/campaigns/{campaign_id}/enroll")
async def enroll_in_campaign(
    campaign_id: str,
    enrollment: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Enroll leads in a campaign"""
    try:
        lead_ids = enrollment.get('lead_ids', [])
        enrolled_count = 0
        
        for lead_id in lead_ids:
            # Check if already enrolled
            check_query = """
            SELECT id FROM campaign_enrollments
            WHERE campaign_id = :campaign_id AND lead_id = :lead_id
            """
            
            existing = db.execute(text(check_query), {
                'campaign_id': campaign_id,
                'lead_id': lead_id
            }).fetchone()
            
            if not existing:
                # Enroll lead
                enroll_query = """
                INSERT INTO campaign_enrollments (
                    campaign_id, lead_id, status
                ) VALUES (
                    :campaign_id, :lead_id, 'active'
                )
                """
                
                db.execute(text(enroll_query), {
                    'campaign_id': campaign_id,
                    'lead_id': lead_id
                })
                
                enrolled_count += 1
        
        # Update campaign stats
        update_query = """
        UPDATE nurture_campaigns
        SET leads_enrolled = leads_enrolled + :count,
            updated_at = NOW()
        WHERE id = :campaign_id
        """
        
        db.execute(text(update_query), {
            'campaign_id': campaign_id,
            'count': enrolled_count
        })
        
        db.commit()
        
        return {
            'campaign_id': campaign_id,
            'enrolled': enrolled_count,
            'total_requested': len(lead_ids)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error enrolling in campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# TEMPLATE MANAGEMENT
# ============================================================================

@router.post("/templates/email")
async def create_email_template(
    template: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create an email template"""
    try:
        template_id = str(uuid4())
        
        query = """
        INSERT INTO email_templates (
            id, name, template_key, description,
            subject, html_body, text_body,
            available_variables, is_active
        ) VALUES (
            :id, :name, :template_key, :description,
            :subject, :html_body, :text_body,
            :available_variables, :is_active
        )
        """
        
        db.execute(text(query), {
            'id': template_id,
            'name': template['name'],
            'template_key': template['template_key'],
            'description': template.get('description'),
            'subject': template['subject'],
            'html_body': template.get('html_body'),
            'text_body': template.get('text_body'),
            'available_variables': json.dumps(template.get('available_variables', [])),
            'is_active': template.get('is_active', True)
        })
        
        db.commit()
        
        return {
            'template': {
                'id': template_id,
                'name': template['name'],
                'template_key': template['template_key']
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating email template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/email")
async def get_email_templates(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get email templates"""
    try:
        query = "SELECT * FROM email_templates WHERE 1=1"
        params = {}
        
        if is_active is not None:
            query += " AND is_active = :is_active"
            params['is_active'] = is_active
            
        query += " ORDER BY name"
        
        result = db.execute(text(query), params)
        templates = []
        
        for row in result:
            template = dict(row)
            template['available_variables'] = json.loads(template['available_variables']) if template['available_variables'] else []
            templates.append(template)
        
        return {'templates': templates}
        
    except Exception as e:
        logger.error(f"Error fetching email templates: {e} RETURNING * RETURNING * RETURNING * RETURNING * RETURNING *")
        raise HTTPException(status_code=500, detail=str(e))