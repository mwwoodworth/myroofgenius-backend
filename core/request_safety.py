"""Shared request hardening helpers for route handlers."""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Dict, Mapping, Optional

from fastapi import HTTPException

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_SCRIPT_TAG_RE = re.compile(r"(?is)<\s*script[^>]*>.*?<\s*/\s*script\s*>")


def sanitize_text(value: Optional[str], *, max_length: Optional[int] = None) -> Optional[str]:
    """Sanitize untrusted text while preserving normal user input."""
    if value is None:
        return None

    cleaned = _CONTROL_CHARS_RE.sub("", str(value)).strip()
    cleaned = _SCRIPT_TAG_RE.sub("", cleaned)

    if max_length is not None:
        return cleaned[:max_length]
    return cleaned


def sanitize_payload(payload: Any) -> Any:
    """Recursively sanitize a JSON-like payload."""
    if isinstance(payload, str):
        return sanitize_text(payload)

    if isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]

    if isinstance(payload, tuple):
        return tuple(sanitize_payload(item) for item in payload)

    if isinstance(payload, dict):
        sanitized: Dict[str, Any] = {}
        for key, value in payload.items():
            key_str = sanitize_text(str(key), max_length=120) or ""
            sanitized[key_str] = sanitize_payload(value)
        return sanitized

    return payload


def require_tenant_id(current_user: Mapping[str, Any]) -> str:
    """Require a tenant id in auth context for tenant-scoped operations."""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")
    return str(tenant_id)


def parse_uuid(value: str, *, field_name: str = "id") -> uuid.UUID:
    """Parse a UUID path/query value with a consistent validation error."""
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


def raise_internal_error(
    logger: logging.Logger,
    operation: str,
    exc: Exception,
) -> "None":
    """Log internal errors and raise a safe 500 response."""
    logger.exception("%s failed", operation, exc_info=exc)
    raise HTTPException(status_code=500, detail="Internal server error")


# Compiled once at module level for performance
_SAFE_COLUMN_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def validate_column_name(field: str) -> str:
    """Validate that a field name is a safe SQL column identifier.

    Only allows alphanumeric characters and underscores, and the name
    must start with a letter or underscore.  Raises HTTP 400 if the
    name is invalid, preventing SQL injection through dynamic column
    names in UPDATE statements.
    """
    if not _SAFE_COLUMN_RE.match(field):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field name: {field}",
        )
    return field
