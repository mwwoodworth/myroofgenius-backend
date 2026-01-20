"""
AUREA (Executive Assistant) endpoints compatible with frontend expectations.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.supabase_auth import get_authenticated_user
from database import get_db
from ai_services.real_ai_integration import (
    ai_service,
    AIServiceNotConfiguredError,
    AIProviderCallError,
)
from routes.ai_brain import get_ai_brain


router = APIRouter(prefix="/api/v1/aurea", tags=["AUREA"])


class AureaChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None


class AureaExecuteRequest(BaseModel):
    command: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None


class AureaMemoryRequest(BaseModel):
    content: str = Field(..., min_length=1)
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[list[str]] = None
    context: Optional[Dict[str, Any]] = None


@router.get("/status")
async def aurea_status():
    providers = ai_service._configured_providers() if ai_service else []
    return {
        "status": "online" if providers else "degraded",
        "version": "2.0",
        "capabilities": ["chat", "execute", "memory"],
        "providers": providers,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health")
async def aurea_health():
    providers = ai_service._configured_providers() if ai_service else []
    brain_ok = False
    try:
        await get_ai_brain()
        brain_ok = True
    except Exception:
        brain_ok = False

    status = "healthy" if providers and brain_ok else "degraded"
    return {
        "status": status,
        "providers": providers,
        "ai_brain": "ready" if brain_ok else "unavailable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/chat")
async def aurea_chat(
    payload: AureaChatRequest,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    prompt = (
        "You are AUREA, the executive AI assistant for BrainOps AI OS. "
        "Be concise, actionable, and honest. Avoid inventing facts or metrics.\n\n"
        f"User message: {payload.message}\n"
        f"Context: {payload.context or {}}\n\n"
        "Return JSON with keys: response, next_actions (array of strings), confidence (0-1)."
    )

    try:
        result = await ai_service.generate_json(prompt)
    except (AIServiceNotConfiguredError, AIProviderCallError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    response_text = result.get("response")
    if not response_text:
        raise HTTPException(status_code=502, detail="AI response missing 'response' field")

    return {
        "response": response_text,
        "next_actions": result.get("next_actions", []),
        "confidence": result.get("confidence"),
        "provider": result.get("ai_provider"),
        "session_id": str(uuid.uuid4()),
        "user_id": current_user.get("id"),
        "tenant_id": current_user.get("tenant_id"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/execute")
async def aurea_execute(
    payload: AureaExecuteRequest,
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    try:
        brain = await get_ai_brain()
        result = await brain.aurea_execute(payload.command, payload.context or {})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "command": payload.command,
        "result": result,
        "status": "executed",
        "user_id": current_user.get("id"),
        "tenant_id": current_user.get("tenant_id"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/memory")
def aurea_memory_store(
    payload: AureaMemoryRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_authenticated_user),
):
    owner_id = current_user.get("id")
    tenant_id = current_user.get("tenant_id")
    memory_key = f"aurea:{owner_id}:{uuid.uuid4()}"

    metadata = payload.metadata or {}
    metadata["tenant_id"] = tenant_id
    metadata["source"] = "aurea"

    result = db.execute(
        text(
            """
            INSERT INTO memory_entries (
                key,
                content,
                metadata,
                owner_type,
                owner_id,
                tags,
                memory_type,
                context_json,
                category,
                title
            ) VALUES (
                :key,
                :content,
                :metadata,
                :owner_type,
                :owner_id,
                :tags,
                :memory_type,
                :context_json,
                :category,
                :title
            )
            RETURNING memory_id, created_at
            """
        ),
        {
            "key": memory_key,
            "content": payload.content,
            "metadata": json.dumps(metadata),
            "owner_type": "aurea",
            "owner_id": owner_id,
            "tags": payload.tags or [],
            "memory_type": "aurea",
            "context_json": json.dumps(payload.context or {}),
            "category": "aurea",
            "title": payload.title or "AUREA Memory",
        },
    ).first()
    db.commit()

    return {
        "memory_id": str(result[0]) if result else None,
        "status": "stored",
        "created_at": result[1].isoformat() if result else None,
    }


@router.get("/executive/status")
async def aurea_executive_status(db: Session = Depends(get_db)):
    brain = await get_ai_brain()
    providers = ai_service._configured_providers() if ai_service else []

    memory_total = None
    try:
        row = db.execute(text("SELECT COUNT(*) FROM memory_entries")).first()
        if row:
            memory_total = int(row[0])
    except Exception:
        memory_total = None

    return {
        "status": "operational",
        "ai_brain": {
            "agents_total": len(getattr(brain, "agents", {})),
            "decisions_made": getattr(brain, "decisions_made", 0),
            "learning_rate": getattr(brain, "learning_rate", None),
        },
        "memory": {
            "total_entries": memory_total,
        },
        "providers": providers,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
