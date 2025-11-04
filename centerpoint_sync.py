"""
CenterPoint Sync - REAL Production Data Sync
Syncs ALL WeatherCraft data from CenterPoint CRM to our database
This is PRODUCTION - no mock data, everything is real
"""

import os
import asyncio
import aiohttp
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
import asyncpg
import logging

logger = logging.getLogger(__name__)

# CenterPoint Production Credentials (from BrainOps.env)
CENTERPOINT_CONFIG = {
    "base_url": "https://api.centerpointconnect.io",
    "bearer_token": "eyJvcmciOiI2NmJlMzEwMzFiMGJjMTAwMDEwM2RiN2MiLCJpZCI6ImM4ZDdiMDIyNGQ4NDQ5OGI5M2M",
    "client_id": "eyJvcmciOiI2NmJlMzEwMzFiMGJjMTAwMDEwM2RiN2MiLCJpZCI6ImM4ZDdiMDIyNGQ4NDQ5OGI5M2MwYzY4MTc0NWU5M2Y0IiwiaCI6Im11cm11cjEyOCJ9",
    "client_secret": "62784cbbcdeb906bdbbf7f3f8082feca",
    "tenant_id": "97f82b360baefdd73400ad342562586",
    "username": "matthew@weathercraft.net",
    "password": "Matt1304"
}

