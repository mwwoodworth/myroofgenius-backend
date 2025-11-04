-- POPULATE MASTER PERSISTENT MEMORY WITH COMPREHENSIVE SYSTEM KNOWLEDGE
-- This contains EVERYTHING about our systems - no more guessing!

BEGIN;

-- ============================================================================
-- SYSTEM ARCHITECTURE DOCUMENTATION
-- ============================================================================

-- 1. Backend API (FastAPI)
INSERT INTO system_architecture (
    component_id, component_name, component_type, description,
    technology_stack, dependencies, configuration, endpoints,
    deployment_info, monitoring_info, repository_url, live_url,
    health_status, health_percentage, version, tags
) VALUES (
    'backend-api',
    'BrainOps Backend API',
    'backend',
    'Main FastAPI backend providing all business logic, AI integrations, and API endpoints',
    '{
        "language": "Python 3.11",
        "framework": "FastAPI",
        "database": "PostgreSQL via Supabase",
        "orm": "SQLAlchemy",
        "auth": "JWT with CustomHTTPBearer",
        "ai_providers": ["Anthropic Claude", "Google Gemini", "OpenAI GPT-4"],
        "deployment": "Docker on Render",
        "monitoring": "Papertrail"
    }'::jsonb,
    '["PostgreSQL", "Redis", "Supabase", "Docker", "Render"]'::jsonb,
    '{
        "port": 10000,
        "workers": 1,
        "environment_variables": {
            "DATABASE_URL": "Required - PostgreSQL connection string",
            "JWT_SECRET_KEY": "Required - JWT signing key",
            "ANTHROPIC_API_KEY": "Required - Claude API",
            "GEMINI_API_KEY": "Required - Gemini API",
            "OPENAI_API_KEY": "Optional - GPT-4 API",
            "PAPERTRAIL_HOST": "logs.papertrailapp.com",
            "PAPERTRAIL_PORT": 34302
        },
        "docker_image": "mwwoodworth/brainops-backend:v4.35",
        "startup_command": "uvicorn apps.backend.main:app --host 0.0.0.0 --port 10000"
    }'::jsonb,
    '{
        "health": "/health",
        "api_health": "/api/v1/health",
        "auth": "/api/v1/auth/*",
        "leads": "/api/v1/leads/capture",
        "crm": "/api/v1/crm/*",
        "products": "/api/v1/products/*",
        "webhooks": "/api/v1/webhooks/vercel"
    }'::jsonb,
    '{
        "platform": "Render",
        "service_id": "srv-d1tfs4idbo4c73di6k00",
        "deploy_hook": "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM",
        "docker_registry": "Docker Hub",
        "docker_repo": "mwwoodworth/brainops-backend",
        "deployment_method": "Docker image push + manual trigger"
    }'::jsonb,
    '{
        "logs": "Papertrail - logs.papertrailapp.com:34302",
        "health_check": "GET /health every 30 seconds",
        "alerts": "Email on failure",
        "metrics": "Not configured yet"
    }'::jsonb,
    'https://github.com/mwwoodworth/fastapi-operator-env',
    'https://brainops-backend-prod.onrender.com',
    'operational',
    100.0,
    'v4.35',
    ARRAY['production', 'critical', 'revenue-generating']
);

