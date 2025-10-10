# BrainOps Production Database Comprehensive Analysis
**Database:** PostgreSQL at aws-0-us-east-2.pooler.supabase.com
**Analysis Date:** 2025-09-30
**Total Tables:** 1,337 (1,174 in public schema)
**Total Rows:** 333,391
**Total Size:** 518 MB

---

## Executive Summary

The BrainOps production database contains **1,174 tables** in the public schema with 333,391 total rows. The database is highly structured with 18 distinct functional areas. **93.8% of tables are currently empty** (1,100 tables), indicating significant schema over-provisioning for future features. The top 9 large tables (1000+ rows) contain 99% of all data.

**Critical Findings:**
- **Production Memory** is the largest table (284,054 rows, 117 MB) - AI memory storage
- **Jobs** table has 12,849 active jobs (primary business data)
- **Customers** table has 3,651 customers (core business data)
- **AI Infrastructure** spans 212 tables but only 3,370 rows total
- **MyRoofGenius SaaS** tables exist but are completely empty (0 rows)
- **Weathercraft ERP** has minimal data (24 rows across 9 tables)

---

## 1. Database Overview

### Schema Distribution
| Schema | Tables | Purpose |
|--------|--------|---------|
| public | 1,187 | Main application data |
| landing_ | 19 | CenterPoint staging data |
| auth | 17 | Authentication/authorization |
| revenue | 12 | Revenue tracking |
| realtime | 10 | Real-time subscriptions |
| storage | 7 | File storage |
| task_os | 7 | Task operating system |
| app_ | 7 | Application-specific |
| **Total** | **1,337** | |

### Data Population Status
| Size Category | Table Count | Percentage |
|---------------|-------------|------------|
| Empty Tables | 1,100 | 93.8% |
| Small Tables (1-99 rows) | 58 | 4.9% |
| Medium Tables (100-999 rows) | 7 | 0.6% |
| Large Tables (1000+ rows) | 9 | 0.8% |

---

## 2. Top 50 Tables by Row Count

| Rank | Table Name | Rows | Size | Notes |
|------|------------|------|------|-------|
| 1 | **production_memory** | 284,054 | 117 MB | AI/Agent memory storage - largest table |
| 2 | **cron_job_history** | 15,176 | 5.3 MB | Background job execution logs |
| 3 | **jobs** | 12,849 | 17 MB | PRIMARY: Job/project tracking |
| 4 | **centerpoint_sync_status** | 6,601 | 13 MB | CenterPoint integration sync |
| 5 | **customers** | 3,651 | 4.3 MB | PRIMARY: Customer master data |
| 6 | **agent_executions** | 2,337 | 1.8 MB | AI agent execution history |
| 7 | **context_snapshots** | 2,088 | 31 MB | Context preservation |
| 8 | **system_monitoring** | 2,079 | 648 KB | System health monitoring |
| 9 | **invoices** | 2,012 | 4.9 MB | PRIMARY: Invoice/billing data |
| 10 | **expenses** | 500 | 272 KB | Expense tracking |
| 11 | **ai_task_queue** | 365 | 456 KB | Active AI task queue |
| 12 | **neural_pathways** | 302 | 104 KB | AI neural network paths |
| 13 | **cns_memory** | 191 | 1.8 MB | Central Nervous System memory |
| 14 | **app_users** | 154 | 192 KB | Application users |
| 15 | **customer_notes** | 100 | 80 KB | Customer notes/comments |
| 16 | **job_tasks** | 100 | 128 KB | Job task breakdown |
| 17 | **erp_completion_todos** | 90 | 80 KB | ERP completion tracking |
| 18 | **persistent_memory** | 83 | 168 KB | Persistent memory store |
| 19 | **master_todo** | 60 | 80 KB | Master todo list |
| 20 | **ai_agents** | 59 | 160 KB | PRIMARY: AI agent registry |
| 21-50 | *See detailed query results* | <60 rows | Various | Mostly configuration/reference tables |

---

## 3. Tables Grouped by Functional Area

### Complete Category Breakdown (18 Categories)

