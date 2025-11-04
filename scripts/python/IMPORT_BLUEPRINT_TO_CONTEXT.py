#!/usr/bin/env python3
"""
Import BrainOps Blueprint into Operational Context System
Parses the ChatGPT blueprint and structures it into our database
"""

import json
import psycopg2
from psycopg2.extras import Json
from datetime import datetime
import uuid
import re

# Database connection
DB_URL = "postgresql://postgres:Brain0ps2O2S@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres"

def parse_blueprint_sections():
    """Parse the blueprint into structured sections"""
    
    sections = [
        # Executive Snapshot
        {
            "version": "2.0.0",
            "section": "executive",
            "subsection": "mission",
            "content": {
                "mission": "Build an AI-native, fully automated business OS that scales from solo founder to multi-brand SaaS ecosystem",
                "core_brands": {
                    "MyRoofGenius": "AI-native commercial roofing platform + marketplace",
                    "WeatherCraft": "Internal modular containerized ERP to be white-labeled",
                    "BrainStack Studio": "Internal HQ for automation, AI orchestration, CI/CD",
                    "AUREA": "Autonomous Unified Reasoning & Executive Assistant"
                },
                "pillars": [
                    "Automation-first (Make.com + MCP, LangGraph agents)",
                    "AI-centric design (RAG, copilot UX, personalization)",
                    "Scalable, modular, secure (FastAPI, Supabase, PostGIS)",
                    "Founder time minimization, revenue-first, quality without compromise"
                ]
            },
            "priority": 3,
            "status": "active",
            "implementation_status": "in_progress"
        },
        
        # System Landscape
        {
            "version": "2.0.0",
            "section": "system_landscape",
            "subsection": "frontend_apps",
            "content": {
                "apps": [
                    "MRG-Web (Next.js/React + Tailwind)",
                    "BSS-Web (internal command center)",
                    "Weathercraft-Web (admin portal + ops dashboards)"
                ],
                "deployment": "Vercel for Next.js apps"
            },
            "priority": 2,
            "status": "active",
            "implementation_status": "partial"
        },
        
        {
            "version": "2.0.0",
            "section": "system_landscape",
            "subsection": "backend_services",
            "content": {
                "services": [
                    "MRG-API (commerce, content, AI proxy)",
                    "Weathercraft-API (ERP/CRM, estimating, scheduling)",
                    "BrainOps-Core (LangGraph, AUREA, MCP bridge)"
                ],
                "deployment": "Render for FastAPI (autoscaling)"
            },
            "priority": 2,
            "status": "active",
            "implementation_status": "operational"
        },
        
        {
            "version": "2.0.0",
            "section": "system_landscape",
            "subsection": "data",
            "content": {
                "database": "Supabase (Postgres + pgvector + storage + RLS)",
                "extensions": ["PostGIS for geospatial", "pgvector for embeddings"],
                "rag_stores": "Supabase + Drive doc embeddings"
            },
            "priority": 2,
            "status": "active",
            "implementation_status": "operational"
        },
        
        # Canonical Repos
        {
            "version": "2.0.0",
            "section": "repositories",
            "subsection": "structure",
            "content": {
                "repos": {
                    "brainops-core": "LangGraph, AUREA, MCP, webhooks",
                    "myroofgenius-web": "Next.js public app + marketplace",
                    "myroofgenius-api": "FastAPI service for MRG",
                    "weathercraft-erp": "Full ERP backend + web admin",
                    "bss-web": "Internal command center",
                    "automation-scenarios": "Make.com blueprints",
                    "infra": "IaC, GitHub Actions, config templates"
                },
                "branch_strategy": {
                    "main": "protected, deploys to production",
                    "develop": "deploys to staging",
                    "feature": "PR to develop with checks"
                }
            },
            "priority": 2,
            "status": "active",
            "implementation_status": "partial"
        },
        
        # Environment Matrix
        {
            "version": "2.0.0",
            "section": "environments",
            "subsection": "matrix",
            "content": {
                "dev": {
                    "frontend": "Vercel Preview",
                    "backend": "Render free tier",
                    "database": "Local docker (optional)"
                },
                "staging": {
                    "frontend": "Vercel Preview",
                    "backend": "Render starter",
                    "database": "Supabase project (staging)"
                },
                "production": {
                    "frontend": "Vercel Prod",
                    "backend": "Render pro",
                    "database": "Supabase project (prod)"
                }
            },
            "priority": 2,
            "status": "active",
            "implementation_status": "operational"
        },
        
        # Multi-AI LangGraph Orchestration
        {
            "version": "2.0.0",
            "section": "ai_orchestration",
            "subsection": "agents",
            "content": {
                "agents": [
                    "Planner - decomposes goals to tasks",
                    "Researcher - sources market/tech intel",
                    "Developer - Claude Code implements changes",
                    "Reviewer/Tester - unit + e2e testing",
                    "Deployer - merges and triggers deployments",
                    "Memory/KM - syncs artifacts to storage",
                    "SEO - Gemini optimized content",
                    "Ops - health checks and self-healing"
                ],
                "flow": "Planner → Researcher → Developer → Reviewer → Deployer → Memory → SEO → Ops",
                "endpoints": [
                    "/webhook/brainops/trigger",
                    "/webhook/build",
                    "/webhook/deploy",
                    "/webhook/ingest"
                ]
            },
            "priority": 3,
            "status": "active",
            "implementation_status": "in_progress"
        },
        
        # AUREA Executive AI
        {
            "version": "2.0.0",
            "section": "aurea",
            "subsection": "capabilities",
            "content": {
                "modalities": ["chat", "voice (WebRTC/Twilio)", "screen-aware"],
                "capabilities": [
                    "Cross-system control via BrainOps-Core",
                    "Memory of founder preferences",
                    "Status rollups",
                    "Explain changes",
                    "Issue work orders"
                ],
                "security": ["voice prints", "device PINs", "audit logs"]
            },
            "priority": 3,
            "status": "active",
            "implementation_status": "operational"
        },
        
        # MyRoofGenius Platform
        {
            "version": "2.0.0",
            "section": "myroofgenius",
            "subsection": "architecture",
            "content": {
                "goals": "Public authority, collaborative hub, digital marketplace, AI SaaS",
                "monetization": {
                    "tiers": ["$97", "$297", "$997"],
                    "model": "Subscription + AI credits + marketplace"
                },
                "tech_stack": {
                    "frontend": "Next.js + Tailwind + Framer Motion",
                    "api": "FastAPI (MRG-API)",
                    "database": "Supabase (RLS per user/org)",
                    "payments": "Stripe subscriptions + credits"
                },
                "modules": [
                    "Marketplace (products, cart, checkout)",
                    "AI Estimator (gated by tier)",
                    "Content hub (blog/learn)",
                    "User portal (purchases, credits, projects)",
                    "AI Modifier (personalization)"
                ]
            },
            "priority": 3,
            "status": "active",
            "implementation_status": "operational"
        },
        
        # WeatherCraft ERP
        {
            "version": "2.0.0",
            "section": "weathercraft",
            "subsection": "modules",
            "content": {
                "design_intent": "Most advanced AI-native ERP, white-labelable SaaS-ready",
                "core_modules": {
                    "CRM": "Leads, accounts, contacts, opportunities",
                    "Estimating": "ITB intake, QTO, assemblies, pricing",
                    "Projects": "WBS, RFIs, submittals, permits",
                    "Field Ops": "Work orders, daily reports, photos",
                    "Scheduling": "Resource leveling, weather-aware",
                    "Procurement": "RFQs, POs, inventory",
                    "Equipment": "Maintenance, utilization",
                    "Financial": "QuickBooks/Stripe integration",
                    "Quality": "Inspections, safety, compliance",
                    "Analytics": "Executive dashboards"
                },
                "ai_copilots": [
                    "Spec compliance auditor",
                    "Assembly recommender",
                    "Proposal copywriter",
                    "Risk detector",
                    "Schedule optimizer"
                ]
            },
            "priority": 3,
            "status": "active",
            "implementation_status": "in_progress"
        },
        
        # Security & Compliance
        {
            "version": "2.0.0",
            "section": "security",
            "subsection": "principles",
            "content": {
                "principles": [
                    "Secrets only in managers (Render/Vercel/Supabase/1Password)",
                    "Never commit plaintext secrets",
                    "RLS everywhere, least-privilege",
                    "Audit logging for admin & AI actions"
                ],
                "critical_vars": [
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                    "GEMINI_API_KEY",
                    "SUPABASE_URL",
                    "STRIPE_SECRET_KEY",
                    "DATABASE_URL"
                ],
                "known_credentials": {
                    "docker_hub": "mwwoodworth",
                    "render_service": "srv-d1tfs4idbo4c73di6k00",
                    "mcp_sse_url": "https://us2.make.com/mcp/api/v1/u/ce87141a-1839-47d5-ac30-b56516091d8c/sse"
                }
            },
            "priority": 3,
            "status": "active",
            "implementation_status": "operational"
        },
        
        # CI/CD & Quality
        {
            "version": "2.0.0",
            "section": "cicd",
            "subsection": "github_actions",
            "content": {
                "workflows": {
                    "test.yml": "lint, type check, unit tests, build",
                    "deploy.yml": "on tag to main, deploy to Vercel/Render",
                    "security.yml": "Dependabot + audit + Trivy"
                },
                "test_requirements": {
                    "coverage": ">85%",
                    "frameworks": "pytest, Playwright",
                    "gates": "migrations dry run, feature flags off, smoke tests"
                }
            },
            "priority": 2,
            "status": "active",
            "implementation_status": "partial"
        },
        
        # SLOs & Observability
        {
            "version": "2.0.0",
            "section": "observability",
            "subsection": "slos",
            "content": {
                "slos": {
                    "api_p95": "<300ms for core endpoints",
                    "uptime": "≥99.9%",
                    "error_budget": "0.1% per month",
                    "search_p95": "<800ms for RAG"
                },
                "tools": ["Sentry", "OpenTelemetry"],
                "runbooks": [
                    "Auto-page on repeated 5xx",
                    "Rollbacks via feature flags",
                    "Kill-switch procedures"
                ]
            },
            "priority": 2,
            "status": "active",
            "implementation_status": "partial"
        }
    ]
    
    return sections