-- 2. MyRoofGenius Frontend
INSERT INTO system_architecture (
    component_id, component_name, component_type, description,
    technology_stack, dependencies, configuration, deployment_info,
    repository_url, live_url, health_status, health_percentage, version, tags
) VALUES (
    'myroofgenius-frontend',
    'MyRoofGenius',
    'frontend',
    'AI-powered roofing business platform - PRIMARY REVENUE SOURCE',
    '{
        "framework": "Next.js 14.2.30",
        "language": "TypeScript",
        "styling": "Tailwind CSS",
        "ui_components": "shadcn/ui + Radix UI",
        "state_management": "React Context + useReducer",
        "auth": "NextAuth v4 + Supabase",
        "deployment": "Vercel",
        "animations": "Framer Motion",
        "3d": "Three.js + React Three Fiber"
    }'::jsonb,
    '["Backend API", "Supabase", "Stripe", "Anthropic Claude"]'::jsonb,
    '{
        "pricing_tiers": ["$97/month", "$297/month", "$997/month"],
        "features": {
            "starter": ["AI Estimator", "5 Projects/month", "Basic Support"],
            "professional": ["Everything in Starter", "Unlimited Projects", "Photo Analysis", "Priority Support"],
            "enterprise": ["Everything in Pro", "Custom Integrations", "White Label", "Dedicated Support"]
        },
        "api_endpoints": {
            "backend": "https://brainops-backend-prod.onrender.com",
            "supabase": "https://yomagoqdmxszqtdwuhab.supabase.co"
        }
    }'::jsonb,
    '{
        "platform": "Vercel",
        "auto_deploy": true,
        "branch": "main",
        "build_command": "npm run build",
        "output_directory": ".next",
        "node_version": "18.x"
    }'::jsonb,
    'https://github.com/mwwoodworth/myroofgenius-app',
    'https://www.myroofgenius.com',
    'operational',
    90.0,
    '1.0.0',
    ARRAY['production', 'revenue', 'critical', 'saas']
);

-- 3. WeatherCraft ERP
INSERT INTO system_architecture (
    component_id, component_name, component_type, description,
    technology_stack, dependencies, configuration, deployment_info,
    repository_url, live_url, health_status, health_percentage, version, tags
) VALUES (
    'weathercraft-erp',
    'WeatherCraft ERP',
    'frontend',
    'Complete ERP system for roofing contractors',
    '{
        "framework": "Next.js 14",
        "database": "PostgreSQL via Supabase",
        "orm": "Drizzle ORM",
        "ui": "Tailwind CSS + shadcn/ui",
        "auth": "Supabase Auth with RLS",
        "deployment": "Vercel"
    }'::jsonb,
    '["Supabase", "Backend API", "CenterPoint API"]'::jsonb,
    '{
        "modules": ["Dashboard", "CRM", "Projects", "Estimates", "Invoices", "Inventory", "Schedule"],
        "database_schema": "Service-focused, no marketplace",
        "centerpoint_sync": true,
        "api_url": "https://brainops-backend-prod.onrender.com"
    }'::jsonb,
    '{
        "platform": "Vercel",
        "auto_deploy": true,
        "branch": "main"
    }'::jsonb,
    'https://github.com/mwwoodworth/weathercraft-erp',
    'https://weathercraft-erp.vercel.app',
    'operational',
    95.0,
    '1.0.0',
    ARRAY['production', 'erp', 'centerpoint']
);

-- ============================================================================
-- STANDARD OPERATING PROCEDURES (SOPs)
-- ============================================================================

-- 1. Backend Deployment SOP
INSERT INTO system_sops (
    sop_id, title, description, category, steps, prerequisites,
    tools_required, expected_outcomes, error_handling, success_criteria
) VALUES (
    'deploy-backend-v4',
    'Deploy Backend API to Production',
    'Complete procedure for deploying FastAPI backend v4.x to Render via Docker',
    'deployment',
    '[
        {
            "step": 1,
            "action": "Update version in main.py and api_health.py",
            "command": "Edit VERSION = \"v4.XX\" in both files",
            "critical": true
        },
        {
            "step": 2,
            "action": "Commit changes to git",
            "command": "git add -A && git commit -m \"chore: Update to v4.XX\" && git push origin main",
            "critical": true
        },
        {
            "step": 3,
            "action": "Login to Docker Hub",
            "command": "docker login -u mwwoodworth -p ''dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho''",
            "critical": true
        },
        {
            "step": 4,
            "action": "Build Docker image",
            "command": "docker build -t mwwoodworth/brainops-backend:v4.XX -f Dockerfile .",
            "critical": true
        },
        {
            "step": 5,
            "action": "Tag as latest",
            "command": "docker tag mwwoodworth/brainops-backend:v4.XX mwwoodworth/brainops-backend:latest",
            "critical": true
        },
        {
            "step": 6,
            "action": "Push both tags to Docker Hub",
            "command": "docker push mwwoodworth/brainops-backend:v4.XX && docker push mwwoodworth/brainops-backend:latest",
            "critical": true
        },
        {
            "step": 7,
            "action": "Trigger Render deployment",
            "command": "Manual trigger in Render dashboard OR curl -X POST ''https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM''",
            "critical": true
        },
        {
            "step": 8,
            "action": "Monitor deployment logs",
            "command": "Watch Render dashboard for deployment status",
            "critical": false
        },
        {
            "step": 9,
            "action": "Verify deployment",
            "command": "curl https://brainops-backend-prod.onrender.com/api/v1/health",
            "critical": true
        }
    ]'::jsonb,
    '["Git repository up to date", "Docker installed", "Docker Hub access", "Render dashboard access"]'::jsonb,
    ARRAY['docker', 'git', 'curl'],
    '{
        "deployment_status": "success",
        "health_check": "200 OK",
        "version_updated": true,
        "no_errors": true
    }'::jsonb,
    '{
        "build_failure": "Check Dockerfile syntax, ensure all dependencies installed",
        "push_failure": "Re-login to Docker Hub, check internet connection",
        "render_failure": "Check Render logs, verify environment variables",
        "health_check_failure": "Check startup logs, verify database connection"
    }'::jsonb,
    '{
        "health_endpoint_returns_200": true,
        "version_matches_expected": true,
        "all_routes_loading": true,
        "no_startup_errors": true
    }'::jsonb
);

