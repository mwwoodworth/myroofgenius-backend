#!/usr/bin/env python3
"""
crm-mcp - Customer relationship management MCP
Port: 5002
"""

import os
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="crm-mcp",
    description="Customer relationship management MCP",
    version="1.0.0"
)

ENVIRONMENT = os.getenv("ENVIRONMENT", os.getenv("ENV", "production")).lower()
IS_PRODUCTION = ENVIRONMENT in {"production", "prod"}
ALLOW_STUBS = os.getenv("ALLOW_MCP_STUBS", "").strip().lower() in {"1", "true", "yes"}
if IS_PRODUCTION and ALLOW_STUBS:
    logger.critical("ALLOW_MCP_STUBS is set in production; refusing to run stub MCP server.")
    ALLOW_STUBS = False

class MCPRequest(BaseModel):
    action: str
    params: Optional[Dict[str, Any]] = {}

class MCPResponse(BaseModel):
    status: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

@app.get("/health")
async def health():
    if not ALLOW_STUBS:
        raise HTTPException(status_code=503, detail="MCP stub server disabled.")
    return {
        "status": "stubbed",
        "server": "crm-mcp",
        "port": 5002,
        "capabilities": ["customers", "contacts", "deals", "communication"],
        "stubbed": True,
        "ready": False,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/execute")
async def execute(request: MCPRequest):
    """Execute MCP action"""
    if not ALLOW_STUBS:
        raise HTTPException(status_code=501, detail="MCP stub server has no implementation.")
    logger.warning("Stub MCP execution requested: %s", request.action)
    return MCPResponse(
        status="stubbed",
        data={
            "action": request.action,
            "detail": "Stubbed MCP server (dev-only).",
            "timestamp": datetime.utcnow().isoformat(),
        },
        error="stubbed",
    )

@app.get("/capabilities")
async def get_capabilities():
    return {
        "server": "crm-mcp",
        "capabilities": ["customers", "contacts", "deals", "communication"],
        "version": "1.0.0",
        "stubbed": True,
        "ready": False
    }

if __name__ == "__main__":
    logger.info("Starting crm-mcp on port 5002")
    uvicorn.run(app, host="0.0.0.0", port=5002)
