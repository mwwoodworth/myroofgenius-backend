"""
Public endpoints for MyRoofGenius frontend
No authentication required
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
import logging

from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/erp/public", tags=["Public"])

class EstimateRequest(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: str
    address: str
    roof_size_sqft: float
    roof_type: str
    notes: Optional[str] = None

@router.post("/estimate-request")
def create_public_estimate(request: EstimateRequest, db: Session = Depends(get_db)):
    """Create estimate from public website"""
    try:
        # Calculate estimate based on roof size and type
        price_per_sqft = {
            "shingle": 7.50,
            "metal": 12.00,
            "tile": 15.00,
            "flat": 8.50
        }
        
        base_price = price_per_sqft.get(request.roof_type.lower(), 7.50)
        total = int(request.roof_size_sqft * base_price * 100)  # Convert to cents
        
        # Generate estimate number
        estimate_number = f"EST-{datetime.now().strftime('%Y%m')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create or find customer
        customer_query = """
            SELECT id FROM customers WHERE email = :email
        """
        customer = db.execute(text(customer_query), {"email": request.customer_email}).first()
        
        if not customer:
            # Create new customer
            create_customer = """
                INSERT INTO customers (id, name, email, phone, address, created_at)
                VALUES (:id, :name, :email, :phone, :address, :created_at)
                RETURNING id
            """
            customer_id = str(uuid.uuid4())
            db.execute(text(create_customer), {
                "id": customer_id,
                "name": request.customer_name,
                "email": request.customer_email,
                "phone": request.customer_phone,
                "address": request.address,
                "created_at": datetime.utcnow()
            })
        else:
            customer_id = str(customer.id)
        
        # Create estimate
        estimate_id = str(uuid.uuid4())
        create_estimate = """
            INSERT INTO estimates (
                id, estimate_number, customer_id, 
                total, status, notes, created_at
            ) VALUES (
                :id, :number, :customer_id,
                :total, 'draft', :notes, :created_at
            )
        """
        
        db.execute(text(create_estimate), {
            "id": estimate_id,
            "number": estimate_number,
            "customer_id": customer_id,
            "total": total,
            "notes": f"Roof: {request.roof_type}, Size: {request.roof_size_sqft} sqft. {request.notes or ''}",
            "created_at": datetime.utcnow()
        })
        
        db.commit()
        
        logger.info(f"Created estimate {estimate_number} for {request.customer_email}")
        
        return {
            "id": estimate_id,
            "estimate_number": estimate_number,
            "customer_id": customer_id,
            "total": total,
            "status": "success",
            "message": "Estimate created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating public estimate: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create estimate request")