| Functional Area | Table Count | Total Rows | Active Data |
|-----------------|-------------|------------|-------------|
| **Other/Miscellaneous** | 473 | 2,661 | Mixed |
| **AI/Agent Infrastructure** | 212 | 3,370 | Active |
| **CenterPoint/Data Integration** | 66 | 6,601 | Active |
| **Inventory/Materials/Equipment** | 52 | 284,118 | Active (mostly production_memory) |
| **Job/Project Management** | 47 | 12,950 | Active |
| **System/Admin/Monitoring** | 46 | 17,274 | Active |
| **Financial Management** | 37 | 2,526 | Active |
| **Roofing/CAD/Weather** | 31 | 24 | Minimal |
| **Sales/Marketing** | 30 | 15 | Minimal |
| **Workflow/Automation** | 28 | 20 | Minimal |
| **Service/Support** | 27 | 0 | Empty |
| **Memory/Knowledge Base** | 24 | 0 | Empty |
| **Customer Management** | 21 | 3,805 | Active |
| **User/Auth/Security** | 19 | 17 | Active |
| **Employee/HR** | 19 | 4 | Minimal |
| **Estimates/Quotes** | 16 | 6 | Minimal |
| **Analytics/Reporting** | 15 | 0 | Empty |
| **MyRoofGenius SaaS** | 11 | 0 | Empty |

---

## 4. Core Business Tables (Detailed Analysis)

### Customer Management (21 tables, 3,805 rows)
**Active Tables:**
- `customers` - 3,651 rows - PRIMARY customer master data
- `customer_notes` - 100 rows
- `customer_history` - 54 rows

**Empty Tables:** 18 tables for advanced features (portals, segments, feedback, etc.)

### Job/Project Management (47 tables, 12,950 rows)
**Active Tables:**
- `jobs` - 12,849 rows - PRIMARY job tracking (95 columns)
- `job_tasks` - 100 rows
- `task_memory` - 1 row

**Empty Tables:** 44 tables for phases, costs, labor, materials, workflows, etc.

### Financial Management (37 tables, 2,526 rows)
**Active Tables:**
- `invoices` - 2,012 rows - PRIMARY billing (69 columns)
- `expenses` - 500 rows
- `revenue_streams` - 12 rows
- `payments` - 1 row

**Empty Tables:** 33 tables for AR aging, payment plans, budgets, etc.

### Employee/HR (19 tables, 4 rows)
**Active Tables:**
- `employees` - 4 rows - Minimal HR data (36 columns)

**Empty Tables:** 18 tables for crews, payroll, schedules, skills, etc.

### Inventory/Equipment (52 tables, 284,118 rows)
**Active Tables:**
- `production_memory` - 284,054 rows - AI memory (NOT inventory!)
- `production_todos` - 33 rows
- `materials` - 19 rows
- `inventory_items` - 12 rows

**Empty Tables:** 48 tables for warehouses, stock transfers, equipment, etc.

### Estimates/Quotes (16 tables, 6 rows)
**Active Tables:**
- `estimates` - 6 rows - PRIMARY estimate data (78 columns, PostGIS enabled)

**Empty Tables:** 15 tables for templates, approvals, assemblies, etc.

---

## 5. AI/Agent Infrastructure (212 tables, 3,370 rows)

### Core AI Agent Tables
| Table | Rows | Size | Purpose |
|-------|------|------|---------|
| `agent_executions` | 2,337 | 1.8 MB | Agent execution history |
| `ai_task_queue` | 365 | 456 KB | Active task queue |
| `neural_pathways` | 302 | 104 KB | Neural network connections |
| `cns_memory` | 191 | 1.8 MB | Central Nervous System memory |
| `ai_agents` | 59 | 160 KB | Agent registry (CORE) |
| `ai_workflow_executions` | 11 | 32 KB | Multi-agent workflows |
| `agent_registry` | 10 | 32 KB | Agent metadata |
| `ai_agents_active` | 8 | 80 KB | Active agent tracking |
| `ai_autonomous_config` | 5 | 48 KB | Autonomy configuration |

### AI Infrastructure Analysis
- **212 total AI/agent tables** (18% of all tables)
- **Only 3,370 rows total** across all AI tables
- **Extensive schema** for future AI capabilities
- **Key systems:** CNS (Central Nervous System), Neural Pathways, Agent Registry, Memory Systems