-- 2. Generate Traffic SOP
INSERT INTO system_sops (
    sop_id, title, description, category, steps, tools_required, success_criteria
) VALUES (
    'generate-traffic-myroofgenius',
    'Generate Traffic to MyRoofGenius',
    'Comprehensive traffic generation strategy for revenue',
    'revenue',
    '[
        {
            "step": 1,
            "action": "Reddit Posts",
            "details": {
                "subreddits": ["r/roofing", "r/Construction", "r/smallbusiness", "r/Entrepreneur"],
                "post_titles": [
                    "Just launched AI roofing estimator - 14 day free trial",
                    "AI tool that does roof estimates in 30 seconds",
                    "How we automated our roofing estimates"
                ],
                "frequency": "2-3 posts per day",
                "best_times": "9am, 12pm, 5pm EST"
            }
        },
        {
            "step": 2,
            "action": "LinkedIn Outreach",
            "details": {
                "target": "Roofing contractors, construction business owners",
                "connection_message": "Hi [Name], I noticed you run [Company]. We just launched MyRoofGenius - AI-powered roofing software. Would love to connect!",
                "follow_up": "Send personalized message about free trial",
                "goal": "20 connections per day"
            }
        },
        {
            "step": 3,
            "action": "Google Ads Campaign",
            "details": {
                "budget": "$50/day initial test",
                "keywords": [
                    "roofing estimation software",
                    "ai roofing calculator",
                    "roofing business software"
                ],
                "landing_page": "https://www.myroofgenius.com/pricing",
                "conversion_tracking": "Setup with Google Tag Manager"
            }
        },
        {
            "step": 4,
            "action": "Facebook Groups",
            "details": {
                "groups": [
                    "Roofing Contractors Network",
                    "Construction Business Owners",
                    "Small Business Automation"
                ],
                "post_strategy": "Share value first, mention tool second",
                "frequency": "1 post per group per week"
            }
        },
        {
            "step": 5,
            "action": "Direct Email Outreach",
            "details": {
                "template": "Subject: Save 25 hours/week on roofing estimates",
                "target": "Roofing companies from Google Maps",
                "volume": "50 emails per day",
                "follow_up": "After 3 days if no response"
            }
        }
    ]'::jsonb,
    ARRAY['Reddit account', 'LinkedIn account', 'Google Ads account', 'Email tool'],
    '{
        "daily_visitors": 100,
        "trial_signups": 5,
        "conversion_rate": "5%",
        "first_paying_customer": true
    }'::jsonb
);

