"""
Gumroad Revenue Pipeline
Handles Gumroad webhooks, recording sales, and triggering automations.
"""

import os
import hmac
import hashlib
import json
import logging
import httpx
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks

from database import get_db_async

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Gumroad Revenue"])

# Configuration
GUMROAD_WEBHOOK_SECRET = os.getenv("GUMROAD_WEBHOOK_SECRET", "")
CONVERTKIT_API_KEY = os.getenv("CONVERTKIT_API_KEY", "")
CONVERTKIT_FORM_ID = os.getenv("CONVERTKIT_FORM_ID", "8419539")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "support@brainops.io")

# Product Mapping (Ported from Node.js)
PRODUCT_MAPPING = {
    # AI Prompt Packs
    'GR-ROOFINT': {
        'name': 'Commercial Roofing Intelligence Bundle',
        'convertkit_tag': 'roofing-intelligence-buyer'
    },
    'GR-PMACC': {
        'name': 'AI-Enhanced Project Management Accelerator',
        'convertkit_tag': 'pm-accelerator-buyer'
    },
    'GR-LAUNCH': {
        'name': 'Digital Product Launch Optimizer',
        'convertkit_tag': 'launch-optimizer-buyer'
    },
    # Automation Packs
    'GR-ONBOARD': {
        'name': 'Intelligent Client Onboarding System',
        'convertkit_tag': 'onboarding-system-buyer'
    },
    'GR-CONTENT': {
        'name': 'AI-Powered Content Production Pipeline',
        'convertkit_tag': 'content-pipeline-buyer'
    },
    'GR-ROOFVAL': {
        'name': 'Commercial Roofing Estimation Validator',
        'convertkit_tag': 'roofing-validator-buyer'
    },
    # Code Starter Kits
    'GR-ERP-START': {
        'name': 'SaaS ERP Starter Kit',
        'convertkit_tag': 'erp-starter-buyer'
    },
    'GR-AI-ORCH': {
        'name': 'BrainOps AI Orchestrator Framework',
        'convertkit_tag': 'ai-orchestrator-buyer'
    },
    'GR-UI-KIT': {
        'name': 'Modern Command Center UI Kit',
        'convertkit_tag': 'ui-kit-buyer'
    },
    # Ultimate Bundle
    'GR-ULTIMATE': {
        'name': 'Ultimate All-Access Bundle',
        'convertkit_tag': 'ultimate-bundle-buyer'
    }
}

def _parse_price_dollars(data: dict[str, Any]) -> Optional[Decimal]:
    raw = data.get("price")
    if raw is None:
        return None
    try:
        # Gumroad webhooks typically provide cents as a string/integer.
        cents = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError):
        return None
    # Store dollars in DB; keep raw in metadata as the source of truth.
    return (cents / Decimal("100")).quantize(Decimal("0.01"))


