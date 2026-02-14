"""
Comprehensive Error Handling Module

Provides centralized error handling, graceful degradation, retry mechanisms,
and user-friendly error messages for the fitness application.
"""

import logging
import time
import functools
from typing import Callable, Any, Optional, Dict, List, TypeVar, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    VALIDATION = "validation"
    NETWORK = "network"
    DATABASE = "database"
    AI_ANALYSIS = "ai_analysis"
    EXTERNAL_API = "external_api"
    FILE_SYSTEM = "file_system"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for error handling"""
    category: ErrorCategory
    severity: ErrorSeverity
    user_message: str
    technical_message: str
    recovery_options: List[str]
    retry_possible: bool = False
    fallback_available: bool = False


class ApplicationError(Exception):
    """Base application error with context"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        recovery_options: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.user_message = user_message or self._generate_user_message()
        self.recovery_options = recovery_options or []
    
    def _generate_user_message(self) -> str:
        """Generate user-friendly error message"""
        return "An error occurred. Please try again or contact support if the problem persists."


class AIAnalysisError(ApplicationError):
    """Error during AI/ML analysis"""
    
    def __init__(self, message: str, confidence: float = 0.0, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AI_ANALYSIS,
            **kwargs
        )
        self.confidence = confidence
    
    def _generate_user_message(self) -> str:
        return "We couldn't analyze this image automatically. You can enter the meal details manually."


class ExternalAPIError(ApplicationError):
    """Error calling external API"""
    
    def __init__(self, message: str, api_name: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.EXTERNAL_API,
            **kwargs
        )
        self.api_name = api_name
    
    def _generate_user_message(self) -> str:
        return f"We're having trouble connecting to {self.api_name}. Please try again in a moment."


class DatabaseError(ApplicationError):
    """Database operation error"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
    
    def _generate_user_message(self) -> str:
        return "We're experiencing database issues. Your data is safe, please try again shortly."


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator to retry function on failure with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {str(e)}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {str(e)}. "
                        f"Retrying in {current_delay}s..."
                    )
                    
                    if on_retry:
                        on_retry(attempt, e)
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def graceful_degradation(
    fallback_value: Any = None,
    fallback_func: Optional[Callable] = None,
    log_error: bool = True
):
    """
    Decorator to provide graceful degradation on function failure
    
    Args:
        fallback_value: Value to return on failure
        fallback_func: Function to call on failure (takes exception as argument)
        log_error: Whether to log the error
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Union[T, Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        f"{func.__name__} failed, using fallback: {str(e)}",
                        exc_info=True
                    )
                
                if fallback_func:
                    return fallback_func(e)
                return fallback_value
        
        return wrapper
    return decorator