-- 3. Fix Frontend API 405 Error SOP
INSERT INTO system_sops (
    sop_id, title, description, category, steps, error_handling
) VALUES (
    'fix-frontend-405-error',
    'Fix Frontend API Route 405 Errors',
    'Workaround for Next.js API route deployment issues',
    'debugging',
    '[
        {
            "step": 1,
            "action": "Identify the problematic route",
            "command": "Check browser console for 405 error on specific endpoint"
        },
        {
            "step": 2,
            "action": "Verify route file exists",
            "command": "ls -la src/app/api/[endpoint]/route.ts"
        },
        {
            "step": 3,
            "action": "Check HTTP methods exported",
            "command": "Ensure both GET and POST are exported if needed"
        },
        {
            "step": 4,
            "action": "Workaround - Use backend directly",
            "command": "Replace frontend API call with: https://brainops-backend-prod.onrender.com/api/v1/[endpoint]"
        },
        {
            "step": 5,
            "action": "Update CORS if needed",
            "command": "Ensure backend allows frontend domain in CORS settings"
        }
    ]'::jsonb,
    '{
        "vercel_deployment_issue": "Redeploy with cache cleared",
        "route_not_found": "Check file naming and exports",
        "cors_error": "Update backend CORS configuration"
    }'::jsonb
);

-- ============================================================================
-- SYSTEM CONFIGURATIONS
-- ============================================================================

-- UI/UX Design System
INSERT INTO ui_specifications (
    spec_id, component_name, component_type, design_system,
    colors, typography, spacing, animations, accessibility
) VALUES (
    'myroofgenius-design-system',
    'MyRoofGenius Design System',
    'design-system',
    'Custom with Tailwind',
    '{
        "primary": "#3B82F6",
        "primary_hover": "#2563EB",
        "secondary": "#10B981",
        "accent": "#F59E0B",
        "background": "#FFFFFF",
        "surface": "#F9FAFB",
        "text_primary": "#111827",
        "text_secondary": "#6B7280",
        "error": "#EF4444",
        "success": "#10B981",
        "warning": "#F59E0B",
        "info": "#3B82F6",
        "dark_mode": {
            "background": "#111827",
            "surface": "#1F2937",
            "text_primary": "#F9FAFB",
            "text_secondary": "#D1D5DB"
        }
    }'::jsonb,
    '{
        "font_family": "Inter, system-ui, sans-serif",
        "heading_sizes": {
            "h1": "text-5xl font-bold",
            "h2": "text-4xl font-semibold",
            "h3": "text-3xl font-semibold",
            "h4": "text-2xl font-medium",
            "h5": "text-xl font-medium",
            "h6": "text-lg font-medium"
        },
        "body_sizes": {
            "large": "text-lg",
            "base": "text-base",
            "small": "text-sm",
            "tiny": "text-xs"
        },
        "line_heights": {
            "tight": "leading-tight",
            "normal": "leading-normal",
            "relaxed": "leading-relaxed"
        }
    }'::jsonb,
    '{
        "spacing_scale": {
            "xs": "0.25rem",
            "sm": "0.5rem",
            "md": "1rem",
            "lg": "1.5rem",
            "xl": "2rem",
            "2xl": "3rem",
            "3xl": "4rem"
        },
        "container_padding": "px-4 sm:px-6 lg:px-8",
        "section_spacing": "py-12 sm:py-16 lg:py-20",
        "card_padding": "p-6",
        "button_padding": "px-4 py-2"
    }'::jsonb,
    '{
        "transitions": {
            "fast": "transition-all duration-150 ease-in-out",
            "base": "transition-all duration-300 ease-in-out",
            "slow": "transition-all duration-500 ease-in-out"
        },
        "hover_scale": "hover:scale-105",
        "hover_shadow": "hover:shadow-lg",
        "fade_in": "animate-fadeIn",
        "slide_up": "animate-slideUp"
    }'::jsonb,
    '{
        "focus_visible": "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary",
        "aria_labels": true,
        "keyboard_navigation": true,
        "screen_reader_support": true,
        "contrast_ratio": "WCAG AA compliant"
    }'::jsonb
);