### Notable Empty AI Tables
- `ai_memories`, `ai_memory`, `agent_memories` - Multiple memory systems defined
- `ai_learning_episodes`, `ai_learning_patterns` - ML infrastructure
- `ai_knowledge_base`, `ai_knowledge_graph` - Knowledge management
- `ai_decision_engine`, `ai_decision_trees` - Decision systems
- `consciousness_evolution` - Advanced AI evolution tracking

---

## 6. System-Specific Tables

### MyRoofGenius SaaS (11 tables, 0 rows - ALL EMPTY)
```
mrg_users
mrg_leads
mrg_ai_usage
mrg_quotes
mrg_subscription_plans
mrg_revenue
mrg_ai_agents
mrg_analytics
myroofgenius_customers
myroofgenius_revenue
myroofgenius_subscriptions
```
**Status:** Schema created but not yet in production use

### Weathercraft ERP (9 tables, 24 rows)
| Table | Rows | Purpose |
|-------|------|---------|
| `weathercraft_system_status` | 10 | System health tracking |
| `weathercraft_test_results` | 8 | Test execution results |
| `weathercraft_rewrite_progress` | 5 | Development progress |
| `weathercraft_analysis_sessions` | 1 | Analysis tracking |
| 5 other tables | 0 | Empty |

**Status:** Development/testing phase, minimal production data

---

## 7. Schema Duplication Analysis

### Identified Duplicate/Similar Schemas
The database shows intentional redundancy in naming patterns, likely for system separation:

| Base Name | Similar Tables | Count | Notes |
|-----------|----------------|-------|-------|
| memories | agent_memories, ai_memories, memories | 3 | Different memory subsystems |
| tasks | agent_tasks, ai_tasks, tasks | 3 | Task management at different levels |
| agents | agents, ai_agents | 2 | Legacy vs new system? |
| decisions | ai_decisions, decisions | 2 | AI vs manual decisions |
| conversations | ai_conversations, conversations | 2 | AI vs human conversations |
| learning_patterns | agent_learning_patterns, ai_learning_patterns | 2 | Different learning systems |
| memory | agent_memory, ai_memory | 2 | Separate memory stores |
| executions | agent_executions, execution_logs | 2 | Different logging levels |

**Recommendation:** 30+ pairs of duplicated table concepts identified. Consider consolidating or clearly documenting the distinction between `ai_*`, `agent_*`, and base table names.

---

## 8. PostGIS/Spatial Tables (20 tables)

### Geographic Data Capabilities
| Table | Geometry Type | SRID | Purpose |
|-------|---------------|------|---------|
| `landing_building_outlines` | POLYGON | 4326 | Building footprints |
| `roof_areas` | POLYGON | 4326 | Roof area measurements |
| `roof_assets` | MULTIPOLYGON | 4326 | Roof asset mapping |
| `roof_planes` | POLYGON | 0 | 3D roof planes |
| `roof_sections` | POLYGON | 4326 | Roof sections |
| `roof_hazards` | POLYGON | 4326 | Hazard zones |
| `roof_penetrations` | POINT | 4326 | Roof penetration points |
| `roof_annotations` | POINT | 4326 | Annotation markers |
| `estimates` | POINT/POLYGON | 4326 | Property location + boundary |
| `landing_properties` | POINT | 4326 | Property locations |
| `daily_routes` | LINESTRING | 4326 | Route tracking |
| `equipment_schedules` | POINT | 4326 | Equipment GPS |
| `field_technician_logs` | POINT | 4326 | Checkin/checkout locations |
| `weather_conditions` | POINT | 4326 | Weather data points |
| And 6 more... | Various | 4326 | Other spatial features |

**Geographic Capabilities:**
- Full PostGIS support enabled
- 20 tables with spatial data (POINT, POLYGON, LINESTRING, MULTIPOLYGON)
- SRID 4326 (WGS84) for GPS coordinates
- Advanced roofing CAD/measurement capabilities
- Field operations GPS tracking

---

## 9. Active vs Dormant Tables

### Recently Active Tables (Last 30 Days)
Based on autovacuum/autoanalyze timestamps:

