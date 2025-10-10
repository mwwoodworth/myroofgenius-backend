"""
Edge Optimization for Colorado Springs
Provides location-based caching, CDN headers, and performance optimization
"""

from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import hashlib
import json
from datetime import datetime, timedelta
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/edge", tags=["Edge Optimization"])

# Colorado Springs coordinates and configuration
COLORADO_SPRINGS = {
    "lat": 38.8339,
    "lon": -104.8214,
    "timezone": "America/Denver",
    "cdn_region": "us-west-2",
    "cache_duration": {
        "static": 31536000,  # 1 year for static assets
        "api": 300,          # 5 minutes for API responses
        "dynamic": 0,        # No cache for dynamic content
        "weather": 3600,     # 1 hour for weather data
        "estimates": 86400   # 24 hours for estimates
    }
}

# Cache store for edge responses
edge_cache = {}

def get_cache_key(path: str, params: dict) -> str:
    """Generate cache key from path and parameters"""
    data = f"{path}:{json.dumps(params, sort_keys=True)}"
    return hashlib.md5(data.encode()).hexdigest()

def get_cache_headers(content_type: str = "api", location: str = "colorado_springs") -> dict:
    """Get optimized cache headers for Colorado Springs"""
    duration = COLORADO_SPRINGS["cache_duration"].get(content_type, 0)

    headers = {
        "Cache-Control": f"public, max-age={duration}" if duration else "no-cache",
        "X-Edge-Location": location.upper(),
        "X-CDN-Region": COLORADO_SPRINGS["cdn_region"],
        "X-Cache-Status": "HIT" if duration else "MISS"
    }

    if duration:
        expires = datetime.utcnow() + timedelta(seconds=duration)
        headers["Expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")

    return headers