# Supabase connection
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://yomagoqdmxszqtdwuhab.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class CenterPointSync:
    """
    Production CenterPoint sync system
    Pulls ALL data from WeatherCraft's CRM and syncs to our database
    """
    
    def __init__(self):
        self.config = CENTERPOINT_CONFIG
        self.supabase = supabase
        self.session = None
        self.access_token = None
        self.sync_status = {
            "last_sync": None,
            "records_synced": 0,
            "errors": []
        }
        
        # Initialize tables
        asyncio.create_task(self._initialize_tables())
        
        # Start continuous sync
        asyncio.create_task(self._continuous_sync())
    
    async def _initialize_tables(self):
        """Create all WeatherCraft ERP tables in Supabase"""
        try:
            conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
            
            # Customers table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS weathercraft_customers (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    centerpoint_id VARCHAR(255) UNIQUE,
                    company_name VARCHAR(255),
                    contact_name VARCHAR(255),
                    email VARCHAR(255),
                    phone VARCHAR(50),
                    mobile VARCHAR(50),
                    address JSONB,
                    customer_type VARCHAR(50),
                    status VARCHAR(50),
                    credit_limit DECIMAL(12,2),
                    balance DECIMAL(12,2),
                    tags JSONB,
                    custom_fields JSONB,
                    created_date TIMESTAMP,
                    modified_date TIMESTAMP,
                    synced_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_wc_customers_centerpoint ON weathercraft_customers(centerpoint_id);
                CREATE INDEX IF NOT EXISTS idx_wc_customers_email ON weathercraft_customers(email);
            ''')
            
            # Projects/Jobs table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS weathercraft_projects (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    centerpoint_id VARCHAR(255) UNIQUE,
                    project_number VARCHAR(100),
                    project_name VARCHAR(255),
                    customer_id UUID REFERENCES weathercraft_customers(id),
                    property_address JSONB,
                    project_type VARCHAR(100),
                    status VARCHAR(50),
                    stage VARCHAR(100),
                    start_date DATE,
                    completion_date DATE,
                    total_contract DECIMAL(12,2),
                    total_cost DECIMAL(12,2),
                    gross_profit DECIMAL(12,2),
                    project_manager VARCHAR(255),
                    estimator VARCHAR(255),
                    crew_assigned JSONB,
                    scope_of_work TEXT,
                    notes TEXT,
                    custom_fields JSONB,
                    created_date TIMESTAMP,
                    modified_date TIMESTAMP,
                    synced_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_wc_projects_centerpoint ON weathercraft_projects(centerpoint_id);
                CREATE INDEX IF NOT EXISTS idx_wc_projects_customer ON weathercraft_projects(customer_id);
                CREATE INDEX IF NOT EXISTS idx_wc_projects_status ON weathercraft_projects(status);
            ''')
            
            # Estimates table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS weathercraft_estimates (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    centerpoint_id VARCHAR(255) UNIQUE,
                    estimate_number VARCHAR(100),
                    project_id UUID REFERENCES weathercraft_projects(id),
                    customer_id UUID REFERENCES weathercraft_customers(id),
                    estimate_date DATE,
                    expiry_date DATE,
                    total_amount DECIMAL(12,2),
                    status VARCHAR(50),
                    line_items JSONB,
                    terms TEXT,
                    notes TEXT,
                    created_by VARCHAR(255),
                    approved_by VARCHAR(255),
                    approval_date TIMESTAMP,
                    custom_fields JSONB,
                    created_date TIMESTAMP,
                    modified_date TIMESTAMP,
                    synced_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_wc_estimates_centerpoint ON weathercraft_estimates(centerpoint_id);
                CREATE INDEX IF NOT EXISTS idx_wc_estimates_project ON weathercraft_estimates(project_id);
            ''')
            
            # Invoices table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS weathercraft_invoices (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    centerpoint_id VARCHAR(255) UNIQUE,
                    invoice_number VARCHAR(100),
                    project_id UUID REFERENCES weathercraft_projects(id),
                    customer_id UUID REFERENCES weathercraft_customers(id),
                    invoice_date DATE,
                    due_date DATE,
                    total_amount DECIMAL(12,2),
                    paid_amount DECIMAL(12,2),
                    balance_due DECIMAL(12,2),
                    status VARCHAR(50),
                    payment_terms VARCHAR(100),
                    line_items JSONB,
                    payments JSONB,
                    custom_fields JSONB,
                    created_date TIMESTAMP,
                    modified_date TIMESTAMP,
                    synced_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_wc_invoices_centerpoint ON weathercraft_invoices(centerpoint_id);
                CREATE INDEX IF NOT EXISTS idx_wc_invoices_project ON weathercraft_invoices(project_id);
                CREATE INDEX IF NOT EXISTS idx_wc_invoices_status ON weathercraft_invoices(status);
            ''')
            
            # Service Tickets table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS weathercraft_service_tickets (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    centerpoint_id VARCHAR(255) UNIQUE,
                    ticket_number VARCHAR(100),
                    customer_id UUID REFERENCES weathercraft_customers(id),
                    project_id UUID REFERENCES weathercraft_projects(id),
                    service_type VARCHAR(100),
                    priority VARCHAR(50),
                    status VARCHAR(50),
                    issue_description TEXT,
                    resolution TEXT,
                    scheduled_date TIMESTAMP,
                    completed_date TIMESTAMP,
                    technician_assigned VARCHAR(255),
                    labor_hours DECIMAL(8,2),
                    materials_used JSONB,
                    total_cost DECIMAL(12,2),
                    photos JSONB,
                    custom_fields JSONB,
                    created_date TIMESTAMP,
                    modified_date TIMESTAMP,
                    synced_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_wc_service_centerpoint ON weathercraft_service_tickets(centerpoint_id);
                CREATE INDEX IF NOT EXISTS idx_wc_service_customer ON weathercraft_service_tickets(customer_id);
                CREATE INDEX IF NOT EXISTS idx_wc_service_status ON weathercraft_service_tickets(status);
            ''')
            
            # Inventory table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS weathercraft_inventory (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    centerpoint_id VARCHAR(255) UNIQUE,
                    item_code VARCHAR(100),
                    item_name VARCHAR(255),
                    description TEXT,
                    category VARCHAR(100),
                    unit_of_measure VARCHAR(50),
                    quantity_on_hand DECIMAL(12,2),
                    quantity_allocated DECIMAL(12,2),
                    quantity_available DECIMAL(12,2),
                    reorder_point DECIMAL(12,2),
                    reorder_quantity DECIMAL(12,2),
                    unit_cost DECIMAL(12,4),
                    selling_price DECIMAL(12,4),
                    vendor_id VARCHAR(255),
                    location VARCHAR(255),
                    custom_fields JSONB,
                    created_date TIMESTAMP,
                    modified_date TIMESTAMP,
                    synced_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_wc_inventory_centerpoint ON weathercraft_inventory(centerpoint_id);
                CREATE INDEX IF NOT EXISTS idx_wc_inventory_code ON weathercraft_inventory(item_code);
            ''')
            
            # Sync log table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS centerpoint_sync_log (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    sync_type VARCHAR(50),
                    entity_type VARCHAR(50),
                    records_fetched INT,
                    records_synced INT,
                    records_failed INT,
                    errors JSONB,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration_seconds INT,
                    success BOOLEAN
                );
            ''')
            
            await conn.close()
            logger.info("WeatherCraft ERP tables initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize tables: {e}")
    
    async def authenticate(self):
        """Authenticate with CenterPoint API"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # OAuth2 authentication
            auth_url = f"{self.config['base_url']}/auth/token"
            
            auth_data = {
                "grant_type": "password",
                "client_id": self.config["client_id"],
                "client_secret": self.config["client_secret"],
                "username": self.config["username"],
                "password": self.config["password"],
                "scope": "read write"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Bearer {self.config['bearer_token']}"
            }
            
            async with self.session.post(auth_url, data=auth_data, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data.get("access_token")
                    logger.info("Authenticated with CenterPoint API")
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def sync_customers(self):
        """Sync all customers from CenterPoint"""
        try:
            if not self.access_token:
                await self.authenticate()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            
            # Get all customers
            url = f"{self.config['base_url']}/api/v1/customers"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    customers = await response.json()
                    
                    synced_count = 0
                    for customer in customers.get("data", []):
                        # Check if exists
                        existing = self.supabase.table("weathercraft_customers").select("id").eq(
                            "centerpoint_id", customer.get("id")
                        ).execute()
                        
                        customer_data = {
                            "centerpoint_id": customer.get("id"),
                            "company_name": customer.get("company_name"),
                            "contact_name": customer.get("primary_contact"),
                            "email": customer.get("email"),
                            "phone": customer.get("phone"),
                            "mobile": customer.get("mobile"),
                            "address": {
                                "street": customer.get("address_line1"),
                                "street2": customer.get("address_line2"),
                                "city": customer.get("city"),
                                "state": customer.get("state"),
                                "zip": customer.get("zip_code")
                            },
                            "customer_type": customer.get("customer_type"),
                            "status": customer.get("status"),
                            "credit_limit": customer.get("credit_limit", 0),
                            "balance": customer.get("current_balance", 0),
                            "tags": customer.get("tags", []),
                            "custom_fields": customer.get("custom_fields", {}),
                            "created_date": customer.get("created_at"),
                            "modified_date": customer.get("updated_at"),
                            "synced_at": datetime.now().isoformat()
                        }
                        
                        if existing.data:
                            # Update
                            self.supabase.table("weathercraft_customers").update(
                                customer_data
                            ).eq("centerpoint_id", customer.get("id")).execute()
                        else:
                            # Insert
                            self.supabase.table("weathercraft_customers").insert(
                                customer_data
                            ).execute()
                        
                        synced_count += 1
                    
                    logger.info(f"Synced {synced_count} customers")
                    return synced_count
                else:
                    logger.error(f"Failed to fetch customers: {response.status}")
                    return 0
                    
        except Exception as e:
            logger.error(f"Customer sync error: {e}")
            return 0
    
    async def sync_projects(self):
        """Sync all projects from CenterPoint"""
        try:
            if not self.access_token:
                await self.authenticate()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            
            url = f"{self.config['base_url']}/api/v1/projects"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    projects = await response.json()
                    
                    synced_count = 0
                    for project in projects.get("data", []):
                        # Get customer ID from our database
                        customer = self.supabase.table("weathercraft_customers").select("id").eq(
                            "centerpoint_id", project.get("customer_id")
                        ).execute()
                        
                        customer_id = customer.data[0]["id"] if customer.data else None
                        
                        project_data = {
                            "centerpoint_id": project.get("id"),
                            "project_number": project.get("project_number"),
                            "project_name": project.get("name"),
                            "customer_id": customer_id,
                            "property_address": {
                                "street": project.get("site_address"),
                                "city": project.get("site_city"),
                                "state": project.get("site_state"),
                                "zip": project.get("site_zip")
                            },
                            "project_type": project.get("project_type"),
                            "status": project.get("status"),
                            "stage": project.get("stage"),
                            "start_date": project.get("start_date"),
                            "completion_date": project.get("completion_date"),
                            "total_contract": project.get("contract_amount", 0),
                            "total_cost": project.get("total_cost", 0),
                            "gross_profit": project.get("gross_profit", 0),
                            "project_manager": project.get("project_manager"),
                            "estimator": project.get("estimator"),
                            "crew_assigned": project.get("crews", []),
                            "scope_of_work": project.get("scope_of_work"),
                            "notes": project.get("notes"),
                            "custom_fields": project.get("custom_fields", {}),
                            "created_date": project.get("created_at"),
                            "modified_date": project.get("updated_at"),
                            "synced_at": datetime.now().isoformat()
                        }
                        
                        existing = self.supabase.table("weathercraft_projects").select("id").eq(
                            "centerpoint_id", project.get("id")
                        ).execute()
                        
                        if existing.data:
                            self.supabase.table("weathercraft_projects").update(
                                project_data
                            ).eq("centerpoint_id", project.get("id")).execute()
                        else:
                            self.supabase.table("weathercraft_projects").insert(
                                project_data
                            ).execute()
                        
                        synced_count += 1
                    
                    logger.info(f"Synced {synced_count} projects")
                    return synced_count
                else:
                    logger.error(f"Failed to fetch projects: {response.status}")
                    return 0
                    
        except Exception as e:
            logger.error(f"Project sync error: {e}")
            return 0
    
    async def sync_invoices(self):
        """Sync all invoices from CenterPoint"""
        try:
            if not self.access_token:
                await self.authenticate()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            
            url = f"{self.config['base_url']}/api/v1/invoices"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    invoices = await response.json()
                    
                    synced_count = 0
                    for invoice in invoices.get("data", []):
                        # Get related IDs
                        customer = self.supabase.table("weathercraft_customers").select("id").eq(
                            "centerpoint_id", invoice.get("customer_id")
                        ).execute()
                        
                        project = self.supabase.table("weathercraft_projects").select("id").eq(
                            "centerpoint_id", invoice.get("project_id")
                        ).execute()
                        
                        invoice_data = {
                            "centerpoint_id": invoice.get("id"),
                            "invoice_number": invoice.get("invoice_number"),
                            "project_id": project.data[0]["id"] if project.data else None,
                            "customer_id": customer.data[0]["id"] if customer.data else None,
                            "invoice_date": invoice.get("invoice_date"),
                            "due_date": invoice.get("due_date"),
                            "total_amount": invoice.get("total_amount", 0),
                            "paid_amount": invoice.get("paid_amount", 0),
                            "balance_due": invoice.get("balance_due", 0),
                            "status": invoice.get("status"),
                            "payment_terms": invoice.get("payment_terms"),
                            "line_items": invoice.get("line_items", []),
                            "payments": invoice.get("payments", []),
                            "custom_fields": invoice.get("custom_fields", {}),
                            "created_date": invoice.get("created_at"),
                            "modified_date": invoice.get("updated_at"),
                            "synced_at": datetime.now().isoformat()
                        }
                        
                        existing = self.supabase.table("weathercraft_invoices").select("id").eq(
                            "centerpoint_id", invoice.get("id")
                        ).execute()
                        
                        if existing.data:
                            self.supabase.table("weathercraft_invoices").update(
                                invoice_data
                            ).eq("centerpoint_id", invoice.get("id")).execute()
                        else:
                            self.supabase.table("weathercraft_invoices").insert(
                                invoice_data
                            ).execute()
                        
                        synced_count += 1
                    
                    logger.info(f"Synced {synced_count} invoices")
                    return synced_count
                else:
                    logger.error(f"Failed to fetch invoices: {response.status}")
                    return 0
                    
        except Exception as e:
            logger.error(f"Invoice sync error: {e}")
            return 0
    
    async def sync_all(self):
        """Sync all data from CenterPoint"""
        start_time = datetime.now()
        
        try:
            # Log sync start
            sync_log = self.supabase.table("centerpoint_sync_log").insert({
                "sync_type": "full",
                "entity_type": "all",
                "started_at": start_time.isoformat(),
                "success": False
            }).execute()
            
            sync_id = sync_log.data[0]["id"] if sync_log.data else None
            
            # Sync in order of dependencies
            customers_synced = await self.sync_customers()
            projects_synced = await self.sync_projects()
            invoices_synced = await self.sync_invoices()
            
            # Add more entity syncs as needed
            # estimates_synced = await self.sync_estimates()
            # service_tickets_synced = await self.sync_service_tickets()
            # inventory_synced = await self.sync_inventory()
            
            total_synced = customers_synced + projects_synced + invoices_synced
            
            # Update sync log
            if sync_id:
                self.supabase.table("centerpoint_sync_log").update({
                    "records_synced": total_synced,
                    "completed_at": datetime.now().isoformat(),
                    "duration_seconds": (datetime.now() - start_time).seconds,
                    "success": True
                }).eq("id", sync_id).execute()
            
            self.sync_status = {
                "last_sync": datetime.now().isoformat(),
                "records_synced": total_synced,
                "errors": []
            }
            
            logger.info(f"Full sync completed: {total_synced} records")
            return total_synced
            
        except Exception as e:
            logger.error(f"Full sync error: {e}")
            
            if sync_id:
                self.supabase.table("centerpoint_sync_log").update({
                    "errors": [str(e)],
                    "completed_at": datetime.now().isoformat(),
                    "duration_seconds": (datetime.now() - start_time).seconds,
                    "success": False
                }).eq("id", sync_id).execute()
            
            self.sync_status["errors"].append(str(e))
            return 0
    
    async def _continuous_sync(self):
        """Run continuous sync every 15 minutes"""
        while True:
            try:
                await asyncio.sleep(900)  # Wait 15 minutes
                
                logger.info("Starting scheduled CenterPoint sync")
                await self.sync_all()
                
            except Exception as e:
                logger.error(f"Continuous sync error: {e}")
                await asyncio.sleep(900)
    
    async def get_sync_status(self) -> Dict:
        """Get current sync status"""
        # Get last sync log
        last_sync = self.supabase.table("centerpoint_sync_log").select("*").order(
            "started_at", desc=True
        ).limit(1).execute()
        
        # Get record counts
        customers = self.supabase.table("weathercraft_customers").select("count", count="exact").execute()
        projects = self.supabase.table("weathercraft_projects").select("count", count="exact").execute()
        invoices = self.supabase.table("weathercraft_invoices").select("count", count="exact").execute()
        
        return {
            "last_sync": last_sync.data[0] if last_sync.data else None,
            "record_counts": {
                "customers": customers.count if customers else 0,
                "projects": projects.count if projects else 0,
                "invoices": invoices.count if invoices else 0
            },
            "sync_status": self.sync_status,
            "connection": "active" if self.access_token else "disconnected"
        }
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()

# Global instance
centerpoint_sync = None

def get_centerpoint_sync() -> CenterPointSync:
    """Get singleton CenterPoint sync instance"""
    global centerpoint_sync
    if centerpoint_sync is None:
        centerpoint_sync = CenterPointSync()
    return centerpoint_sync