| Table | Rows | Last Activity | Status |
|-------|------|---------------|--------|
| `master_env_vars` | 29 | 2025-10-01 | Very active |
| `cron_job_history` | 15,176 | 2025-09-30 | Daily updates |
| `ai_task_queue` | 365 | 2025-09-29 | Active processing |
| `system_monitoring` | 2,079 | 2025-09-29 | Active monitoring |
| `cns_memory` | 191 | 2025-09-29 | Active AI memory |
| `persistent_memory` | 83 | 2025-09-29 | Active |
| `ai_agents` | 59 | 2025-09-22 to 2025-09-29 | Active |
| `neural_pathways` | 302 | 2025-09-29 | Active AI |
| `agent_executions` | 2,337 | 2025-09-27 | Active |
| `production_memory` | 284,054 | 2025-09-26 | Active |
| `customers`, `jobs`, `invoices` | Various | Recent | Core business |

**Activity Pattern:**
- Active tables: ~30-40 tables with regular updates
- Dormant tables: ~1,140 tables with no recent activity
- **90%+ of schema is pre-provisioned for future features**

---

## 10. Index Optimization Recommendations

### Tables Needing Index Optimization

| Table | Rows | Seq Scans | Index Scans | Issue | Recommendation |
|-------|------|-----------|-------------|-------|----------------|
| **agent_executions** | 2,337 | 37 | 6 | MORE SEQ THAN INDEX | Add indexes on execution_date, agent_id, status |
| **centerpoint_sync_status** | 6,601 | 25 | 2 | MORE SEQ THAN INDEX | Add indexes on sync_date, entity_type, status |
| **system_monitoring** | 2,079 | 23 | 0 | NO INDEX USAGE | Add indexes on timestamp, component, severity |
| **cron_job_history** | 15,177 | 22 | 1 | MORE SEQ THAN INDEX | Add composite index on (job_name, created_at) |
| **context_snapshots** | 2,088 | 22 | 1 | MORE SEQ THAN INDEX | Add indexes on created_at, context_type |

### Well-Indexed Tables (Good Performance)
- `customers` - 14 indexes, 251,661 index scans vs 36,751 seq scans ✅
- `production_memory` - 5 indexes, 951,682 index scans vs 13,151 seq scans ✅
- `jobs` - 25 indexes, 58,683 index scans vs 631 seq scans ✅
- `invoices` - 23 indexes, 51,871 index scans vs 213 seq scans ✅

### Specific Index Recommendations

```sql
-- Agent Executions
CREATE INDEX idx_agent_executions_agent_date ON agent_executions(agent_id, executed_at);
CREATE INDEX idx_agent_executions_status ON agent_executions(status) WHERE status != 'completed';

-- CenterPoint Sync Status
CREATE INDEX idx_centerpoint_sync_entity_date ON centerpoint_sync_status(entity_type, last_sync_at);
CREATE INDEX idx_centerpoint_sync_status ON centerpoint_sync_status(sync_status) WHERE sync_status != 'completed';

-- System Monitoring
CREATE INDEX idx_system_monitoring_time ON system_monitoring(monitored_at DESC);
CREATE INDEX idx_system_monitoring_component ON system_monitoring(component, severity);

-- Cron Job History
CREATE INDEX idx_cron_job_history_name_date ON cron_job_history(job_name, created_at DESC);
CREATE INDEX idx_cron_job_history_status ON cron_job_history(status);

-- Context Snapshots
CREATE INDEX idx_context_snapshots_date ON context_snapshots(created_at DESC);
CREATE INDEX idx_context_snapshots_type ON context_snapshots(context_type);
```

---

## 11. CenterPoint Integration (66 tables, 6,601 rows)

### CenterPoint Data Tables
The database has extensive CenterPoint ERP integration infrastructure:

**Landing/Staging Tables (19 tables):**
- `landing_centerpoint_companies`
- `landing_centerpoint_jobs`
- `landing_invoices`
- `landing_jobs`
- `landing_productions`
- `landing_properties`
- `landing_files`
- And 12 more staging tables

**CenterPoint Core Tables:**
- `centerpoint_sync_status` - 6,601 rows (most active)
- `centerpoint_companies`, `centerpoint_contacts`, `centerpoint_employees`
- `centerpoint_equipment`, `centerpoint_estimates`, `centerpoint_invoices`
- `centerpoint_job_history`, `centerpoint_notes`, `centerpoint_photos`
- `centerpoint_productions`, `centerpoint_products`
- And 20+ more integration tables

**File Management:**
- `cp_file_blobs`, `cp_file_content`, `cp_file_storage`
- `cp_file_queue`, `cp_file_large_objects`
- `cp_download_jobs`, `cp_entity_sync`