@lru_cache(maxsize=1000)
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points (simple approximation)"""
    import math
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

@router.get("/status")
async def edge_status(request: Request):
    """Get edge optimization status"""

    # Check if request is from Colorado Springs area
    client_ip = request.client.host if request.client else "unknown"

    # In production, you'd use a GeoIP service here
    # For now, we'll assume local requests are from Colorado Springs
    is_local = client_ip.startswith("127.") or client_ip.startswith("192.168.")

    return JSONResponse(
        content={
            "edge_location": "Colorado Springs, CO",
            "coordinates": {
                "lat": COLORADO_SPRINGS["lat"],
                "lon": COLORADO_SPRINGS["lon"]
            },
            "cdn_region": COLORADO_SPRINGS["cdn_region"],
            "cache_config": COLORADO_SPRINGS["cache_duration"],
            "optimized": True,
            "client_ip": client_ip,
            "is_local": is_local,
            "timestamp": datetime.utcnow().isoformat()
        },
        headers=get_cache_headers("api")
    )

@router.get("/optimize/{path:path}")
async def optimize_request(path: str, request: Request):
    """Optimize any request through edge caching"""

    # Generate cache key
    query_params = dict(request.query_params)
    cache_key = get_cache_key(path, query_params)

    # Check cache
    if cache_key in edge_cache:
        cached = edge_cache[cache_key]
        if cached["expires"] > datetime.utcnow():
            logger.info(f"Cache HIT for {path}")
            return JSONResponse(
                content=cached["data"],
                headers={**get_cache_headers("api"), "X-Cache-Status": "HIT"}
            )

    # Cache MISS - in production, this would proxy to the actual endpoint
    logger.info(f"Cache MISS for {path}")

    # Simulate response (in production, call actual endpoint)
    response_data = {
        "path": path,
        "params": query_params,
        "optimized": True,
        "edge_location": "Colorado Springs",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Store in cache
    edge_cache[cache_key] = {
        "data": response_data,
        "expires": datetime.utcnow() + timedelta(seconds=COLORADO_SPRINGS["cache_duration"]["api"])
    }

    return JSONResponse(
        content=response_data,
        headers={**get_cache_headers("api"), "X-Cache-Status": "MISS"}
    )

@router.post("/purge")
async def purge_cache(pattern: Optional[str] = None):
    """Purge edge cache"""

    if pattern:
        # Purge specific pattern
        keys_to_remove = [k for k in edge_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del edge_cache[key]
        purged = len(keys_to_remove)
    else:
        # Purge all
        purged = len(edge_cache)
        edge_cache.clear()

    return {
        "status": "success",
        "purged_keys": purged,
        "message": f"Purged {purged} cache entries"
    }

@router.get("/weather")
async def get_local_weather():
    """Get Colorado Springs weather (cached for 1 hour)"""

    # Check cache
    cache_key = "weather_colorado_springs"
    if cache_key in edge_cache:
        cached = edge_cache[cache_key]
        if cached["expires"] > datetime.utcnow():
            return JSONResponse(
                content=cached["data"],
                headers={**get_cache_headers("weather"), "X-Cache-Status": "HIT"}
            )

    # Simulate weather data (in production, call weather API)
    weather_data = {
        "location": "Colorado Springs, CO",
        "temperature": 72,
        "conditions": "Partly Cloudy",
        "humidity": 35,
        "wind_speed": 8,
        "ideal_for_roofing": True,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Cache it
    edge_cache[cache_key] = {
        "data": weather_data,
        "expires": datetime.utcnow() + timedelta(seconds=COLORADO_SPRINGS["cache_duration"]["weather"])
    }

    return JSONResponse(
        content=weather_data,
        headers={**get_cache_headers("weather"), "X-Cache-Status": "MISS"}
    )

@router.get("/nearest-crew")
async def get_nearest_crew(lat: Optional[float] = None, lon: Optional[float] = None):
    """Find nearest crew to location (defaults to Colorado Springs)"""

    if not lat or not lon:
        lat = COLORADO_SPRINGS["lat"]
        lon = COLORADO_SPRINGS["lon"]

    # Simulate crew locations
    crews = [
        {"id": 1, "name": "Alpha Team", "lat": 38.8339, "lon": -104.8214, "available": True},
        {"id": 2, "name": "Bravo Team", "lat": 38.8462, "lon": -104.8004, "available": True},
        {"id": 3, "name": "Charlie Team", "lat": 38.8125, "lon": -104.8231, "available": False},
    ]

    # Calculate distances
    for crew in crews:
        crew["distance_km"] = calculate_distance(lat, lon, crew["lat"], crew["lon"])

    # Sort by distance and filter available
    available_crews = [c for c in crews if c["available"]]
    available_crews.sort(key=lambda x: x["distance_km"])

    return JSONResponse(
        content={
            "request_location": {"lat": lat, "lon": lon},
            "nearest_crew": available_crews[0] if available_crews else None,
            "all_crews": crews,
            "edge_optimized": True
        },
        headers=get_cache_headers("api")
    )

@router.get("/performance-metrics")
async def get_performance_metrics():
    """Get edge performance metrics"""

    total_cached = len(edge_cache)
    active_cached = sum(1 for v in edge_cache.values() if v["expires"] > datetime.utcnow())

    return {
        "edge_location": "Colorado Springs, CO",
        "metrics": {
            "total_cached_items": total_cached,
            "active_cached_items": active_cached,
            "cache_hit_rate": 0.75,  # Simulated
            "avg_response_time_ms": 42,  # Simulated
            "bandwidth_saved_mb": active_cached * 0.1,  # Rough estimate
        },
        "optimization": {
            "cdn_enabled": True,
            "compression": "gzip",
            "http2": True,
            "server_push": False
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# CDN configuration for static assets
CDN_CONFIG = {
    "providers": {
        "cloudflare": {
            "enabled": True,
            "zone": "myroofgenius.com",
            "cache_level": "aggressive"
        },
        "fastly": {
            "enabled": False,
            "service_id": None
        }
    },
    "rules": [
        {
            "pattern": "*.jpg|*.png|*.gif|*.webp",
            "cache_duration": 31536000,  # 1 year
            "compress": True
        },
        {
            "pattern": "*.js|*.css",
            "cache_duration": 86400,  # 1 day
            "compress": True,
            "minify": True
        },
        {
            "pattern": "/api/v1/estimates/*",
            "cache_duration": 3600,  # 1 hour
            "vary": ["Accept", "Authorization"]
        }
    ]
}

@router.get("/cdn-config")
async def get_cdn_config():
    """Get CDN configuration for Colorado Springs optimization"""
    return {
        "location": "Colorado Springs, CO",
        "config": CDN_CONFIG,
        "recommendations": [
            "Use Cloudflare's Denver PoP for lowest latency",
            "Enable Argo Smart Routing for 30% faster responses",
            "Use Workers for edge compute near Colorado Springs",
            "Enable Polish for automatic image optimization"
        ]
    }