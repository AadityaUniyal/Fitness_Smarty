"""
Comprehensive Logging and Monitoring Configuration

Provides application logging, audit trails, and performance monitoring
for the fitness app backend.

Requirement: 10.5
"""

import logging
import logging.handlers
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
from pathlib import Path
import sys

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        
        return json.dumps(log_data)


def setup_logging(
    app_name: str = "fitness_app",
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = True
) -> logging.Logger:
    """
    Setup comprehensive logging configuration
    
    Args:
        app_name: Application name for logger
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Enable console logging
        enable_file: Enable file logging
        enable_json: Enable JSON formatted logging
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler for general logs
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            LOGS_DIR / f"{app_name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # JSON file handler for structured logs
    if enable_json:
        json_handler = logging.handlers.RotatingFileHandler(
            LOGS_DIR / f"{app_name}_structured.json",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        logger.addHandler(json_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / f"{app_name}_errors.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s\n%(exc_info)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_handler.setFormatter(error_formatter)
    logger.addHandler(error_handler)
    
    return logger


class AuditLogger:
    """
    Audit trail logger for tracking user actions and system operations
    """
    
    def __init__(self, logger_name: str = "audit"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        # Audit log handler
        audit_handler = logging.handlers.RotatingFileHandler(
            LOGS_DIR / "audit.log",
            maxBytes=20 * 1024 * 1024,  # 20MB
            backupCount=10
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(audit_handler)
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ):
        """
        Log user action for audit trail
        
        Args:
            user_id: User identifier
            action: Action performed (create, read, update, delete, etc.)
            resource: Resource affected (meal_log, user_profile, etc.)
            details: Additional details about the action
            status: Action status (success, failure, error)
        """
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "status": status,
            "details": details or {}
        }
        
        self.logger.info(
            f"User action: {action} on {resource}",
            extra=audit_data
        )
    
    def log_system_operation(
        self,
        operation: str,
        component: str,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ):
        """
        Log system operation for audit trail
        
        Args:
            operation: Operation performed
            component: System component
            details: Additional details
            status: Operation status
        """
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "component": component,
            "status": status,
            "details": details or {}
        }
        
        self.logger.info(
            f"System operation: {operation} in {component}",
            extra=audit_data
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        access_type: str = "read"
    ):
        """
        Log data access for compliance and security
        
        Args:
            user_id: User accessing the data
            resource_type: Type of resource accessed
            resource_id: Specific resource identifier
            access_type: Type of access (read, write, delete)
        """
        self.log_user_action(
            user_id=user_id,
            action=f"data_access_{access_type}",
            resource=resource_type,
            details={"resource_id": resource_id}
        )


class PerformanceMonitor:
    """
    Performance monitoring for critical operations
    """
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        # Performance log handler
        perf_handler = logging.handlers.RotatingFileHandler(
            LOGS_DIR / "performance.log",
            maxBytes=20 * 1024 * 1024,  # 20MB
            backupCount=10
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(perf_handler)
    
    def log_operation_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log operation performance metrics
        
        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            metadata: Additional metadata
        """
        perf_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
            "metadata": metadata or {}
        }
        
        # Log warning if operation is slow
        if duration_ms > 1000:  # > 1 second
            self.logger.warning(
                f"Slow operation: {operation} took {duration_ms:.2f}ms",
                extra=perf_data
            )
        else:
            self.logger.info(
                f"Operation: {operation} completed in {duration_ms:.2f}ms",
                extra=perf_data
            )
    
    def monitor_endpoint(self, endpoint: str):
        """
        Decorator to monitor endpoint performance
        
        Args:
            endpoint: Endpoint path
        
        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    self.log_operation_performance(
                        operation=f"endpoint_{endpoint}",
                        duration_ms=duration_ms,
                        success=success,
                        metadata={"error": error} if error else None
                    )
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    self.log_operation_performance(
                        operation=f"endpoint_{endpoint}",
                        duration_ms=duration_ms,
                        success=success,
                        metadata={"error": error} if error else None
                    )
            
            # Return appropriate wrapper based on function type
            import inspect
            if inspect.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


def monitor_function(operation_name: str):
    """
    Decorator to monitor function performance
    
    Args:
        operation_name: Name of the operation being monitored
    
    Returns:
        Decorator function
    """
    perf_monitor = PerformanceMonitor()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                perf_monitor.log_operation_performance(
                    operation=operation_name,
                    duration_ms=duration_ms,
                    success=success,
                    metadata={"error": error} if error else None
                )
        
        return wrapper
    
    return decorator


# Global instances
app_logger = setup_logging()
audit_logger = AuditLogger()
performance_monitor = PerformanceMonitor()


# Convenience functions
def log_info(message: str, **kwargs):
    """Log info message"""
    app_logger.info(message, extra=kwargs)


def log_warning(message: str, **kwargs):
    """Log warning message"""
    app_logger.warning(message, extra=kwargs)


def log_error(message: str, exc_info=None, **kwargs):
    """Log error message"""
    app_logger.error(message, exc_info=exc_info, extra=kwargs)


def log_debug(message: str, **kwargs):
    """Log debug message"""
    app_logger.debug(message, extra=kwargs)


def log_critical(message: str, exc_info=None, **kwargs):
    """Log critical message"""
    app_logger.critical(message, exc_info=exc_info, extra=kwargs)
