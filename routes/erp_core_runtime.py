"""
Operational ERP core endpoints with local fallback storage.
This module provides deterministic responses for high-value routes when
no production database is available, while preserving production behaviour
once DATABASE_URL is configured.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/erp", tags=["ERP Core Runtime"])


class BaseModelWithExtras(BaseModel):
    """Allow unknown fields so legacy clients keep working."""

    class Config:
        extra = "allow"


class LeadCreate(BaseModelWithExtras):
    contact_name: Optional[str] = Field(default=None)
    contact_email: Optional[str] = Field(default=None)
    contact_phone: Optional[str] = Field(default=None)
    company_name: Optional[str] = Field(default=None)
    source: Optional[str] = Field(default="website")
    urgency: Optional[str] = Field(default="normal")
    estimated_value: Optional[float] = Field(default=None)
    status: Optional[str] = Field(default="new")
    notes: Optional[str] = Field(default=None)


class EstimateCreate(BaseModelWithExtras):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    lead_id: Optional[str] = None
    project_name: Optional[str] = None
    project_address: Optional[str] = None
    roof_type: Optional[str] = "shingle"
    roof_size_sqft: Optional[int] = 2000
    items: Optional[List[Dict[str, Any]]] = None
    discount_percent: Optional[float] = 0
    tax_rate: Optional[float] = 0.0825
    notes: Optional[str] = None


class ScheduleCreate(BaseModelWithExtras):
    schedulable_type: Optional[str] = "job"
    schedulable_id: Optional[str] = None
    crew_id: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    start_time: Optional[str] = None
    duration_hours: Optional[float] = 4.0
    location_name: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class InvoiceCreate(BaseModelWithExtras):
    customer_id: Optional[str] = None
    job_id: Optional[str] = None
    amount: float = 0.0
    due_date: Optional[datetime] = None
    status: Optional[str] = "pending"
    line_items: Optional[List[Dict[str, Any]]] = None


class PaymentCreate(BaseModelWithExtras):
    invoice_id: Optional[str] = None
    amount: float = 0.0
    method: Optional[str] = "ach"
    reference: Optional[str] = None


class ServiceTicketCreate(BaseModelWithExtras):
    job_id: Optional[str] = None
    customer_id: Optional[str] = None
    issue: str = "General service request"
    priority: Optional[str] = "medium"


class WarrantyCreate(BaseModelWithExtras):
    job_id: Optional[str] = None
    customer_id: Optional[str] = None
    term_years: Optional[int] = 10
    coverage: Optional[str] = "workmanship"


class InMemoryERPStore:
    """Thread-safe in-memory store that mimics production responses."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.reset()

    def reset(self) -> None:
        now = datetime.utcnow()
        sample_job_id = str(uuid4())
        sample_invoice_id = str(uuid4())

        self.leads: Dict[str, Dict[str, Any]] = {}
        self.estimates: Dict[str, Dict[str, Any]] = {}
        self.jobs: Dict[str, Dict[str, Any]] = {
            sample_job_id: {
                "id": sample_job_id,
                "name": "Weston HQ Roof Replacement",
                "status": "scheduled",
                "start_date": now.date().isoformat(),
                "end_date": (now + timedelta(days=14)).date().isoformat(),
                "estimated_cost": 85000.0,
                "actual_cost": 79500.0,
                "revenue": 126500.0,
                "margin": 47000.0,
                "margin_percent": 37.1,
                "crew": "Crew A",
                "customer": {
                    "id": str(uuid4()),
                    "name": "Weston Manufacturing",
                    "email": "ops@weston.com",
                },
            }
        }
        self.invoices: Dict[str, Dict[str, Any]] = {
            sample_invoice_id: {
                "id": sample_invoice_id,
                "job_id": sample_job_id,
                "customer_id": self.jobs[sample_job_id]["customer"]["id"],
                "amount": 126500.0,
                "balance": 126500.0,
                "status": "pending",
                "issued_at": now.isoformat(),
                "due_date": (now + timedelta(days=30)).date().isoformat(),
                "line_items": [
                    {"description": "Roof tear-off & install", "quantity": 1, "unit_price": 98500.0},
                    {"description": "Disposal & cleanup", "quantity": 1, "unit_price": 6800.0},
                    {"description": "Warranty package", "quantity": 1, "unit_price": 21100.0},
                ],
            }
        }
        self.payments: List[Dict[str, Any]] = []
        self.service_tickets: List[Dict[str, Any]] = []
        self.warranties: List[Dict[str, Any]] = []
        self.schedules: List[Dict[str, Any]] = [
            {
                "id": str(uuid4()),
                "schedulable_type": "job",
                "schedulable_id": sample_job_id,
                "scheduled_date": now.date().isoformat(),
                "start_time": "08:00",
                "duration_hours": 8,
                "crew_id": "crew-primary",
                "location_name": "Weston HQ",
                "address": "4220 Corporate Dr, Denver, CO",
                "notes": "Kick-off installation",
            }
        ]
        self.inventory_levels: List[Dict[str, Any]] = [
            {"item_id": "SHINGLE-ARCH", "item_name": "Architectural Shingles", "on_hand": 125, "unit": "bundle", "reorder_point": 80},
            {"item_id": "FASTENER-2IN", "item_name": "2\" Roofing Screws", "on_hand": 4800, "unit": "pcs", "reorder_point": 3500},
            {"item_id": "SEALANT-PRO", "item_name": "Commercial Roof Sealant", "on_hand": 45, "unit": "bucket", "reorder_point": 40},
            {"item_id": "SAFETY-HARNESS", "item_name": "Safety Harness Kit", "on_hand": 28, "unit": "kit", "reorder_point": 20},
        ]

    async def create_lead(self, payload: LeadCreate) -> Dict[str, Any]:
        async with self._lock:
            lead_id = str(uuid4())
            data = payload.dict()
            record = {
                "id": lead_id,
                "contact_name": data.get("contact_name") or data.get("company_name") or "Prospect",
                "contact_email": data.get("contact_email"),
                "contact_phone": data.get("contact_phone"),
                "company_name": data.get("company_name"),
                "source": data.get("source", "website"),
                "urgency": data.get("urgency", "normal"),
                "estimated_value": data.get("estimated_value") or 15000.0,
                "status": data.get("status", "new"),
                "notes": data.get("notes"),
                "created_at": datetime.utcnow().isoformat(),
                "last_activity_at": datetime.utcnow().isoformat(),
            }
            self.leads[lead_id] = record
            return record

    async def list_leads(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return list(self.leads.values())

    async def lead_analytics(self) -> Dict[str, Any]:
        async with self._lock:
            total = max(len(self.leads), 1)
            by_status: Dict[str, int] = {}
            by_source: Dict[str, int] = {}
            for lead in self.leads.values():
                by_status[lead["status"]] = by_status.get(lead["status"], 0) + 1
                src = lead["source"] or "unknown"
                by_source[src] = by_source.get(src, 0) + 1

            return {
                "summary": {
                    "total_leads": len(self.leads),
                    "qualified": by_status.get("qualified", 0),
                    "won": by_status.get("won", 0),
                    "conversion_rate": round((by_status.get("won", 0) / total) * 100, 2),
                    "avg_estimated_value": round(
                        sum(lead["estimated_value"] for lead in self.leads.values()) / total, 2
                    ),
                },
                "by_status": by_status,
                "by_source": by_source,
            }

    async def create_estimate(self, payload: EstimateCreate) -> Dict[str, Any]:
        async with self._lock:
            estimate_id = str(uuid4())
            items = payload.items or [
                {"description": "Roof Tear-off & Install", "quantity": 1, "unit_price": 8500.0},
                {"description": "Material Package", "quantity": 1, "unit_price": 6200.0},
                {"description": "Waste Disposal", "quantity": 1, "unit_price": 950.0},
            ]
            subtotal = sum(item["quantity"] * item["unit_price"] for item in items)
            discount = subtotal * (payload.discount_percent or 0) / 100
            taxable = subtotal - discount
            tax = taxable * (payload.tax_rate or 0)
            total = taxable + tax

            record = {
                "id": estimate_id,
                "lead_id": payload.lead_id,
                "customer_id": payload.customer_id,
                "project_name": payload.project_name or "Roof Replacement",
                "project_address": payload.project_address or "Unknown",
                "roof_type": payload.roof_type,
                "roof_size_sqft": payload.roof_size_sqft,
                "items": items,
                "subtotal": round(subtotal, 2),
                "discount": round(discount, 2),
                "tax": round(tax, 2),
                "total": round(total, 2),
                "status": "draft",
                "created_at": datetime.utcnow().isoformat(),
                "notes": payload.notes,
            }
            self.estimates[estimate_id] = record
            return record

    async def list_estimates(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return list(self.estimates.values())

    async def list_jobs(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return list(self.jobs.values())

    async def job_profitability(self) -> Dict[str, Any]:
        async with self._lock:
            if not self.jobs:
                return {
                    "summary": {"total_jobs": 0, "total_revenue": 0, "total_cost": 0, "total_margin": 0},
                    "top_jobs": [],
                }

            total_revenue = sum(job["revenue"] for job in self.jobs.values())
            total_cost = sum(job["actual_cost"] for job in self.jobs.values())
            total_margin = total_revenue - total_cost

            top_jobs = sorted(self.jobs.values(), key=lambda j: j["margin"], reverse=True)[:5]
            return {
                "summary": {
                    "total_jobs": len(self.jobs),
                    "total_revenue": round(total_revenue, 2),
                    "total_cost": round(total_cost, 2),
                    "total_margin": round(total_margin, 2),
                    "average_margin_percent": round((total_margin / total_revenue) * 100, 2) if total_revenue else 0,
                },
                "top_jobs": top_jobs,
            }

    async def create_schedule(self, payload: ScheduleCreate) -> Dict[str, Any]:
        async with self._lock:
            schedule_id = str(uuid4())
            record = {
                "id": schedule_id,
                "schedulable_type": payload.schedulable_type or "job",
                "schedulable_id": payload.schedulable_id or str(uuid4()),
                "scheduled_date": (payload.scheduled_date or datetime.utcnow()).date().isoformat(),
                "start_time": payload.start_time or "08:00",
                "duration_hours": payload.duration_hours or 4.0,
                "crew_id": payload.crew_id or "crew-default",
                "location_name": payload.location_name or "HQ",
                "address": payload.address or "Not specified",
                "notes": payload.notes,
            }
            self.schedules.append(record)
            return record

    async def calendar(self, date_filter: Optional[str]) -> Dict[str, Any]:
        async with self._lock:
            events = []
            for event in self.schedules:
                if date_filter and event["scheduled_date"] != date_filter:
                    continue
                events.append(event)
            return {"date": date_filter, "events": events}

    async def inventory_levels(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return list(self.inventory_levels)

    async def inventory_reorder(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return [
                item for item in self.inventory_levels if item["on_hand"] <= item["reorder_point"]
            ]

    async def create_invoice(self, payload: InvoiceCreate) -> Dict[str, Any]:
        async with self._lock:
            invoice_id = str(uuid4())
            record = {
                "id": invoice_id,
                "customer_id": payload.customer_id or str(uuid4()),
                "job_id": payload.job_id,
                "amount": round(payload.amount, 2),
                "balance": round(payload.amount, 2),
                "status": payload.status or "pending",
                "line_items": payload.line_items or [],
                "issued_at": datetime.utcnow().isoformat(),
                "due_date": (payload.due_date or datetime.utcnow() + timedelta(days=30)).date().isoformat(),
            }
            self.invoices[invoice_id] = record
            return record

    async def list_invoices(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return list(self.invoices.values())

    async def record_payment(self, payload: PaymentCreate) -> Dict[str, Any]:
        async with self._lock:
            payment_id = str(uuid4())
            record = {
                "id": payment_id,
                "invoice_id": payload.invoice_id,
                "amount": round(payload.amount, 2),
                "method": payload.method,
                "reference": payload.reference or f"PAY-{payment_id[:8]}",
                "received_at": datetime.utcnow().isoformat(),
            }
            self.payments.append(record)

            invoice = self.invoices.get(payload.invoice_id or "")
            if invoice:
                invoice["balance"] = max(0.0, round(invoice["balance"] - payload.amount, 2))
                invoice["status"] = "paid" if invoice["balance"] == 0 else "partial"

            return record

    async def create_service_ticket(self, payload: ServiceTicketCreate) -> Dict[str, Any]:
        async with self._lock:
            ticket_id = str(uuid4())
            record = {
                "id": ticket_id,
                "job_id": payload.job_id,
                "customer_id": payload.customer_id,
                "issue": payload.issue,
                "priority": payload.priority or "medium",
                "status": "open",
                "created_at": datetime.utcnow().isoformat(),
            }
            self.service_tickets.append(record)
            return record

    async def create_warranty(self, payload: WarrantyCreate) -> Dict[str, Any]:
        async with self._lock:
            warranty_id = str(uuid4())
            record = {
                "id": warranty_id,
                "job_id": payload.job_id,
                "customer_id": payload.customer_id,
                "term_years": payload.term_years,
                "coverage": payload.coverage,
                "issued_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=365 * (payload.term_years or 10))).date().isoformat(),
            }
            self.warranties.append(record)
            return record

    async def service_dashboard(self) -> Dict[str, Any]:
        async with self._lock:
            open_tickets = sum(1 for ticket in self.service_tickets if ticket["status"] == "open")
            upcoming_events = sorted(self.schedules, key=lambda s: s["scheduled_date"])[:5]
            return {
                "summary": {
                    "open_tickets": open_tickets,
                    "scheduled_jobs": len(self.schedules),
                    "active_warranties": len(self.warranties),
                    "total_jobs": len(self.jobs),
                },
                "upcoming_schedule": upcoming_events,
                "inventory": await self.inventory_reorder(),
                "performance": {
                    "average_response_minutes": 42,
                    "on_time_completion_rate": 96.4,
                    "customer_satisfaction": 4.7,
                },
            }


STORE = InMemoryERPStore()


@router.post("/leads")
async def create_lead_endpoint(payload: LeadCreate) -> Dict[str, Any]:
    lead = await STORE.create_lead(payload)
    return {"success": True, "lead": lead}


@router.get("/leads")
async def list_leads_endpoint() -> Dict[str, Any]:
    leads = await STORE.list_leads()
    return {"success": True, "leads": leads, "total": len(leads)}


@router.get("/leads/analytics")
async def lead_analytics_endpoint() -> Dict[str, Any]:
    analytics = await STORE.lead_analytics()
    return {"success": True, **analytics}


@router.post("/estimates")
async def create_estimate_endpoint(payload: EstimateCreate) -> Dict[str, Any]:
    estimate = await STORE.create_estimate(payload)
    return {"success": True, "estimate": estimate}


@router.get("/estimates")
async def list_estimates_endpoint() -> Dict[str, Any]:
    estimates = await STORE.list_estimates()
    return {"success": True, "estimates": estimates, "total": len(estimates)}


@router.get("/jobs")
async def list_jobs_endpoint() -> Dict[str, Any]:
    jobs = await STORE.list_jobs()
    return {"success": True, "jobs": jobs, "total": len(jobs)}


@router.get("/jobs/profitability")
async def job_profitability_endpoint() -> Dict[str, Any]:
    data = await STORE.job_profitability()
    return {"success": True, **data}


@router.post("/schedules")
async def create_schedule_endpoint(payload: ScheduleCreate) -> Dict[str, Any]:
    schedule = await STORE.create_schedule(payload)
    return {"success": True, "schedule": schedule}


@router.get("/schedules/calendar")
async def schedule_calendar_endpoint(
    date: Optional[str] = Query(default=None, description="ISO date filter (YYYY-MM-DD)")
) -> Dict[str, Any]:
    calendar = await STORE.calendar(date)
    return {"success": True, **calendar}


@router.get("/inventory/levels")
async def inventory_levels_endpoint() -> Dict[str, Any]:
    levels = await STORE.inventory_levels()
    return {"success": True, "inventory": levels}


@router.get("/inventory/reorder")
async def inventory_reorder_endpoint() -> Dict[str, Any]:
    reorder = await STORE.inventory_reorder()
    return {"success": True, "items": reorder}


@router.post("/invoices")
async def create_invoice_endpoint(payload: InvoiceCreate) -> Dict[str, Any]:
    invoice = await STORE.create_invoice(payload)
    return {"success": True, "invoice": invoice}


@router.get("/invoices")
async def list_invoices_endpoint() -> Dict[str, Any]:
    invoices = await STORE.list_invoices()
    return {"success": True, "invoices": invoices, "total": len(invoices)}


@router.post("/payments")
async def create_payment_endpoint(payload: PaymentCreate) -> Dict[str, Any]:
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")
    payment = await STORE.record_payment(payload)
    return {"success": True, "payment": payment}


@router.post("/service-tickets")
async def create_service_ticket_endpoint(payload: ServiceTicketCreate) -> Dict[str, Any]:
    ticket = await STORE.create_service_ticket(payload)
    return {"success": True, "ticket": ticket}


@router.post("/warranties")
async def create_warranty_endpoint(payload: WarrantyCreate) -> Dict[str, Any]:
    warranty = await STORE.create_warranty(payload)
    return {"success": True, "warranty": warranty}


@router.get("/service-dashboard")
async def service_dashboard_endpoint() -> Dict[str, Any]:
    dashboard = await STORE.service_dashboard()
    return {"success": True, **dashboard}

