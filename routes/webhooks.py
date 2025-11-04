"""
Webhook handlers for external integrations
"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Webhooks"])

@router.post("/revenue/webhook")
async def handle_revenue_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle revenue webhook events"""
    try:
        # Get webhook payload
        payload = await request.json() if request.body else {}
        
        # Log the webhook event
        logger.info(f"Revenue webhook received: {payload.get('type', 'unknown')}")
        
        # Process in background to avoid timeout
        background_tasks.add_task(process_revenue_event, payload)
        
        # Always return success to prevent retries
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        # Still return success to prevent retry loops
        

async def process_revenue_event(payload: Dict[Any, Any]):
    """Process revenue event in background"""
    try:
        event_type = payload.get("type", "unknown")
        
        # Handle different event types
        if event_type == "payment_intent.succeeded":
            logger.info(f"Payment succeeded: {payload.get('id')}")
        elif event_type == "customer.created":
            logger.info(f"Customer created: {payload.get('id')}")
        else:
            logger.info(f"Unhandled event type: {event_type}")
            
    except Exception as e:
        logger.error(f"Error processing revenue event: {e}")

@router.post("/webhooks/stripe")
async def handle_stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        payload = await request.json() if request.body else {}
        logger.info(f"Stripe webhook: {payload.get('type', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        

@router.post("/webhooks/render")
async def handle_render_webhook(request: Request):
    """Handle Render deployment webhooks"""
    try:
        payload = await request.json() if request.body else {}
        logger.info(f"Render webhook: {payload.get('type', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Render webhook error: {e}")
        