def _verify_gumroad_signature(payload: bytes, signature: Optional[str]) -> None:
    # Always require signature verification when a secret is configured.
    if not GUMROAD_WEBHOOK_SECRET:
        logger.error("GUMROAD_WEBHOOK_SECRET is not configured; rejecting webhook")
        raise HTTPException(status_code=503, detail="Webhook secret not configured")

    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")

    expected_sig = hmac.new(
        GUMROAD_WEBHOOK_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        raise HTTPException(status_code=401, detail="Invalid signature")


async def add_to_convertkit(
    email: str,
    first_name: str,
    last_name: str,
    product_code: str,
    price: Optional[Decimal],
):
    """Add subscriber to ConvertKit"""
    if not CONVERTKIT_API_KEY:
        logger.warning("ConvertKit API key missing")
        return

    try:
        async with httpx.AsyncClient() as client:
            # Subscribe to form
            await client.post(
                f"https://api.convertkit.com/v3/forms/{CONVERTKIT_FORM_ID}/subscribe",
                json={
                    "api_key": CONVERTKIT_API_KEY,
                    "email": email,
                    "first_name": first_name,
                    "fields": {
                        "last_name": last_name,
                        "gumroad_customer": "true",
                        "last_purchase": datetime.now(timezone.utc).isoformat(),
                        "purchased_products": product_code,
                        "total_spent": float(price) if price is not None else None,
                    }
                }
            )

            # Add tag (lookup by name -> subscribe by id)
            product = PRODUCT_MAPPING.get(product_code)
            tag_name = (product or {}).get("convertkit_tag")
            if tag_name:
                tags_resp = await client.get(
                    "https://api.convertkit.com/v3/tags",
                    params={"api_key": CONVERTKIT_API_KEY},
                )
                tags = (tags_resp.json() or {}).get("tags") or []
                tag_id = None
                for tag in tags:
                    if str(tag.get("name", "")).strip().lower() == str(tag_name).strip().lower():
                        tag_id = tag.get("id")
                        break
                if tag_id:
                    await client.post(
                        f"https://api.convertkit.com/v3/tags/{tag_id}/subscribe",
                        json={"api_key": CONVERTKIT_API_KEY, "email": email},
                    )
                else:
                    logger.warning("ConvertKit tag not found: %s", tag_name)

    except Exception as e:
        logger.error(f"ConvertKit error: {e}")

async def send_purchase_email(email: str, name: str, product_name: str, download_url: str):
    """Send transactional email via SendGrid"""
    if not SENDGRID_API_KEY:
        logger.warning("SendGrid API key missing")
        return

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {SENDGRID_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{"to": [{"email": email}]}],
                    "from": {"email": SENDGRID_FROM_EMAIL, "name": "BrainOps Team"},
                    "subject": f"Your {product_name} is ready!",
                    "content": [{
                        "type": "text/html",
                        "value": f"""
                            <h2>Hi {name},</h2>
                            <p>Thank you for purchasing <strong>{product_name}</strong>!</p>
                            <p><a href="{download_url}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download Your Product</a></p>
                            <p>If you have any questions, reply to this email.</p>
                            <p>Best,<br>BrainOps Team</p>
                        """
                    }]
                }
            )
    except Exception as e:
        logger.error(f"SendGrid error: {e}")

@router.post("/webhook/gumroad")
async def gumroad_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle Gumroad sales webhook"""
    
    # 1. Verify Signature
    payload = await request.body()
    signature = request.headers.get("x-gumroad-signature")
    _verify_gumroad_signature(payload, signature)

    # 2. Parse Data
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            data = await request.json()  # type: ignore[assignment]
        else:
            form_data = await request.form()
            data = dict(form_data)
            
        email = data.get("email")
        full_name = data.get("full_name", "")
        product_name = data.get("product_name")
        product_permalink = data.get("product_permalink")
        sale_id = data.get("sale_id")
        currency = data.get("currency", "USD")
        download_url = data.get("url") or data.get("product_url") or data.get("download_url") or "https://gumroad.com/library"
        price = _parse_price_dollars(data)
        is_test = str(data.get("test", "")).lower() in {"1", "true", "yes"}

        if not email or not product_name:
             # Just a ping or test
             return {"status": "ignored", "reason": "missing_fields"}

    except Exception as e:
        logger.error(f"Failed to parse webhook: {e}")
        raise HTTPException(status_code=400, detail="Bad request")

    # 3. Identify Product
    product_code = (product_permalink or "").upper()
    if not product_code:
        for code in PRODUCT_MAPPING:
            if code in product_name:
                product_code = code
                break
    
    mapped_product = PRODUCT_MAPPING.get(product_code, {"name": product_name})
    
    # 4. Record Sale (AsyncPG). If we cannot persist, return 500 so Gumroad retries.
    try:
        db = await get_db_async()
        pool = db.pool
        async with pool.acquire() as conn:
            inserted = await conn.fetchval("""
                INSERT INTO gumroad_sales (
                    sale_id, email, customer_name, product_code, product_name,
                    price, currency, sale_timestamp, convertkit_synced,
                    stripe_synced, sendgrid_sent, metadata, is_test
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8, $9, $10, $11::jsonb, $12)
                ON CONFLICT (sale_id) DO NOTHING
                RETURNING sale_id
            """,
            sale_id, email, full_name, product_code, product_name, 
            float(price) if price is not None else None,
            currency,
            False,
            False,
            False,
            json.dumps(data),
            is_test,
            )
            if inserted:
                logger.info("Recorded Gumroad sale: %s", sale_id)
            else:
                # Idempotent behavior: do not re-trigger automations for duplicates.
                return {"status": "duplicate", "sale_id": sale_id}

    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
        
    # 5. Trigger Automations
    name_parts = full_name.split(" ")
    first_name = name_parts[0]
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    background_tasks.add_task(add_to_convertkit, email, first_name, last_name, product_code, price)
    background_tasks.add_task(send_purchase_email, email, first_name, mapped_product["name"], download_url)

    return {"status": "success", "sale_id": sale_id}
