"""
Dynamic route loader for all route modules
Automatically registers all routes from the routes directory
"""

import os
import importlib
import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Define route mappings (file_name -> prefix)
ROUTE_MAPPINGS = {
    # Core business routes
    "products_api": "/api/v1/products",

    # Tasks 61-70: Sales & CRM
    "lead_management": "/api/v1/leads",
    "opportunity_tracking": "/api/v1/opportunities",
    "sales_pipeline": "/api/v1/pipelines",
    "quote_management": "/api/v1/quotes",
    "proposal_generation": "/api/v1/proposals",
    "contract_management": "/api/v1/contracts",
    "commission_tracking": "/api/v1/commissions",
    "sales_forecasting": "/api/v1/forecasts",
    "territory_management": "/api/v1/territories",
    "sales_analytics": "/api/v1/sales/analytics",

    # Tasks 71-80: Marketing
    "campaign_management": "/api/v1/campaigns",
    "email_marketing": "/api/v1/email-marketing",
    "social_media_management": "/api/v1/social-media",
    "lead_nurturing": "/api/v1/lead-nurturing",
    "content_marketing": "/api/v1/content-marketing",
    "marketing_analytics": "/api/v1/marketing/analytics",
    "customer_segmentation": "/api/v1/segmentation",
    "ab_testing": "/api/v1/ab-testing",
    "marketing_automation": "/api/v1/marketing-automation",
    "landing_page_management": "/api/v1/landing-pages",

    # Tasks 81-90: Customer Service
    "ticket_management": "/api/v1/tickets",
    "knowledge_base": "/api/v1/knowledge-base",
    "live_chat": "/api/v1/live-chat",
    "customer_feedback": "/api/v1/feedback",
    "sla_management": "/api/v1/sla",
    "customer_portal": "/api/v1/customer-portal",
    "service_catalog": "/api/v1/service-catalog",
    "faq_management": "/api/v1/faq",
    "support_analytics": "/api/v1/support/analytics",
    "escalation_management": "/api/v1/escalations",

    # Tasks 91-100: Analytics & BI
    "business_intelligence": "/api/v1/analytics/bi",
    "data_warehouse": "/api/v1/data-warehouse",
    "reporting_engine": "/api/v1/reporting",
    "predictive_analytics": "/api/v1/predictive",
    "realtime_analytics": "/api/v1/realtime-analytics",
    "data_visualization": "/api/v1/visualizations",
    "performance_metrics": "/api/v1/metrics",
    "data_governance": "/api/v1/data-governance",
    "executive_dashboards": "/api/v1/executive-dashboards",
    "analytics_api": "/api/v1/analytics-api",

    # Tasks 101-110: Advanced Operations
    "vendor_management": "/api/v1/vendors",
    "procurement_system": "/api/v1/procurement",
    "contract_lifecycle": "/api/v1/contract-lifecycle",
    "risk_management": "/api/v1/risk-management",
    "compliance_tracking": "/api/v1/compliance",
    "legal_management": "/api/v1/legal",
    "insurance_management": "/api/v1/insurance",
    "sustainability_tracking": "/api/v1/sustainability",
    "rd_management": "/api/v1/rd_projects",
    "strategic_planning": "/api/v1/strategic-planning",
}

EXCLUDED_MODULES = {
    # Replaced by routes.erp_core_runtime which provides resilient implementations
    "complete_erp",
}

def load_all_routes(app: FastAPI):
    """
    Dynamically load all route files from the routes directory
    """
    routes_dir = os.path.dirname(__file__)
    loaded_count = 0
    failed_count = 0
    skipped_files = ["__init__.py", "route_loader.py", "__pycache__"]

    # Get all Python files in routes directory
    route_files = []
    for filename in os.listdir(routes_dir):
        if filename.endswith(".py") and filename not in skipped_files:
            module_name = filename[:-3]  # Remove .py extension
            route_files.append(module_name)

    logger.info(f"Found {len(route_files)} route files to load")

    # Load each route file
    for module_name in sorted(route_files):
        if module_name in EXCLUDED_MODULES:
            logger.info(f"Skipping route module {module_name} (handled elsewhere)")
            continue
        try:
            # Import the module
            module = importlib.import_module(f"routes.{module_name}")

            # Check if module has a router
            if hasattr(module, 'router'):
                router = module.router

                # Create tag from module name
                tag = " ".join(word.capitalize() for word in module_name.split("_"))

                # FIX v148: Check if router already has a prefix
                # If it does, use it directly (don't add another prefix)
                if hasattr(router, 'prefix') and router.prefix:
                    # Router already has its own prefix, use it as-is
                    app.include_router(router, tags=[tag])
                    loaded_count += 1
                    if loaded_count <= 10 or loaded_count % 50 == 0:
                        logger.debug(f"Loaded route: {module_name} (using router prefix: {router.prefix})")
                else:
                    # Router has no prefix, we need to provide one
                    if module_name in ROUTE_MAPPINGS:
                        prefix = ROUTE_MAPPINGS[module_name]
                    elif module_name.startswith("task_"):
                        # Handle task_XXX_name files
                        parts = module_name.split("_")
                        if len(parts) >= 2 and parts[1].isdigit():
                            task_num = parts[1]
                            prefix = f"/api/v1/task{task_num}"
                        else:
                            prefix = f"/api/v1/{module_name.replace('_', '-')}"
                    else:
                        # Default: convert underscores to hyphens
                        prefix = f"/api/v1/{module_name.replace('_', '-')}"

                    # Register the router WITH our prefix
                    app.include_router(router, prefix=prefix, tags=[tag])
                    loaded_count += 1

                    if loaded_count <= 10 or loaded_count % 50 == 0:
                        logger.debug(f"Loaded route: {module_name} -> {prefix}")

            else:
                logger.warning(f"Module {module_name} has no router attribute")
                failed_count += 1

        except Exception as e:
            logger.error(f"Failed to load route {module_name}: {e}")
            failed_count += 1

    logger.info(f"Route loading complete: {loaded_count} loaded, {failed_count} failed")
    return loaded_count, failed_count
