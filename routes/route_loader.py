"""
Dynamic route loader for all route modules
Automatically registers all routes from the routes directory
"""

import os
import importlib
import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)

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
        try:
            # Import the module
            module = importlib.import_module(f"routes.{module_name}")

            # Check if module has a router
            if hasattr(module, 'router'):
                router = module.router
                tag = " ".join(word.capitalize() for word in module_name.split("_"))
                prefix = f"/api/v1/{module_name.replace('_', '-')}"
                
                app.include_router(router, prefix=prefix, tags=[tag])
                loaded_count += 1
                logger.debug(f"Loaded route: {module_name} -> {prefix}")

            else:
                logger.warning(f"Module {module_name} has no router attribute")
                failed_count += 1

        except Exception as e:
            logger.error(f"Failed to load route {module_name}: {e}")
            failed_count += 1

    logger.info(f"Route loading complete: {loaded_count} loaded, {failed_count} failed")
    return loaded_count, failed_count
