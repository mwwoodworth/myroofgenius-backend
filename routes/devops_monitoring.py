"""
DevOps Monitoring Routes for Render and Vercel
Provides observability and webhook endpoints for deployment platforms
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Header
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import os
import json
import httpx
import logging

router = APIRouter(
    prefix="/api/v1",
    tags=["DevOps Monitoring"]
)

logger = logging.getLogger(__name__)

# Configuration
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID")
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
VERCEL_PROJECT_ID = os.getenv("VERCEL_PROJECT_ID")


def _render_configured() -> bool:
    return bool(RENDER_API_KEY and RENDER_SERVICE_ID)


def _vercel_configured() -> bool:
    return bool(VERCEL_TOKEN and VERCEL_PROJECT_ID)

# ============================================================================
# RENDER MONITORING
# ============================================================================

@router.get("/render/status")
async def get_render_status():
    """Get current Render deployment status"""
    try:
        if not _render_configured():
            raise HTTPException(status_code=503, detail="Render API not configured (set RENDER_API_KEY and RENDER_SERVICE_ID).")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}",
                headers={"Authorization": f"Bearer {RENDER_API_KEY}"}
            )
            
            if response.status_code == 200:
                service_data = response.json()
                return {
                    "status": "healthy",
                    "service": {
                        "id": service_data.get("id"),
                        "name": service_data.get("name"),
                        "type": service_data.get("type"),
                        "status": service_data.get("suspended") == False and "active" or "suspended",
                        "url": service_data.get("serviceDetails", {}).get("url"),
                        "region": service_data.get("region"),
                        "created_at": service_data.get("createdAt"),
                        "updated_at": service_data.get("updatedAt")
                    }
                }
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"Render API returned {response.status_code}: {response.text}",
                )
    except Exception as e:
        logger.error(f"Error fetching Render status: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/render/deployments")
async def get_render_deployments(limit: int = 10):
    """Get recent Render deployments"""
    try:
        if not _render_configured():
            raise HTTPException(status_code=503, detail="Render API not configured (set RENDER_API_KEY and RENDER_SERVICE_ID).")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys?limit={limit}",
                headers={"Authorization": f"Bearer {RENDER_API_KEY}"}
            )
            
            if response.status_code == 200:
                deploys = response.json()
                return {
                    "deployments": [
                        {
                            "id": d.get("id"),
                            "status": d.get("status"),
                            "trigger": d.get("trigger"),
                            "commit": d.get("commit", {}).get("id"),
                            "branch": d.get("commit", {}).get("branch"),
                            "created_at": d.get("createdAt"),
                            "finished_at": d.get("finishedAt")
                        }
                        for d in deploys
                    ]
                }
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"Render API returned {response.status_code}: {response.text}",
                )
    except Exception as e:
        logger.error(f"Error fetching Render deployments: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=502, detail=str(e))

@router.post("/webhooks/render")
async def render_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle Render deployment webhooks"""
    try:
        payload = await request.json()
        
        # Log the webhook event
        event_type = payload.get("type", "unknown")
        logger.info(f"Render webhook received: {event_type}")
        
        # Database operations removed - table schema issues
        # Just process the webhook for logging and notifications
        
        # Process based on event type
        if event_type == "deploy.created":
            logger.info(f"New deployment started: {payload.get('deploy', {}).get('id')}")
        elif event_type == "deploy.updated":
            status = payload.get("deploy", {}).get("status")
            logger.info(f"Deployment updated: {status}")
            if status == "live":
                # Deployment successful
                background_tasks.add_task(notify_deployment_success, payload)
        elif event_type == "deploy.canceled":
            logger.warning(f"Deployment canceled: {payload.get('deploy', {}).get('id')}")
        
        return {
            "success": True,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing Render webhook: {e}")
        # Return success even on error to prevent webhook retries
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ============================================================================
# VERCEL MONITORING
# ============================================================================

@router.get("/vercel/status")
async def get_vercel_status():
    """Get Vercel project status"""
    try:
        if not _vercel_configured():
            raise HTTPException(status_code=503, detail="Vercel API not configured (set VERCEL_TOKEN and VERCEL_PROJECT_ID).")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.vercel.com/v9/projects/{VERCEL_PROJECT_ID}",
                headers={"Authorization": f"Bearer {VERCEL_TOKEN}"}
            )
            
            if response.status_code == 200:
                project = response.json()
                return {
                    "status": "healthy",
                    "project": {
                        "id": project.get("id"),
                        "name": project.get("name"),
                        "framework": project.get("framework"),
                        "node_version": project.get("nodeVersion"),
                        "created_at": project.get("createdAt"),
                        "updated_at": project.get("updatedAt")
                    }
                }
            else:
                raise HTTPException(status_code=502, detail=f"Vercel API returned {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Error fetching Vercel status: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/vercel/deployments")
