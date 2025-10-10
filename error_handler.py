"""
Global Error Handler for Commercial Grade Operation
Ensures no crashes and provides meaningful error responses
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from typing import Any

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch all unhandled exceptions and return graceful error response
    """
    # Log the full error for debugging
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())

    # Return user-friendly error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Our team has been notified.",
            "detail": str(exc) if logger.level <= logging.DEBUG else None,
            "request_id": request.headers.get("X-Request-Id", "unknown")
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation errors with clear messages
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "The request data is invalid",
            "errors": errors
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with consistent format
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "path": request.url.path
        }
    )

def add_error_handlers(app):
    """
    Add all error handlers to the FastAPI app
    """
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

def safe_endpoint(func):
    """
    Decorator to wrap endpoints in try-catch
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Endpoint error in {func.__name__}: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Operation failed",
                    "message": str(e)
                }
            )
    wrapper.__name__ = func.__name__
    return wrapper