-- Critical Environment Variables
INSERT INTO system_configurations (
    config_key, config_value, component, environment, category, is_secret, is_required
) VALUES
    ('DATABASE_URL', '{"value": "postgresql://postgres:Brain0ps2O2S@db.yomagoqdmxszqtdwuhab.supabase.co:5432/postgres"}'::jsonb, 'backend', 'production', 'database', true, true),
    ('SUPABASE_URL', '{"value": "https://yomagoqdmxszqtdwuhab.supabase.co"}'::jsonb, 'all', 'production', 'database', false, true),
    ('SUPABASE_ANON_KEY', '{"value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk4MzMyNzYsImV4cCI6MjA2NTQwOTI3Nn0.gKC0PybkqPTLlzDWIdS8a6KFVXZ1PQaNcQr2ekroxzE"}'::jsonb, 'frontend', 'production', 'auth', true, true),
    ('SUPABASE_SERVICE_KEY', '{"value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlvbWFnb3FkbXhzenF0ZHd1aGFiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTgzMzI3NiwiZXhwIjoyMDY1NDA5Mjc2fQ.7C3guJ_0moYGkdyeFmJ9cd2BmduB5NnU00erIIxH3gQ"}'::jsonb, 'backend', 'production', 'auth', true, true),
    ('DOCKER_USERNAME', '{"value": "mwwoodworth"}'::jsonb, 'deployment', 'production', 'deployment', false, true),
    ('DOCKER_PAT', '{"value": "dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho"}'::jsonb, 'deployment', 'production', 'deployment', true, true),
    ('RENDER_DEPLOY_HOOK', '{"value": "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM"}'::jsonb, 'deployment', 'production', 'deployment', true, true),
    ('STRIPE_PUBLISHABLE_KEY', '{"value": "pk_live_51PnM0CIWpMBRJ2y3pE5L9mnLT0d7KN0KkHHBRl2qTELGubivgKHraXfRKxvZCOLTNfIvqICysHIyQLqVQxrrK0oB00ctBfxRhZ"}'::jsonb, 'frontend', 'production', 'payment', false, true),
    ('STRIPE_SECRET_KEY', '{"value": "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"}'::jsonb, 'backend', 'production', 'payment', true, true);

-- ============================================================================
-- CRITICAL PERSISTENT MEMORIES
-- ============================================================================

INSERT INTO persistent_memory (
    memory_key, memory_value, category, subcategory, importance
) VALUES
    ('revenue_critical', 
     '{"fact": "MyRoofGenius is the ONLY revenue source", "centerpoint": "CenterPoint is NOT revenue - just data", "focus": "Generate paying customers for MyRoofGenius"}'::jsonb,
     'critical', 'revenue', 10),
    
    ('system_status_current',
     '{"backend": "v4.35 operational", "myroofgenius": "90% operational", "weathercraft": "95% operational", "overall_health": "81.8%", "date": "2025-08-17"}'::jsonb,
     'status', 'current', 9),
    
    ('pricing_tiers',
     '{"starter": "$97/month", "professional": "$297/month", "enterprise": "$997/month", "billing": "Stripe", "trial": "14 days free"}'::jsonb,
     'revenue', 'pricing', 10),
    
    ('lead_capture_workaround',
     '{"issue": "Frontend API routes return 405", "workaround": "Use backend directly at https://brainops-backend-prod.onrender.com/api/v1/leads/capture", "method": "POST", "fix_priority": "low"}'::jsonb,
     'issues', 'workarounds', 8),
    
    ('deployment_credentials',
     '{"docker_hub": "mwwoodworth / dckr_pat_iI44t5EXTpawhU8Rwnc91ETcZho", "render_hook": "https://api.render.com/deploy/srv-d1tfs4idbo4c73di6k00?key=t2qc-8j6xrM", "vercel": "Auto-deploy on git push"}'::jsonb,
     'credentials', 'deployment', 10),
    
    ('testing_results_latest',
     '{"date": "2025-08-17", "backend": "100%", "myroofgenius": "90%", "weathercraft": "95%", "lead_api": "405 error", "overall": "81.8%"}'::jsonb,
     'testing', 'results', 7);

-- ============================================================================
-- DEPLOYMENT HISTORY
-- ============================================================================