class ErrorHandler:
    """Centralized error handling service"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[Dict[str, Any]] = []
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorContext:
        """
        Handle an error and return error context
        
        Args:
            error: The exception that occurred
            context: Additional context information
            
        Returns:
            ErrorContext with handling information
        """
        # Classify error
        category = self._classify_error(error)
        severity = self._determine_severity(error, category)
        
        # Generate messages
        user_message = self._generate_user_message(error, category)
        technical_message = str(error)
        
        # Determine recovery options
        recovery_options = self._get_recovery_options(error, category)
        retry_possible = self._is_retry_possible(error, category)
        fallback_available = self._is_fallback_available(error, category)
        
        # Log error
        self._log_error(error, category, severity, context)
        
        # Track error
        self._track_error(category, severity)
        
        return ErrorContext(
            category=category,
            severity=severity,
            user_message=user_message,
            technical_message=technical_message,
            recovery_options=recovery_options,
            retry_possible=retry_possible,
            fallback_available=fallback_available
        )
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error into category"""
        if isinstance(error, ApplicationError):
            return error.category
        
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Network errors
        if any(keyword in error_message for keyword in ['connection', 'timeout', 'network', 'unreachable']):
            return ErrorCategory.NETWORK
        
        # Database errors
        if any(keyword in error_type.lower() for keyword in ['database', 'sql', 'integrity', 'operational']):
            return ErrorCategory.DATABASE
        
        # Validation errors
        if any(keyword in error_type.lower() for keyword in ['validation', 'value', 'type']):
            return ErrorCategory.VALIDATION
        
        # File system errors
        if any(keyword in error_type.lower() for keyword in ['file', 'io', 'permission']):
            return ErrorCategory.FILE_SYSTEM
        
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity"""
        if isinstance(error, ApplicationError):
            return error.severity
        
        # Critical categories
        if category in [ErrorCategory.DATABASE, ErrorCategory.AUTHENTICATION]:
            return ErrorSeverity.HIGH
        
        # Medium severity
        if category in [ErrorCategory.EXTERNAL_API, ErrorCategory.AI_ANALYSIS]:
            return ErrorSeverity.MEDIUM
        
        # Low severity
        if category == ErrorCategory.VALIDATION:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _generate_user_message(self, error: Exception, category: ErrorCategory) -> str:
        """Generate user-friendly error message"""
        if isinstance(error, ApplicationError):
            return error.user_message
        
        messages = {
            ErrorCategory.NETWORK: "We're having trouble connecting. Please check your internet connection and try again.",
            ErrorCategory.DATABASE: "We're experiencing technical difficulties. Your data is safe, please try again shortly.",
            ErrorCategory.AI_ANALYSIS: "We couldn't analyze this automatically. You can enter the information manually.",
            ErrorCategory.EXTERNAL_API: "We're having trouble accessing external services. Please try again in a moment.",
            ErrorCategory.FILE_SYSTEM: "There was a problem with file storage. Please try again.",
            ErrorCategory.VALIDATION: "Please check your input and try again.",
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please log in again.",
            ErrorCategory.AUTHORIZATION: "You don't have permission to perform this action.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again or contact support."
        }
        
        return messages.get(category, messages[ErrorCategory.UNKNOWN])
    
    def _get_recovery_options(self, error: Exception, category: ErrorCategory) -> List[str]:
        """Get recovery options for error"""
        if isinstance(error, ApplicationError):
            return error.recovery_options
        
        options = {
            ErrorCategory.NETWORK: [
                "Check your internet connection",
                "Try again in a moment",
                "Contact support if the problem persists"
            ],
            ErrorCategory.AI_ANALYSIS: [
                "Enter meal details manually",
                "Try taking a clearer photo",
                "Ensure good lighting and focus"
            ],
            ErrorCategory.EXTERNAL_API: [
                "Try again in a few minutes",
                "Use manual entry as an alternative"
            ],
            ErrorCategory.VALIDATION: [
                "Check your input for errors",
                "Ensure all required fields are filled"
            ]
        }
        
        return options.get(category, ["Try again", "Contact support if the problem persists"])
    
    def _is_retry_possible(self, error: Exception, category: ErrorCategory) -> bool:
        """Determine if retry is possible"""
        retry_categories = [
            ErrorCategory.NETWORK,
            ErrorCategory.EXTERNAL_API,
            ErrorCategory.DATABASE
        ]
        return category in retry_categories
    
    def _is_fallback_available(self, error: Exception, category: ErrorCategory) -> bool:
        """Determine if fallback is available"""
        fallback_categories = [
            ErrorCategory.AI_ANALYSIS,
            ErrorCategory.EXTERNAL_API
        ]
        return category in fallback_categories
    
    def _log_error(
        self,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: Optional[Dict[str, Any]]
    ):
        """Log error with appropriate level"""
        log_message = f"[{category.value}] {type(error).__name__}: {str(error)}"
        
        if context:
            log_message += f" | Context: {context}"
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, exc_info=True)
        elif severity == ErrorSeverity.HIGH:
            logger.error(log_message, exc_info=True)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _track_error(self, category: ErrorCategory, severity: ErrorSeverity):
        """Track error for monitoring"""
        key = f"{category.value}_{severity.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        
        self.error_history.append({
            'category': category.value,
            'severity': severity.value,
            'timestamp': time.time()
        })
        
        # Keep only last 1000 errors
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            'error_counts': self.error_counts.copy(),
            'total_errors': sum(self.error_counts.values()),
            'recent_errors': len(self.error_history)
        }


# Global error handler instance
error_handler = ErrorHandler()
