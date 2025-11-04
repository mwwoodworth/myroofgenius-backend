"""
Simplified Vercel Log Drain endpoint that returns 200 for testing
"""
from fastapi import APIRouter, Request, Response
import json

router = APIRouter()

@router.post("/logs/vercel")
async def receive_vercel_logs(request: Request):
    """
    Receive log drain data from Vercel
    Returns 200 immediately to pass Vercel's test
    """
    try:
        # Get the body but don't block
        body = await request.body()
        
        # Try to parse if it's NDJSON
        if body:
            lines = body.decode('utf-8').strip().split('\n')
            log_count = 0
            
            for line in lines:
                if line:
                    try:
                        log_data = json.loads(line)
                        log_count += 1
                        
                        # Just print for now - no database dependency
                        if log_data.get("level") == "error":
                            print(f"❌ Vercel Error: {log_data.get('message', 'Unknown error')}")
                        elif log_data.get("statusCode") == 404:
                            print(f"🔍 404: {log_data.get('path', 'Unknown path')}")
                            
                    except:
                        pass
            
            print(f"📊 Received {log_count} Vercel logs")
    except:
        # Don't let any error prevent 200 response
        pass
    
    # ALWAYS return 200 for Vercel
    return {"status": "ok", "message": "Log drain configured successfully"}

@router.get("/logs/vercel")
async def vercel_logs_health():
    """
    Health check for Vercel logs endpoint
    """
    return {"status": "ok", "endpoint": "vercel-logs", "ready": True}

@router.head("/logs/vercel")
async def vercel_logs_head():
    """
    HEAD request support for Vercel validation
    """
    return Response(status_code=200)