"""Email templating, rate limiting, and bounce tracking service."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import asyncpg
from fastapi import HTTPException

from core.request_safety import sanitize_payload, sanitize_text

logger = logging.getLogger(__name__)


class _SafeTemplateMap(dict):
    def __missing__(self, key: str) -> str:
        return ""


@dataclass
class RenderedEmail:
    subject: str
    html_body: str
    text_body: Optional[str]


class EmailEngine:
    """Provides template management and safe send orchestration."""

    def __init__(self, max_emails_per_minute: int = 60):
        self.max_emails_per_minute = max(1, max_emails_per_minute)

    async def ensure_tables(self, conn: asyncpg.Connection) -> None:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS email_templates (
                id UUID PRIMARY KEY,
                tenant_id VARCHAR(255) NOT NULL,
                template_name VARCHAR(255) NOT NULL,
                subject_template TEXT NOT NULL,
                html_template TEXT NOT NULL,
                text_template TEXT,
                metadata JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE (tenant_id, template_name)
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS email_send_events (
                id UUID PRIMARY KEY,
                tenant_id VARCHAR(255) NOT NULL,
                recipient_email VARCHAR(255) NOT NULL,
                template_name VARCHAR(255),
                provider VARCHAR(100),
                provider_message_id VARCHAR(255),
                status VARCHAR(50) NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS email_bounces (
                id UUID PRIMARY KEY,
                tenant_id VARCHAR(255) NOT NULL,
                recipient_email VARCHAR(255) NOT NULL,
                reason TEXT,
                provider_event_id VARCHAR(255),
                metadata JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_email_send_events_tenant_created
                ON email_send_events(tenant_id, created_at DESC)
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_email_bounces_tenant_email
                ON email_bounces(tenant_id, recipient_email)
            """
        )

    async def upsert_template(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_id: str,
        template_name: str,
        subject_template: str,
        html_template: str,
        text_template: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        await self.ensure_tables(conn)

        clean_metadata = sanitize_payload(metadata or {})
        clean_template_name = sanitize_text(template_name, max_length=255)

        row = await conn.fetchrow(
            """
            INSERT INTO email_templates (
                id, tenant_id, template_name, subject_template,
                html_template, text_template, metadata, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7::jsonb, NOW(), NOW()
            )
            ON CONFLICT (tenant_id, template_name) DO UPDATE
            SET subject_template = EXCLUDED.subject_template,
                html_template = EXCLUDED.html_template,
                text_template = EXCLUDED.text_template,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING id, template_name, updated_at
            """,
            str(uuid.uuid4()),
            tenant_id,
            clean_template_name,
            subject_template,
            html_template,
            text_template,
            json.dumps(clean_metadata),
        )

        return {
            "id": str(row["id"]),
            "template_name": row["template_name"],
            "updated_at": row["updated_at"],
        }

    async def _assert_rate_limit(self, conn: asyncpg.Connection, tenant_id: str) -> None:
        sent_last_minute = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM email_send_events
            WHERE tenant_id = $1
              AND created_at >= NOW() - INTERVAL '1 minute'
              AND status IN ('queued', 'sent')
            """,
            tenant_id,
        )

        if (sent_last_minute or 0) >= self.max_emails_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Email send rate limit exceeded",
            )

    async def is_bounce_suppressed(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_id: str,
        recipient_email: str,
        bounce_threshold: int = 3,
    ) -> bool:
        await self.ensure_tables(conn)
        bounce_count = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM email_bounces
            WHERE tenant_id = $1
              AND lower(recipient_email) = lower($2)
            """,
            tenant_id,
            recipient_email,
        )
        return (bounce_count or 0) >= bounce_threshold

    async def render_template(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_id: str,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RenderedEmail:
        await self.ensure_tables(conn)

        template = await conn.fetchrow(
            """
            SELECT subject_template, html_template, text_template
            FROM email_templates
            WHERE tenant_id = $1 AND template_name = $2
            """,
            tenant_id,
            template_name,
        )
        if not template:
            raise HTTPException(status_code=404, detail="Email template not found")

        clean_context = sanitize_payload(context or {})
        mapper = _SafeTemplateMap(clean_context)

        return RenderedEmail(
            subject=template["subject_template"].format_map(mapper),
            html_body=template["html_template"].format_map(mapper),
            text_body=(template["text_template"].format_map(mapper) if template["text_template"] else None),
        )

    async def queue_send(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_id: str,
        recipient_email: str,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        provider: str = "resend",
    ) -> Dict[str, Any]:
        """Queue a send event with template rendering and tenant rate limiting."""
        await self.ensure_tables(conn)
        await self._assert_rate_limit(conn, tenant_id)

        email = sanitize_text(recipient_email, max_length=255)
        if not email:
            raise HTTPException(status_code=400, detail="Recipient email is required")

        if await self.is_bounce_suppressed(conn, tenant_id=tenant_id, recipient_email=email):
            raise HTTPException(status_code=409, detail="Recipient is suppressed due to repeated bounces")

        rendered = await self.render_template(
            conn,
            tenant_id=tenant_id,
            template_name=template_name,
            context=context,
        )

        event_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO email_send_events (
                id, tenant_id, recipient_email, template_name,
                provider, status, metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, 'queued', $6::jsonb, NOW()
            )
            """,
            event_id,
            tenant_id,
            email,
            template_name,
            provider,
            json.dumps(
                {
                    "subject": rendered.subject,
                    "text_body": rendered.text_body,
                    "context": sanitize_payload(context or {}),
                }
            ),
        )

        return {
            "event_id": event_id,
            "status": "queued",
            "recipient_email": email,
            "provider": provider,
            "subject": rendered.subject,
            "html_body": rendered.html_body,
            "text_body": rendered.text_body,
        }

    async def record_bounce(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_id: str,
        recipient_email: str,
        reason: Optional[str],
        provider_event_id: Optional[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        await self.ensure_tables(conn)

        bounce_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO email_bounces (
                id, tenant_id, recipient_email, reason,
                provider_event_id, metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6::jsonb, NOW()
            )
            """,
            bounce_id,
            tenant_id,
            sanitize_text(recipient_email, max_length=255),
            sanitize_text(reason, max_length=1000),
            sanitize_text(provider_event_id, max_length=255),
            json.dumps(sanitize_payload(metadata or {})),
        )

        return {
            "id": bounce_id,
            "status": "recorded",
            "recipient_email": recipient_email,
        }


email_engine = EmailEngine()