async def get_vercel_deployments(limit: int = 10):
    """Get recent Vercel deployments"""
    try:
        if not _vercel_configured():
            raise HTTPException(status_code=503, detail="Vercel API not configured (set VERCEL_TOKEN and VERCEL_PROJECT_ID).")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.vercel.com/v6/deployments?projectId={VERCEL_PROJECT_ID}&limit={limit}",
                headers={"Authorization": f"Bearer {VERCEL_TOKEN}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "deployments": [
                        {
                            "id": d.get("uid"),
                            "url": d.get("url"),
                            "state": d.get("state"),
                            "ready_state": d.get("readyState"),
                            "created_at": d.get("createdAt"),
                            "building_at": d.get("buildingAt"),
                            "ready": d.get("ready")
                        }
                        for d in data.get("deployments", [])
                    ]
                }
            else:
                raise HTTPException(status_code=502, detail=f"Vercel API returned {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"Error fetching Vercel deployments: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=502, detail=str(e))

@router.post("/webhooks/vercel")
async def vercel_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_vercel_signature: Optional[str] = Header(None)
):
    """Handle Vercel deployment webhooks"""
    try:
        payload = await request.json()
        
        # Log the webhook event
        event_type = payload.get("type", "unknown")
        logger.info(f"Vercel webhook received: {event_type}")
        
        # Store webhook data - DISABLED due to missing column issue
        
        # engine = get_db_engine()
        # with engine.connect() as conn:
        #     conn.execute(text("""
        #         INSERT INTO deployment_events (
        #             platform,
        #             event_type,
        #             payload,
        #             timestamp
        #         ) VALUES (
        #             'vercel',
        #             :event_type,
        #             :payload,
        #             NOW()
        #         )
        #         ON CONFLICT DO NOTHING
        #     """), {
        #         "event_type": event_type,
        #         "payload": json.dumps(payload)
        #     })
        #     conn.commit()
        
        # Process based on event type
        if event_type == "deployment.created":
            logger.info(f"New deployment created: {payload.get('payload', {}).get('url')}")
        elif event_type == "deployment.succeeded":
            logger.info(f"Deployment succeeded: {payload.get('payload', {}).get('url')}")
            background_tasks.add_task(notify_deployment_success, payload)
        elif event_type == "deployment.error":
            logger.error(f"Deployment failed: {payload.get('payload', {}).get('url')}")
        elif event_type == "deployment.canceled":
            logger.warning(f"Deployment canceled: {payload.get('payload', {}).get('url')}")
        
        return {
            "success": True,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error processing Vercel webhook: {e}")
        # Return success even on error to prevent webhook retries
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/logs/vercel")
async def vercel_log_drain(request: Request):
    """Handle Vercel log drain events

    Vercel sends logs as newline-delimited JSON (NDJSON).
    This endpoint silently accepts all log data without storing it.
    """
    try:
        # Vercel sends logs as newline-delimited JSON
        body = await request.body()

        # Handle empty body gracefully
        if not body:
            return {
                "success": True,
                "processed": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

        body_str = body.decode('utf-8').strip()

        # Handle empty string after stripping
        if not body_str:
            return {
                "success": True,
                "processed": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

        logs = body_str.split('\n')

        processed_count = 0
        for log_line in logs:
            log_line = log_line.strip()
            if log_line:
                try:
                    # Just validate it's valid JSON - we don't store but accept
                    json.loads(log_line)
                    processed_count += 1
                except json.JSONDecodeError:
                    # Silently skip malformed log lines - don't flood error logs
                    pass

        return {
            "success": True,
            "processed": processed_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except UnicodeDecodeError:
        # Body wasn't valid UTF-8 - accept anyway to prevent drain disablement
        return {
            "success": True,
            "processed": 0,
            "note": "non-utf8-body",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Only log truly unexpected errors with details
        logger.warning(f"Vercel log drain unexpected error: {type(e).__name__}: {e}")
        # Return success to prevent log drain from being disabled
        return {
            "success": True,
            "processed": 0,
            "timestamp": datetime.utcnow().isoformat()
        }

# ============================================================================
# OBSERVABILITY DASHBOARD
# ============================================================================

@router.get("/observability/dashboard")
async def get_observability_dashboard():
    """Get comprehensive observability dashboard data"""
    render_configured = _render_configured()
    vercel_configured = _vercel_configured()

    if not render_configured and not vercel_configured:
        raise HTTPException(
            status_code=503,
            detail="No observability providers configured (set Render/Vercel credentials).",
        )

    platforms: Dict[str, Any] = {
        "render": {"configured": render_configured, "service_id": RENDER_SERVICE_ID if render_configured else None},
        "vercel": {"configured": vercel_configured, "project_id": VERCEL_PROJECT_ID if vercel_configured else None},
    }

    errors: List[Dict[str, Any]] = []
    render_data: Optional[Dict[str, Any]] = None
    vercel_data: Optional[Dict[str, Any]] = None

    async with httpx.AsyncClient() as client:
        if render_configured:
            try:
                service_resp = await client.get(
                    f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}",
                    headers={"Authorization": f"Bearer {RENDER_API_KEY}"},
                )
                service_resp.raise_for_status()
                deploys_resp = await client.get(
                    f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys?limit=10",
                    headers={"Authorization": f"Bearer {RENDER_API_KEY}"},
                )
                deploys_resp.raise_for_status()
                render_data = {
                    "service": service_resp.json(),
                    "deployments": deploys_resp.json(),
                }
            except Exception as exc:
                errors.append({"provider": "render", "error": str(exc)})

        if vercel_configured:
            try:
                project_resp = await client.get(
                    f"https://api.vercel.com/v9/projects/{VERCEL_PROJECT_ID}",
                    headers={"Authorization": f"Bearer {VERCEL_TOKEN}"},
                )
                project_resp.raise_for_status()
                deploys_resp = await client.get(
                    f"https://api.vercel.com/v6/deployments?projectId={VERCEL_PROJECT_ID}&limit=10",
                    headers={"Authorization": f"Bearer {VERCEL_TOKEN}"},
                )
                deploys_resp.raise_for_status()
                vercel_data = {
                    "project": project_resp.json(),
                    "deployments": deploys_resp.json(),
                }
            except Exception as exc:
                errors.append({"provider": "vercel", "error": str(exc)})

    if (render_configured and not render_data) and (vercel_configured and not vercel_data):
        raise HTTPException(status_code=502, detail={"platforms": platforms, "errors": errors})

    status = "operational" if not errors else "degraded"
    return {
        "status": status,
        "platforms": platforms,
        "render": render_data,
        "vercel": vercel_data,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat(),
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def notify_deployment_success(payload: dict):
    """Send notification when deployment succeeds"""
    try:
        platform = "Render" if "render" in str(payload) else "Vercel"
        logger.info(f"Deployment successful on {platform}")
        
        # Could send to Slack, email, etc.
        # For now, just log it
        
    except Exception as e:
        logger.error(f"Error sending deployment notification: {e}")

# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/observability/health")
async def observability_health():
    """Check observability system health"""
    render_configured = _render_configured()
    vercel_configured = _vercel_configured()
    status_value = "healthy" if (render_configured or vercel_configured) else "unavailable"
    return {
        "status": status_value,
        "services": {
            "render": {
                "webhook": "/api/v1/webhooks/render",
                "status": "/api/v1/render/status",
                "deployments": "/api/v1/render/deployments"
            },
            "vercel": {
                "webhook": "/api/v1/webhooks/vercel",
                "logs": "/api/v1/logs/vercel",
                "status": "/api/v1/vercel/status",
                "deployments": "/api/v1/vercel/deployments"
            },
            "dashboard": "/api/v1/observability/dashboard"
        },
        "configured": {"render": render_configured, "vercel": vercel_configured},
        "timestamp": datetime.utcnow().isoformat(),
    }
