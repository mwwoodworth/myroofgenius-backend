"""
Custom exceptions and error handling
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class BrainOpsException(Exception):
    """Base exception for BrainOps platform"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class AIProviderError(BrainOpsException):
    """AI provider related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )

class AIQuotaExceededError(AIProviderError):
    """AI provider quota exceeded"""
    
    def __init__(self, provider: str, reset_time: Optional[datetime] = None):
        details = {"provider": provider}
        if reset_time:
            details["reset_time"] = reset_time.isoformat()
        super().__init__(
            message=f"Quota exceeded for {provider}",
            details=details
        )

class DatabaseError(BrainOpsException):
    """Database related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )

class AuthenticationError(BrainOpsException):
    """Authentication errors"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class AuthorizationError(BrainOpsException):
    """Authorization errors"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )

class ValidationError(BrainOpsException):
    """Input validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

class RateLimitError(BrainOpsException):
    """Rate limiting errors"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )

class ResourceNotFoundError(BrainOpsException):
    """Resource not found errors"""
    
    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            message=f"{resource} with id {resource_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "id": str(resource_id)}
        )

class ExternalServiceError(BrainOpsException):
    """External service integration errors"""
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"service": service}
        )

async def brainops_exception_handler(request: Request, exc: BrainOpsException):
    """Custom exception handler for BrainOps exceptions"""
    
    # Log the error
    logger.error(
        f"BrainOps exception: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__,
                "details": exc.details
            },
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Generic exception handler for unexpected errors"""
    
    # Log the full traceback
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={
            "traceback": traceback.format_exc(),
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Don't expose internal errors in production
    if request.app.state.settings.is_production:
        message = "An unexpected error occurred"
        details = {}
    else:
        message = str(exc)
        details = {"traceback": traceback.format_exc()}
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": message,
                "type": "InternalServerError",
                "details": details
            },
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
    )

async def validation_exception_handler(request: Request, exc: HTTPException):
    """Handler for validation exceptions"""
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "ValidationError"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
    )