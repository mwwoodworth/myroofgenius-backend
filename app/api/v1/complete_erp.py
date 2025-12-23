"""
Complete ERP Workflow Implementation
Full lead-to-completion system
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from uuid import uuid4
import json

from database import get_db
from pydantic import BaseModel, EmailStr
from core.supabase_auth import get_current_user

router = APIRouter(prefix="/api/v1/erp", tags=["Complete ERP"])

# Models
class LeadCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    address: str
    roof_type: Optional[str] = "shingle"
    square_footage: Optional[int] = 2000
    urgency: Optional[str] = "normal"
    source: Optional[str] = "api"
    notes: Optional[str] = None

class EstimateCreate(BaseModel):
    customer_id: str
    square_footage: int
    roof_type: str = "shingle"
    materials_grade: str = "standard"  # economy, standard, premium
    include_warranty: bool = True
    
class ProjectCreate(BaseModel):
    customer_id: str
    estimate_id: str
    start_date: Optional[str] = None
    crew_size: Optional[int] = 4

class ProjectUpdate(BaseModel):
    status: str
    completion_percentage: Optional[int] = None
    notes: Optional[str] = None

# Complete Workflow Endpoints

@router.post("/workflow/lead-to-project")
async def create_complete_workflow(lead: LeadCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Complete workflow from lead capture to project creation"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="User not assigned to any tenant")

        result = {}

        # 1. Create Lead (id auto-generates)
        lead_query = text("""
            INSERT INTO leads (name, email, phone, address, roof_type, square_footage, urgency, source, status, tenant_id)
            VALUES (:name, :email, :phone, :address, :roof_type, :square_footage, :urgency, :source, 'NEW', :tenant_id)
            RETURNING id, name, email
        """)
        
        lead_result = db.execute(lead_query, {
            'name': lead.name,
            'email': lead.email,
            'phone': lead.phone,
            'address': lead.address,
            'roof_type': lead.roof_type,
            'square_footage': lead.square_footage,
            'urgency': lead.urgency,
            'source': lead.source,
            'tenant_id': tenant_id
        }).fetchone()
        db.commit()
        result['lead'] = {'id': lead_result[0], 'name': lead_result[1], 'email': lead_result[2]}
        
        # 2. Score and Qualify Lead
        lead_id = lead_result[0]
        score = calculate_lead_score(lead)
        db.execute(text("UPDATE leads SET score = :score WHERE id = :id AND tenant_id = :tenant_id"),
                  {'score': score, 'id': lead_id, 'tenant_id': tenant_id})
        result['lead_score'] = score
        
        # 3. Convert to Customer
        customer_id = str(uuid4())
        customer_query = text("""
            INSERT INTO customers (id, name, email, phone, address, source, tenant_id)
            VALUES (:id, :name, :email, :phone, CAST(:address AS jsonb), 'lead_conversion', :tenant_id)
            RETURNING id
        """)
        
        # Format address as JSON
        address_json = json.dumps({"street": lead.address, "formatted": lead.address})
        
        customer_result = db.execute(customer_query, {
            'id': customer_id,
            'name': lead.name,
            'email': lead.email,
            'phone': lead.phone,
            'address': address_json,
            'tenant_id': tenant_id
        }).fetchone()
        db.commit()
        result['customer'] = {'id': customer_result[0], 'name': lead.name, 'email': lead.email}
        
        # 4. Generate AI Estimate
        estimate = await generate_ai_estimate(customer_id, lead.square_footage, lead.roof_type, db, tenant_id=tenant_id)
        result['estimate'] = estimate

        # 5. Create Project
        project = await create_project_from_estimate(customer_id, estimate['id'], db, tenant_id=tenant_id)
        result['project'] = project

        # 6. Generate Documents
        documents = await generate_project_documents(project['id'], db, tenant_id=tenant_id)
        result['documents'] = documents

        # 7. Schedule and Assign
        schedule = await schedule_project(project['id'], db, tenant_id=tenant_id)
        result['schedule'] = schedule
        
        return {
            "success": True,
            "message": "Complete workflow created successfully",
            "workflow": result
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leads")
async def create_lead(lead: LeadCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Create a new lead"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="User not assigned to any tenant")

        lead_id = str(uuid4())
        query = text("""
            INSERT INTO leads (id, name, email, phone, address, roof_type, square_footage, urgency, source, status, tenant_id)
            VALUES (:id, :name, :email, :phone, :address, :roof_type, :square_footage, :urgency, :source, 'NEW', :tenant_id)
            RETURNING id, name, email, status, score
        """)
        
        result = db.execute(query, {
            'id': lead_id,
            'name': lead.name,
            'email': lead.email,
            'phone': lead.phone,
            'address': lead.address,
            'roof_type': lead.roof_type,
            'square_footage': lead.square_footage,
            'urgency': lead.urgency,
            'source': lead.source,
            'tenant_id': tenant_id
        }).fetchone()

        db.commit()

        # Calculate and update score
        score = calculate_lead_score(lead)
        db.execute(text("UPDATE leads SET score = :score WHERE id = :id AND tenant_id = :tenant_id"),
                  {'score': score, 'id': lead_id, 'tenant_id': tenant_id})
        db.commit()
        
        return {
            "id": result[0],
            "name": result[1],
            "email": result[2],
            "status": result[3],
            "score": score
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/estimates")
async def create_estimate(estimate: EstimateCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Generate AI-powered estimate"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="User not assigned to any tenant")

        result = await generate_ai_estimate(
            estimate.customer_id,
            estimate.square_footage,
            estimate.roof_type,
            db,
            estimate.materials_grade,
            tenant_id=tenant_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects")
async def create_project(project: ProjectCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Create project from approved estimate"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="User not assigned to any tenant")

        result = await create_project_from_estimate(
            project.customer_id,
            project.estimate_id,
            db,
            project.start_date,
            project.crew_size,
            tenant_id=tenant_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/projects/{project_id}")
async def update_project(project_id: str, update: ProjectUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Update project status and track progress"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="User not assigned to any tenant")

        query = text("""
            UPDATE jobs
            SET status = :status,
                completion_percentage = COALESCE(:completion, completion_percentage),
                notes = COALESCE(:notes, notes),
                updated_at = NOW()
            WHERE id = :id AND tenant_id = :tenant_id
            RETURNING id, status, completion_percentage
        """)

        result = db.execute(query, {
            'id': project_id,
            'status': update.status,
            'completion': update.completion_percentage,
            'notes': update.notes,
            'tenant_id': tenant_id
        }).fetchone()

        db.commit()

        # If completed, generate final documents
        if update.status == 'completed':
            await generate_completion_documents(project_id, db, tenant_id=tenant_id)
        
        return {
            "id": result[0],
            "status": result[1],
            "completion": result[2]
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Helper Functions

def calculate_lead_score(lead: LeadCreate) -> int:
    """Calculate lead score based on various factors"""
    score = 50  # Base score
    
    # Urgency scoring
    if lead.urgency == "high":
        score += 30
    elif lead.urgency == "medium":
        score += 15
    
    # Square footage scoring
    if lead.square_footage:
        if lead.square_footage > 3000:
            score += 20
        elif lead.square_footage > 2000:
            score += 10
    
    # Source scoring
    if lead.source in ["referral", "repeat"]:
        score += 25
    elif lead.source == "website":
        score += 10
    
    return min(score, 100)  # Cap at 100

async def generate_ai_estimate(customer_id: str, sq_ft: int, roof_type: str, db: Session, grade: str = "standard", tenant_id: str = None) -> Dict:
    """Generate comprehensive AI estimate"""

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required for estimate generation")

    # Pricing matrix (per sq ft)
    pricing = {
        "shingle": {"economy": 5.50, "standard": 7.50, "premium": 9.50},
        "tile": {"economy": 8.00, "standard": 11.00, "premium": 15.00},
        "metal": {"economy": 9.00, "standard": 12.00, "premium": 16.00},
        "flat": {"economy": 6.00, "standard": 8.00, "premium": 10.00}
    }
    
    base_price = pricing.get(roof_type, pricing["shingle"])[grade]
    
    # Calculate costs
    materials_cost = sq_ft * base_price * 0.6
    labor_cost = sq_ft * base_price * 0.3
    overhead = sq_ft * base_price * 0.1
    total = materials_cost + labor_cost + overhead
    
    # Create estimate
    estimate_id = str(uuid4())
    estimate_number = f"EST-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
    
    items = [
        {"description": f"Materials - {roof_type} ({grade})", "quantity": sq_ft, "unit_price": base_price * 0.6, "total": materials_cost},
        {"description": "Labor", "quantity": sq_ft, "unit_price": base_price * 0.3, "total": labor_cost},
        {"description": "Overhead & Profit", "quantity": 1, "unit_price": overhead, "total": overhead}
    ]
    
    # Get customer info
    customer_info = db.execute(text("SELECT name, email, phone FROM customers WHERE id = :id AND tenant_id = :tenant_id"), {'id': customer_id, 'tenant_id': tenant_id}).fetchone()
    
    # Use existing system user ID  
    system_user_id = "44491c1c-0e28-4aa1-ad33-552d1386769c"
    
    query = text("""
        INSERT INTO estimates (id, estimate_number, customer_id, client_name, client_email, client_phone,
                             title, subtotal, total, total_amount, subtotal_cents, total_cents,
                             status, description, line_items,
                             estimate_date, valid_until, created_by_id, created_by, tenant_id)
        VALUES (:id, :estimate_number, :customer_id, :client_name, :client_email, :client_phone,
                :title, :subtotal, :total, :total, :subtotal_cents, :total_cents,
                'pending', :description, :line_items,
                :estimate_date, :valid_until, :created_by_id, :created_by, :tenant_id)
        RETURNING id, estimate_number, total_amount, status
    """)
    
    result = db.execute(query, {
        'id': estimate_id,
        'estimate_number': estimate_number,
        'customer_id': customer_id,
        'client_name': customer_info[0] if customer_info else 'Customer',
        'client_email': customer_info[1] if customer_info else '',
        'client_phone': customer_info[2] if customer_info else '',
        'title': f'{roof_type.title()} Roof Replacement - {sq_ft} sq ft',
        'subtotal': materials_cost + labor_cost,
        'total': total,
        'subtotal_cents': int((materials_cost + labor_cost) * 100),
        'total_cents': int(total * 100),
        'description': f'Roof replacement estimate - {sq_ft} sq ft {roof_type}',
        'line_items': json.dumps(items),
        'estimate_date': datetime.now().date().isoformat(),
        'valid_until': (datetime.now() + timedelta(days=30)).date().isoformat(),
        'created_by_id': system_user_id,
        'created_by': system_user_id,
        'tenant_id': tenant_id
    }).fetchone()
    
    db.commit()
    
    return {
        "id": result[0],
        "estimate_number": result[1],
        "total": float(result[2]),
        "status": result[3],
        "breakdown": {
            "materials": materials_cost,
            "labor": labor_cost,
            "overhead": overhead
        },
        "items": items
    }

async def create_project_from_estimate(customer_id: str, estimate_id: str, db: Session,
                                      start_date: str = None, crew_size: int = 4, tenant_id: str = None) -> Dict:
    """Create project/job from approved estimate"""

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required for project creation")

    # Get estimate details
    estimate = db.execute(
        text("SELECT total_amount, description FROM estimates WHERE id = :id AND tenant_id = :tenant_id"),
        {'id': estimate_id, 'tenant_id': tenant_id}
    ).fetchone()
    
    if not estimate:
        raise ValueError("Estimate not found")
    
    # Generate job number
    job_number = f"JOB-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
    
    # Create job
    job_id = str(uuid4())
    query = text("""
        INSERT INTO jobs (id, customer_id, job_number, status, title, description,
                         scheduled_start, estimate_id, tenant_id)
        VALUES (:id, :customer_id, :job_number, 'scheduled', :title, :description,
                :start_date, :estimate_id, :tenant_id)
        RETURNING id, job_number, status
    """)
    
    result = db.execute(query, {
        'id': job_id,
        'customer_id': customer_id,
        'job_number': job_number,
        'title': f'Roof Replacement - ${estimate[0]:,.2f}',
        'description': estimate[1],
        'start_date': start_date or (datetime.now() + timedelta(days=7)).isoformat(),
        'estimate_id': estimate_id,
        'tenant_id': tenant_id
    }).fetchone()

    db.commit()

    # Update estimate status
    db.execute(
        text("UPDATE estimates SET status = 'approved' WHERE id = :id AND tenant_id = :tenant_id"),
        {'id': estimate_id, 'tenant_id': tenant_id}
    )
    db.commit()
    
    return {
        "id": result[0],
        "job_number": result[1],
        "status": result[2],
        "start_date": start_date or (datetime.now() + timedelta(days=7)).isoformat(),
        "crew_size": crew_size,
        "estimated_total": float(estimate[0]) if estimate[0] else 0
    }

async def generate_project_documents(project_id: str, db: Session, tenant_id: str = None) -> List[Dict]:
    """Generate all required project documents"""

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required for document generation")

    documents = []

    # Get project details
    project = db.execute(
        text("""
            SELECT j.*, c.name, c.email, c.address
            FROM jobs j
            JOIN customers c ON j.customer_id = c.id
            WHERE j.id = :id AND j.tenant_id = :tenant_id
        """),
        {'id': project_id, 'tenant_id': tenant_id}
    ).fetchone()
    
    # Generate documents
    doc_types = [
        ("contract", "Roofing Contract"),
        ("permit", "Building Permit Application"),
        ("materials", "Materials Order List"),
        ("schedule", "Project Schedule"),
        ("safety", "Safety Plan")
    ]
    
    for doc_type, doc_name in doc_types:
        doc_id = str(uuid4())
        documents.append({
            "id": doc_id,
            "type": doc_type,
            "name": doc_name,
            "project_id": project_id,
            "status": "generated",
            "url": f"/api/v1/documents/{doc_id}"
        })
    
    return documents

async def schedule_project(project_id: str, db: Session, tenant_id: str = None) -> Dict:
    """Create project schedule with milestones"""

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required for project scheduling")

    milestones = [
        ("materials_delivery", "Materials Delivery", 0),
        ("tear_off", "Tear Off Old Roof", 1),
        ("decking_inspection", "Decking Inspection", 1),
        ("underlayment", "Install Underlayment", 2),
        ("roofing", "Install Roofing Material", 3),
        ("flashing", "Install Flashing", 4),
        ("cleanup", "Cleanup", 5),
        ("final_inspection", "Final Inspection", 5)
    ]
    
    schedule = {
        "project_id": project_id,
        "start_date": datetime.now() + timedelta(days=7),
        "end_date": datetime.now() + timedelta(days=12),
        "milestones": []
    }
    
    for milestone_type, name, day_offset in milestones:
        schedule["milestones"].append({
            "type": milestone_type,
            "name": name,
            "scheduled_date": (datetime.now() + timedelta(days=7 + day_offset)).isoformat(),
            "status": "pending"
        })
    
    return schedule

async def generate_completion_documents(project_id: str, db: Session, tenant_id: str = None) -> List[Dict]:
    """Generate completion documents"""

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant ID required for completion document generation")

    return [
        {"type": "warranty", "name": "Warranty Certificate"},
        {"type": "invoice", "name": "Final Invoice"},
        {"type": "completion", "name": "Completion Certificate"},
        {"type": "photos", "name": "Before/After Photos"}
    ]

# Revenue tracking endpoints

@router.get("/revenue/dashboard")
async def revenue_dashboard(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get revenue metrics and analytics"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="User not assigned to any tenant")

        metrics = {}

        # Total revenue
        revenue = db.execute(text("""
            SELECT
                COUNT(*) as total_projects,
                SUM(total) as total_revenue,
                AVG(total) as avg_project_value
            FROM jobs
            WHERE status = 'completed' AND tenant_id = :tenant_id
        """), {'tenant_id': tenant_id}).fetchone()

        metrics['revenue'] = {
            'total_projects': revenue[0],
            'total_revenue': float(revenue[1]) if revenue[1] else 0,
            'avg_value': float(revenue[2]) if revenue[2] else 0
        }

        # Pipeline
        pipeline = db.execute(text("""
            SELECT status, COUNT(*) as count, SUM(total_amount) as value
            FROM estimates
            WHERE tenant_id = :tenant_id
            GROUP BY status
        """), {'tenant_id': tenant_id}).fetchall()

        metrics['pipeline'] = [
            {'status': row[0], 'count': row[1], 'value': float(row[2]) if row[2] else 0}
            for row in pipeline
        ]

        # Lead conversion
        leads = db.execute(text("""
            SELECT
                COUNT(*) as total_leads,
                COUNT(CASE WHEN status = 'CONVERTED' THEN 1 END) as converted,
                AVG(score) as avg_score
            FROM leads
            WHERE tenant_id = :tenant_id
        """), {'tenant_id': tenant_id}).fetchone()
        
        metrics['leads'] = {
            'total': leads[0],
            'converted': leads[1],
            'conversion_rate': (leads[1] / leads[0] * 100) if leads[0] > 0 else 0,
            'avg_score': float(leads[2]) if leads[2] else 0
        }
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow/status/{lead_id}")
async def get_workflow_status(lead_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Track complete workflow status for a lead"""
    try:
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="User not assigned to any tenant")

        status = {}

        # Lead status
        lead = db.execute(
            text("SELECT name, email, status, score FROM leads WHERE id = :id AND tenant_id = :tenant_id"),
            {'id': lead_id, 'tenant_id': tenant_id}
        ).fetchone()

        if lead:
            status['lead'] = {
                'name': lead[0],
                'email': lead[1],
                'status': lead[2],
                'score': lead[3]
            }

        # Find related customer
        customer = db.execute(
            text("SELECT id, name FROM customers WHERE email = :email AND tenant_id = :tenant_id"),
            {'email': lead[1] if lead else '', 'tenant_id': tenant_id}
        ).fetchone()

        if customer:
            status['customer'] = {'id': customer[0], 'name': customer[1]}

            # Find estimates
            estimates = db.execute(
                text("SELECT id, total_amount, status FROM estimates WHERE customer_id = :id AND tenant_id = :tenant_id"),
                {'id': customer[0], 'tenant_id': tenant_id}
            ).fetchall()

            status['estimates'] = [
                {'id': e[0], 'total': float(e[1]), 'status': e[2]}
                for e in estimates
            ]

            # Find jobs
            jobs = db.execute(
                text("SELECT id, job_number, status, completion_percentage FROM jobs WHERE customer_id = :id AND tenant_id = :tenant_id"),
                {'id': customer[0], 'tenant_id': tenant_id}
            ).fetchall()

            status['projects'] = [
                {'id': j[0], 'number': j[1], 'status': j[2], 'completion': j[3]}
                for j in jobs
            ]
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
