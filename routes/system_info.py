"""
System info endpoints for version + route discovery.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.routing import APIRoute

from version import __version__, __build__, __status__


router = APIRouter(prefix="/api/v1", tags=["System"])


@router.get("/version")
def get_version():
    return {
        "version": __version__,
        "build": __build__,
        "status": __status__,
    }


@router.get("/routes")
def list_routes(request: Request):
    routes = []
    for route in request.app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = sorted(m for m in (route.methods or []) if m not in {"HEAD", "OPTIONS"})
        routes.append(
            {
                "path": route.path,
                "methods": methods,
                "name": route.name,
            }
        )

    return {
        "count": len(routes),
        "routes": routes,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