INSERT INTO deployment_history (
    deployment_id, component, version, environment, deployment_type,
    deployment_status, deployment_steps, configuration_used,
    started_at, completed_at, deployed_by, notes
) VALUES
    ('deploy-backend-v435', 'backend', 'v4.35', 'production', 'docker',
     'success',
     '["Updated version", "Built Docker image", "Pushed to Docker Hub", "Triggered Render deployment", "Verified health"]'::jsonb,
     '{"docker_image": "mwwoodworth/brainops-backend:v4.35", "simplified": true}'::jsonb,
     '2025-08-17 00:00:00', '2025-08-17 00:15:00', 'claude',
     'Simplified backend to fix deployment issues - removed complex routes, kept essential endpoints'),
    
    ('deploy-backend-v434', 'backend', 'v4.34', 'production', 'docker',
     'failed',
     '["Updated version", "Built Docker image", "Pushed to Docker Hub", "Render deployment failed"]'::jsonb,
     '{"docker_image": "mwwoodworth/brainops-backend:v4.34"}'::jsonb,
     '2025-08-16 23:00:00', '2025-08-16 23:30:00', 'claude',
     'Deployment failed due to startup errors - too complex'),
    
    ('deploy-backend-v433', 'backend', 'v4.33', 'production', 'docker',
     'failed',
     '["Updated version", "Built Docker image", "Pushed to Docker Hub", "Render deployment failed"]'::jsonb,
     '{"docker_image": "mwwoodworth/brainops-backend:v4.33"}'::jsonb,
     '2025-08-16 22:00:00', '2025-08-16 22:30:00', 'claude',
     'Initial v4.33 deployment failed - status showed update_failed');

-- ============================================================================
-- DECISION LOG
-- ============================================================================

INSERT INTO decision_log (
    decision_id, title, description, category, context,
    options_considered, decision_made, reasoning, actual_outcome
) VALUES
    ('simplify-backend-v435',
     'Simplify Backend to v4.35',
     'Create minimal backend with only essential endpoints',
     'architecture',
     '{"problem": "v4.33 and v4.34 failing to deploy", "errors": "Complex routes causing startup failures"}'::jsonb,
     '["Fix complex routes", "Debug startup errors", "Simplify to essential endpoints only"]'::jsonb,
     'Simplify to essential endpoints only',
     'Faster to get operational system than debugging complex issues. Can add features back incrementally.',
     '{"result": "success", "deployment": "working", "health": "100%"}'::jsonb),
    
    ('revenue-focus-myroofgenius',
     'Focus All Efforts on MyRoofGenius Revenue',
     'Prioritize MyRoofGenius as sole revenue source',
     'business',
     '{"analysis": "CenterPoint provides data but no revenue", "myroofgenius": "Has pricing and payment ready"}'::jsonb,
     '["Focus on CenterPoint integration", "Focus on MyRoofGenius revenue", "Split efforts equally"]'::jsonb,
     'Focus on MyRoofGenius revenue',
     'MyRoofGenius has pricing tiers, Stripe integration, and is ready for customers. CenterPoint is just data.',
     '{"result": "correct", "focus": "clear", "next_steps": "generate_traffic"}'::jsonb);

-- ============================================================================
-- ERROR PATTERNS
-- ============================================================================

INSERT INTO error_patterns (
    error_id, error_message, error_type, component, root_cause,
    immediate_fix, permanent_fix, severity
) VALUES
    ('frontend-api-405',
     'Method Not Allowed - 405',
     'deployment',
     'myroofgenius-frontend',
     'Next.js API routes not properly deployed on Vercel',
     '{"workaround": "Use backend API directly"}'::jsonb,
     '{"solution": "Debug Vercel deployment configuration", "priority": "low"}'::jsonb,
     'medium'),
    
    ('backend-startup-failure',
     'Container failed to start',
     'deployment',
     'backend',
     'Too many complex routes causing import errors',
     '{"fix": "Simplify to essential routes only"}'::jsonb,
     '{"solution": "Incrementally add routes back with testing"}'::jsonb,
     'critical');

COMMIT;

-- Verify data was inserted
DO $$
DECLARE
    memory_count INTEGER;
    sop_count INTEGER;
    arch_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO memory_count FROM persistent_memory;
    SELECT COUNT(*) INTO sop_count FROM system_sops;
    SELECT COUNT(*) INTO arch_count FROM system_architecture;
    
    RAISE NOTICE 'Persistent Memory Population Complete!';
    RAISE NOTICE 'Memories stored: %', memory_count;
    RAISE NOTICE 'SOPs documented: %', sop_count;
    RAISE NOTICE 'Architecture components: %', arch_count;
    RAISE NOTICE '';
    RAISE NOTICE '✅ System knowledge fully documented and persistent!';
END $$;