**Migration/Sync:**
- `cp_sync_status`, `cp_sync_tracking`, `cp_mv_progress`
- `cp_final_companies`, `cp_final_invoices`, `cp_final_productions`

**Status:** Active bidirectional sync with CenterPoint ERP system

---

## 12. Memory/Knowledge Systems (24 tables, mostly empty)

### Memory Table Architecture
Multiple overlapping memory systems identified:

**Production Memory:**
- `production_memory` - 284,054 rows (ACTIVE)
- `production_memory_entries` - 0 rows
- `production_memory_metadata` - 0 rows
- `production_memory_embeddings` - 0 rows
- `production_memory_sync` - 0 rows

**Persistent Memory:**
- `persistent_memory` - 83 rows (ACTIVE)
- `claude_persistent_memory` - 23 rows (ACTIVE)

**AI Memory Systems:**
- `ai_memory` - 0 rows
- `ai_memories` - 0 rows
- `ai_memory_store` - 3 rows
- `ai_memory_clusters` - 0 rows
- `ai_memory_relationships` - 0 rows
- `ai_memory_vectors` - 0 rows

**Agent Memory:**
- `agent_memory` - 0 rows
- `agent_memories` - 0 rows
- `agent_memory_access` - 0 rows

**CNS Memory:**
- `cns_memory` - 191 rows (ACTIVE)

**General Memory:**
- `memories` - 0 rows
- `memory_entries` - 0 rows
- `memory_collections` - 0 rows
- `memory_objects` - 0 rows
- `memory_relationships` - 0 rows
- `memory_versions` - 0 rows

**Recommendation:** Consolidate memory systems - currently 24 different memory-related tables with significant overlap.

---

## 13. Critical Missing Infrastructure

### Tables Defined But Empty (High Priority)

**Employee/HR Management:**
- No crew data (crews, crew_members, crew_schedules all empty)
- No payroll records
- No employee schedules or time tracking
- Only 4 employee records exist

**Inventory Management:**
- No warehouse data
- No stock movements or transfers
- No equipment tracking (equipment table empty)
- Only 12 inventory items defined

**Project Management:**
- Projects table is empty (using jobs table instead)
- No project phases, milestones, or Gantt tracking
- No project resource allocation

**Service Operations:**
- All 27 service/support tables are empty
- No service requests, tickets, or maintenance tracking
- Inspections infrastructure unused

**Sales/Marketing:**
- Only 15 leads in system
- No active marketing campaigns
- Email automation infrastructure unused

**Analytics/Reporting:**
- All 15 analytics tables empty
- No BI dashboards or KPI tracking
- Report automation unused

---

## 14. Foreign Key Relationships

### Core Table Relationships (50+ identified)

**Customer Hub (Primary Key: customers.id):**
- Referenced by: appointments, ar_aging, cad_projects, calendar_events, collection_cases, contracts, credit_checks, customer_communications, customer_contacts, customer_history, customer_notes, customer_portals, and 20+ more

**Job Hub (Primary Key: jobs.id):**
- Referenced by: appointments, cad_projects, calendar_events, contracts, change_orders, daily_field_reports, and 15+ more

**Invoice Hub (Primary Key: invoices.id):**
- Referenced by: campaign_enrollments, collection_case_invoices, credit_write_offs, dispute_refunds, and 8+ more

**Estimate Hub (Primary Key: estimates.id):**
- Referenced by: cad_drawings, cad_projects, cad_takeoff_features, calendar_events, contracts, and 6+ more

**Employee Hub (Primary Key: employees.id):**
- Referenced by: benefit_enrollments, compensation_history, disciplinary_actions, and 5+ more

**Tenant Hub (Primary Key: tenants.id):**
- Referenced by: customer_portals (multi-tenant architecture)

**Strong referential integrity** across core business tables

---

## 15. Table Column Complexity

### Highest Column Count Tables
Based on sample analysis:

- `jobs` - **95 columns** - Extensive job tracking
- `customers` - **81 columns** - Comprehensive customer data
- `estimates` - **78 columns** - Detailed estimate management
- `invoices` - **69 columns** - Complex billing
- `leads` - **50 columns** - Rich lead data
- `employees` - **36 columns** - Complete HR data
- `projects` - **36 columns** - Full project management

