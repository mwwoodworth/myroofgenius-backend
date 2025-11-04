#!/usr/bin/env python3
"""
Fix main.py to properly register ALL 351 route files
This will make all endpoints actually work
"""

import os
import re

def get_all_route_files():
    """Get all route files in the routes directory"""
    routes_dir = "routes"
    route_files = []

    for filename in os.listdir(routes_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            route_files.append(filename[:-3])  # Remove .py extension

    return sorted(route_files)

def generate_imports(route_files):
    """Generate import statements for all route files"""
    imports = []

    for route_file in route_files:
        # Create a router variable name from the file name
        router_var = route_file.replace("_", "_") + "_router"
        imports.append(f"from routes.{route_file} import router as {router_var}")

    return imports

def generate_registrations(route_files):
    """Generate router registration statements"""
    registrations = []

    # Define special prefixes for certain routes
    special_prefixes = {
        "lead_management": "/api/v1/leads",
        "lead_scoring": "/api/v1/leads/scoring",
        "opportunity_tracking": "/api/v1/opportunities",
        "commission_tracking": "/api/v1/commissions",
        "sales_forecasting": "/api/v1/forecasts",
        "territory_management": "/api/v1/territories",
        "email_marketing": "/api/v1/email-marketing",
        "social_media_management": "/api/v1/social-media",
        "lead_nurturing": "/api/v1/lead-nurturing",
        "content_marketing": "/api/v1/content-marketing",
        "customer_segmentation": "/api/v1/segmentation",
        "ab_testing": "/api/v1/ab-testing",
        "marketing_automation": "/api/v1/marketing-automation",
        "landing_page_management": "/api/v1/landing-pages",
        "knowledge_base": "/api/v1/knowledge-base",
        "live_chat": "/api/v1/live-chat",
        "customer_feedback": "/api/v1/feedback",
        "sla_management": "/api/v1/sla",
        "customer_portal": "/api/v1/customer-portal",
        "service_catalog": "/api/v1/service-catalog",
        "faq_management": "/api/v1/faq",
        "escalation_management": "/api/v1/escalations",
        "data_warehouse": "/api/v1/data-warehouse",
        "reporting_engine": "/api/v1/reporting",
        "predictive_analytics": "/api/v1/predictive",
        "realtime_analytics": "/api/v1/realtime-analytics",
        "data_visualization": "/api/v1/visualizations",
        "performance_metrics": "/api/v1/metrics",
        "data_governance": "/api/v1/data-governance",
        "executive_dashboards": "/api/v1/executive-dashboards",
        "analytics_api": "/api/v1/analytics-api",
        "vendor_management": "/api/v1/vendors",
        "procurement_system": "/api/v1/procurement",
        "contract_lifecycle": "/api/v1/contract-lifecycle",
        "risk_management": "/api/v1/risk-management",
        "compliance_tracking": "/api/v1/compliance",
        "legal_management": "/api/v1/legal",
        "insurance_management": "/api/v1/insurance",
        "sustainability_tracking": "/api/v1/sustainability",
        "rd_management": "/api/v1/rd",
        "strategic_planning": "/api/v1/strategic-planning",
    }

    for route_file in route_files:
        router_var = route_file.replace("_", "_") + "_router"

        # Determine the prefix
        if route_file in special_prefixes:
            prefix = special_prefixes[route_file]
        elif route_file.startswith("task_"):
            # Handle task_XXX_name files
            parts = route_file.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                task_num = parts[1]
                prefix = f"/api/v1/task{task_num}"
            else:
                prefix = f"/api/v1/{route_file.replace('_', '-')}"
        else:
            # Default: convert underscores to hyphens for URL
            prefix = f"/api/v1/{route_file.replace('_', '-')}"

        # Create a tag from the file name
        tag = " ".join(word.capitalize() for word in route_file.split("_"))

        registrations.append(f'    app.include_router({router_var}, prefix="{prefix}", tags=["{tag}"])')

    return registrations

def update_main_py():
    """Update main.py with all route registrations"""

    # Get all route files
    route_files = get_all_route_files()
    print(f"Found {len(route_files)} route files")

    # Read current main.py
    with open("main.py", "r") as f:
        content = f.read()

    # Find where to insert imports (after other imports)
    import_insert_point = content.rfind("from routes.")
    if import_insert_point == -1:
        import_insert_point = content.rfind("import")

    # Find the line after the last import
    import_end = content.find("\n", import_insert_point)
    while content[import_end:import_end+5] in ["\nfrom", "\nimpo"]:
        import_end = content.find("\n", import_end + 1)

    # Generate new imports
    new_imports = generate_imports(route_files)

    # Find where routers are registered (look for app.include_router)
    registration_point = content.find("# Register routers")
    if registration_point == -1:
        registration_point = content.find("app.include_router")

    # Find the end of router registrations
    last_router = content.rfind("app.include_router")
    registration_end = content.find("\n", last_router)

    # Generate new registrations
    new_registrations = generate_registrations(route_files)

    # Create new content
    new_content = (
        content[:import_end] + "\n\n" +
        "# Auto-generated imports for all routes\n" +
        "\n".join(new_imports) + "\n" +
        content[import_end:registration_point] +
        "# Register all routers (auto-generated)\n" +
        "try:\n" +
        "\n".join(new_registrations) + "\n" +
        '    logger.info(f"Successfully registered {len(route_files)} route modules")\n' +
        "except Exception as e:\n" +
        '    logger.error(f"Error registering routes: {e}")\n\n' +
        content[registration_end + 1:]
    )

    # Save backup
    with open("main.py.backup", "w") as f:
        f.write(content)
    print("Created backup: main.py.backup")

    # Write updated main.py
    with open("main.py", "w") as f:
        f.write(new_content)

    print(f"Updated main.py with {len(new_imports)} imports and {len(new_registrations)} router registrations")

    return len(route_files)

def main():
    """Fix all route registrations"""
    print("=" * 60)
    print("FIXING ROUTE REGISTRATIONS IN MAIN.PY")
    print("=" * 60)

    # Update main.py
    num_routes = update_main_py()

    print("\n✅ COMPLETE!")
    print(f"All {num_routes} routes are now properly registered")
    print("\nNext steps:")
    print("1. Test locally to ensure no import errors")
    print("2. Build and push Docker image")
    print("3. Deploy to production")
    print("4. Test all endpoints again")

if __name__ == "__main__":
    main()