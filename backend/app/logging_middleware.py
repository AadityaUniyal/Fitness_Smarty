"""
Logging Middleware for FastAPI

Integrates comprehensive logging, audit trails, and performance monitoring
into the FastAPI application.

Requirement: 10.5
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
from typing import Callable
from .logging_config import app_logger, audit_logger, performance_monitor


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract user ID if available
        user_id = None
        if hasattr(request.state, "user"):
            user_id = str(request.state.user.id)
        
        # Log request
        app_logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_id": user_id
            }
        )
        
        # Measure request processing time
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            app_logger.info(
                f"Response: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "user_id": user_id
                }
            )
            
            # Log performance metrics
            performance_monitor.log_operation_performance(
                operation=f"{request.method} {request.url.path}",
                duration_ms=duration_ms,
                success=response.status_code < 400,
                metadata={
                    "status_code": response.status_code,
                    "user_id": user_id
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            app_logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "error": str(e)
                }
            )
            
            # Log performance metrics for failed request
            performance_monitor.log_operation_performance(
                operation=f"{request.method} {request.url.path}",
                duration_ms=duration_ms,
                success=False,
                metadata={
                    "error": str(e),
                    "user_id": user_id
                }
            )
            
            raise


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to create audit trails for sensitive operations
    """
    
    # Operations that should be audited
    AUDITED_PATHS = [
        "/api/auth/register",
        "/api/auth/login",
        "/api/users",
        "/api/meals/analyze",
        "/api/goals",
        "/api/recommendations"
    ]
    
    # Methods that modify data
    WRITE_METHODS = ["POST", "PUT", "PATCH", "DELETE"]
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this request should be audited
        should_audit = any(
            request.url.path.startswith(path) for path in self.AUDITED_PATHS
        ) or request.method in self.WRITE_METHODS
        
        if not should_audit:
            return await call_next(request)
        
        # Extract user ID if available
        user_id = "anonymous"
        if hasattr(request.state, "user"):
            user_id = str(request.state.user.id)
        
        # Process request
        response = await call_next(request)
        
        # Determine action type
        action = self._get_action_type(request.method)
        
        # Determine resource type from path
        resource = self._extract_resource_from_path(request.url.path)
        
        # Log audit trail
        audit_logger.log_user_action(
            user_id=user_id,
            action=action,
            resource=resource,
            details={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code
            },
            status="success" if response.status_code < 400 else "failure"
        )
        
        return response
    
    def _get_action_type(self, method: str) -> str:
        """Map HTTP method to action type"""
        action_map = {
            "POST": "create",
            "GET": "read",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete"
        }
        return action_map.get(method, "unknown")
    
    def _extract_resource_from_path(self, path: str) -> str:
        """Extract resource type from URL path"""
        # Remove /api/ prefix if present
        if path.startswith("/api/"):
            path = path[5:]
        
        # Extract first path segment as resource type
        parts = path.split("/")
        if len(parts) > 0:
            return parts[0]
        
        return "unknown"


def setup_logging_middleware(app):
    """
    Setup all logging middleware for the FastAPI application
    
    Args:
        app: FastAPI application instance
    """
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Add audit middleware
    app.add_middleware(AuditMiddleware)
    
    app_logger.info("Logging middleware initialized")