**Wide table design** - optimized for comprehensive data capture but may impact query performance

---

## 16. Summary Statistics

### By the Numbers
- **1,174 tables** in public schema
- **333,391 total rows** across all tables
- **518 MB total size**
- **1,100 tables (93.8%) are empty** - pre-provisioned
- **212 tables (18%)** for AI/Agent infrastructure
- **66 tables (5.6%)** for CenterPoint integration
- **20 tables** with PostGIS spatial data
- **30+ identified index optimization opportunities**
- **50+ foreign key relationships** on core tables
- **18 distinct functional areas**

### Data Distribution
- **Top 1 table** (production_memory) = 85% of all rows
- **Top 3 tables** = 93% of all rows
- **Top 9 tables** = 99% of all rows
- **Bottom 1,165 tables** = 1% of all rows

---

## 17. Critical Recommendations

### Immediate Actions (High Priority)

1. **Index Optimization**
   - Add missing indexes to `agent_executions`, `centerpoint_sync_status`, `system_monitoring`
   - Monitor index usage on newly created indexes

2. **Schema Consolidation**
   - Audit and consolidate duplicate memory systems (24 tables)
   - Document the distinction between `ai_*`, `agent_*`, and base tables
   - Consider archiving or dropping unused empty tables

3. **MyRoofGenius Deployment**
   - All 11 MyRoofGenius tables are empty
   - Multi-tenant infrastructure exists (tenants table has 35 rows)
   - Ready for production data migration

4. **Data Quality**
   - Only 4 employees in system (likely incomplete)
   - Only 6 estimates (very low for 3,651 customers)
   - Review data completeness for core business operations

### Medium Priority

5. **Performance Tuning**
   - Consider partitioning `production_memory` table (284K rows, 117 MB)
   - Review query performance on `jobs` table (12,849 rows, 95 columns)
   - Optimize `context_snapshots` (2,088 rows, 31 MB - large for row count)

6. **Infrastructure Planning**
   - Activate employee/HR systems (19 tables, 0 data)
   - Implement inventory management (52 tables, minimal usage)
   - Deploy service/support ticketing (27 tables, all empty)

7. **AI System Optimization**
   - Consolidate memory architectures
   - Document AI agent execution patterns
   - Review necessity of 212 AI tables for 3,370 total rows

### Low Priority

8. **Cleanup**
   - Archive old `cron_job_history` records (15,176 rows)
   - Review and clean `agent_executions` (2,337 records)
   - Consider purging old `context_snapshots`

9. **Documentation**
   - Document spatial data usage and requirements
   - Create data dictionary for 1,174 tables
   - Map out system integration points

---

## 18. Production Readiness Assessment

### Weathercraft ERP
**Status:** ⚠️ **Limited Production Use**
- Only 24 rows across 9 tables
- Appears to be in development/testing phase
- Not ready for full production deployment

### MyRoofGenius SaaS
**Status:** 🔴 **Not in Production**
- All 11 tables completely empty (0 rows)
- Schema created but no data
- Multi-tenant infrastructure ready (35 tenants exist)
- Needs data migration and deployment

### BrainOps Core (Customers/Jobs/Invoices)
**Status:** ✅ **Production Ready**
- 3,651 active customers
- 12,849 jobs tracked
- 2,012 invoices processed
- Strong data integrity and indexing

### AI Agent Infrastructure
**Status:** ✅ **Active Development**
- 2,337 agent executions recorded
- 365 tasks in queue
- 59 registered agents
- Production-ready but underutilized (212 tables for 3,370 rows)

---

## Conclusion

The BrainOps database is a **highly over-provisioned schema** with 1,174 tables but only ~70 tables containing meaningful data. The core business operations (customers, jobs, invoices) are production-ready with strong data integrity and indexing. The AI infrastructure is extensive but mostly empty, indicating significant planned future capabilities. MyRoofGenius SaaS tables exist but are completely unpopulated, suggesting the system is schema-ready but not yet deployed.

**Key Next Steps:**
1. Optimize indexes on high-traffic AI/monitoring tables
2. Consolidate redundant memory table architectures
3. Migrate data to MyRoofGenius SaaS infrastructure
4. Review and clean up schema over-provisioning
5. Document the 93.8% of empty tables - are they needed?

**Database Health:** Good (core business data), but significant architectural cleanup recommended.