def insert_blueprint_data():
    """Insert parsed blueprint into operational context"""
    
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    try:
        # Get blueprint sections
        sections = parse_blueprint_sections()
        
        # Insert each section
        for section in sections:
            query = """
                INSERT INTO operational_blueprint 
                (version, section, subsection, content, priority, status, implementation_status, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (version, section, subsection) 
                DO UPDATE SET 
                    content = EXCLUDED.content,
                    priority = EXCLUDED.priority,
                    status = EXCLUDED.status,
                    implementation_status = EXCLUDED.implementation_status,
                    updated_at = NOW()
            """
            
            # Extract tags from content
            tags = []
            if section['section'] == 'executive':
                tags = ['critical', 'mission', 'strategy']
            elif section['section'] == 'system_landscape':
                tags = ['architecture', 'infrastructure']
            elif section['section'] == 'repositories':
                tags = ['code', 'version_control']
            elif section['section'] == 'ai_orchestration':
                tags = ['ai', 'automation', 'langgraph']
            elif section['section'] == 'security':
                tags = ['security', 'compliance', 'credentials']
            elif section['section'] == 'myroofgenius':
                tags = ['product', 'revenue', 'saas']
            elif section['section'] == 'weathercraft':
                tags = ['erp', 'crm', 'operations']
            else:
                tags = [section['section']]
            
            cur.execute(query, (
                section['version'],
                section['section'],
                section['subsection'],
                Json(section['content']),
                section['priority'],
                section['status'],
                section['implementation_status'],
                tags
            ))
        
        # Insert current system status
        system_components = [
            ('backend_api', 'healthy', 95.0, {'version': 'v8.8', 'url': 'https://brainops-backend-prod.onrender.com'}),
            ('myroofgenius', 'healthy', 97.0, {'score': '9.7/10', 'url': 'https://myroofgenius.com'}),
            ('weathercraft_erp', 'healthy', 85.0, {'status': 'integrated', 'url': 'https://weathercraft-erp.vercel.app'}),
            ('task_os', 'healthy', 90.0, {'status': 'operational', 'url': 'https://brainops-task-os.vercel.app'}),
            ('database', 'healthy', 100.0, {'tables': 313, 'provider': 'Supabase'}),
            ('ai_agents', 'healthy', 95.0, {'count': 15, 'neural_pathways': 210}),
            ('automations', 'healthy', 90.0, {'workflows': 8, 'status': 'active'}),
            ('centerpoint_sync', 'healthy', 85.0, {'capacity': '1.4M records', 'status': 'configured'})
        ]
        
        for component, status, health_score, metrics in system_components:
            cur.execute("""
                INSERT INTO operational_status (component, status, health_score, metrics)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (component) 
                DO UPDATE SET 
                    status = EXCLUDED.status,
                    health_score = EXCLUDED.health_score,
                    metrics = EXCLUDED.metrics,
                    updated_at = NOW()
            """, (component, status, health_score, Json(metrics)))
        
        # Insert critical paths
        critical_paths = [
            {
                "path_name": "docker_deployment",
                "path_type": "deployment",
                "steps": [
                    "Login to Docker Hub",
                    "Build Docker image with version tag",
                    "Tag image as latest",
                    "Push version tag",
                    "Push latest tag",
                    "Trigger Render webhook",
                    "Monitor deployment",
                    "Run health checks"
                ],
                "estimated_duration_minutes": 10
            },
            {
                "path_name": "database_migration",
                "path_type": "maintenance",
                "steps": [
                    "Backup current database",
                    "Create migration script",
                    "Test on staging",
                    "Apply to production",
                    "Verify schema",
                    "Update models",
                    "Deploy backend"
                ],
                "estimated_duration_minutes": 30
            },
            {
                "path_name": "emergency_recovery",
                "path_type": "recovery",
                "steps": [
                    "Identify failure point",
                    "Check system health",
                    "Rollback if needed",
                    "Fix root cause",
                    "Test fix locally",
                    "Deploy fix",
                    "Monitor recovery",
                    "Post-mortem"
                ],
                "estimated_duration_minutes": 60
            }
        ]
        
        for path in critical_paths:
            cur.execute("""
                INSERT INTO critical_paths (path_name, path_type, steps, estimated_duration_minutes)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (path_name) DO UPDATE SET
                    steps = EXCLUDED.steps,
                    updated_at = NOW()
            """, (path['path_name'], path['path_type'], Json(path['steps']), path['estimated_duration_minutes']))
        
        # Insert MCP integrations to track
        mcp_services = [
            ('Docker Hub', 13, 'pending', None, ['build', 'push', 'tag', 'list']),
            ('GitHub', 85, 'pending', None, ['repo', 'pr', 'issues', 'actions']),
            ('Stripe', 22, 'pending', None, ['payments', 'subscriptions', 'invoices']),
            ('Make.com', 20, 'connected', 'https://us2.make.com/mcp/api/v1/u/ce87141a-1839-47d5-ac30-b56516091d8c/sse', ['scenarios', 'webhooks']),
            ('Notion', 19, 'pending', None, ['pages', 'databases', 'blocks'])
        ]
        
        for service, tools, status, url, capabilities in mcp_services:
            cur.execute("""
                INSERT INTO mcp_integrations (service, tool_count, status, connection_url, capabilities)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (service) DO UPDATE SET
                    tool_count = EXCLUDED.tool_count,
                    status = EXCLUDED.status,
                    updated_at = NOW()
            """, (service, tools, status, url, Json(capabilities)))
        
        # Insert environment registry
        environments = [
            {
                "environment": "production",
                "service": "backend_api",
                "configuration": {
                    "url": "https://brainops-backend-prod.onrender.com",
                    "docker_image": "mwwoodworth/brainops-backend:latest",
                    "version": "v8.8"
                },
                "health_check_url": "https://brainops-backend-prod.onrender.com/api/v1/health",
                "deployment_url": "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"
            },
            {
                "environment": "production",
                "service": "myroofgenius",
                "configuration": {
                    "url": "https://myroofgenius.com",
                    "platform": "Vercel",
                    "framework": "Next.js 14"
                },
                "health_check_url": "https://myroofgenius.com",
                "deployment_url": "https://vercel.com/mwwoodworth/myroofgenius"
            },
            {
                "environment": "production",
                "service": "weathercraft_erp",
                "configuration": {
                    "url": "https://weathercraft-erp.vercel.app",
                    "platform": "Vercel",
                    "framework": "Next.js 14"
                },
                "health_check_url": "https://weathercraft-erp.vercel.app",
                "deployment_url": "https://vercel.com/mwwoodworth/weathercraft-erp"
            }
        ]
        
        for env in environments:
            cur.execute("""
                INSERT INTO environment_registry 
                (environment, service, configuration, health_check_url, deployment_url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (environment, service) DO UPDATE SET
                    configuration = EXCLUDED.configuration,
                    health_check_url = EXCLUDED.health_check_url,
                    deployment_url = EXCLUDED.deployment_url,
                    updated_at = NOW()
            """, (env['environment'], env['service'], Json(env['configuration']), 
                  env['health_check_url'], env['deployment_url']))
        
        conn.commit()
        print("✅ Blueprint successfully imported into operational context!")
        print(f"📊 Imported:")
        print(f"   - {len(sections)} blueprint sections")
        print(f"   - {len(system_components)} system status records")
        print(f"   - {len(critical_paths)} critical paths")
        print(f"   - {len(mcp_services)} MCP integrations")
        print(f"   - {len(environments)} environment configurations")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing blueprint: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 Importing BrainOps Blueprint into Operational Context System...")
    insert_blueprint_data()
    print("\n🎯 Operational context is now LIVE and will never lose track again!")