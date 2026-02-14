"""
API Validation and Error Handling Module

Provides comprehensive input validation, consistent error responses,
and proper HTTP status code handling for all API endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, validator
from fastapi import HTTPException, status
from datetime import datetime
import re


class APIError(BaseModel):
    """Standard API error response structure"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()
    status_code: int


class APIResponse(BaseModel):
    """Standard API success response structure"""
    success: bool = True
    data: Any
    message: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    message: str
    value: Any = None


class ValidationResult(BaseModel):
    """Result of validation checks"""
    is_valid: bool
    errors: List[ValidationError] = []


class APIValidator:
    """Comprehensive API input validation"""
    
    @staticmethod
    def validate_user_id(user_id: str) -> ValidationResult:
        """Validate user ID format"""
        errors = []
        
        if not user_id or not user_id.strip():
            errors.append(ValidationError(
                field="user_id",
                message="User ID cannot be empty",
                value=user_id
            ))
        elif len(user_id) > 255:
            errors.append(ValidationError(
                field="user_id",
                message="User ID too long (max 255 characters)",
                value=user_id
            ))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    @staticmethod
    def validate_meal_type(meal_type: str) -> ValidationResult:
        """Validate meal type"""
        valid_types = ['breakfast', 'lunch', 'dinner', 'snack']
        errors = []
        
        if not meal_type:
            errors.append(ValidationError(
                field="meal_type",
                message="Meal type is required",
                value=meal_type
            ))
        elif meal_type.lower() not in valid_types:
            errors.append(ValidationError(
                field="meal_type",
                message=f"Invalid meal type. Must be one of: {', '.join(valid_types)}",
                value=meal_type
            ))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    @staticmethod
    def validate_activity_level(activity_level: str) -> ValidationResult:
        """Validate activity level"""
        valid_levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']
        errors = []
        
        if not activity_level:
            errors.append(ValidationError(
                field="activity_level",
                message="Activity level is required",
                value=activity_level
            ))
        elif activity_level.lower() not in valid_levels:
            errors.append(ValidationError(
                field="activity_level",
                message=f"Invalid activity level. Must be one of: {', '.join(valid_levels)}",
                value=activity_level
            ))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    @staticmethod
    def validate_primary_goal(primary_goal: str) -> ValidationResult:
        """Validate primary fitness goal"""
        valid_goals = ['weight_loss', 'weight_gain', 'muscle_gain', 'maintenance', 'athletic_performance']
        errors = []
        
        if not primary_goal:
            errors.append(ValidationError(
                field="primary_goal",
                message="Primary goal is required",
                value=primary_goal
            ))
        elif primary_goal.lower() not in valid_goals:
            errors.append(ValidationError(
                field="primary_goal",
                message=f"Invalid primary goal. Must be one of: {', '.join(valid_goals)}",
                value=primary_goal
            ))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    @staticmethod
    def validate_goal_type(goal_type: str) -> ValidationResult:
        """Validate goal type"""
        valid_types = ['daily_calories', 'weekly_exercise', 'weight_target', 'protein_target', 'steps_target']
        errors = []
        
        if not goal_type:
            errors.append(ValidationError(
                field="goal_type",
                message="Goal type is required",
                value=goal_type
            ))
        elif goal_type.lower() not in valid_types:
            errors.append(ValidationError(
                field="goal_type",
                message=f"Invalid goal type. Must be one of: {', '.join(valid_types)}",
                value=goal_type
            ))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    @staticmethod
    def validate_numeric_range(
        value: float,
        field_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> ValidationResult:
        """Validate numeric value is within acceptable range"""
        errors = []
        
        if value is None:
            errors.append(ValidationError(
                field=field_name,
                message=f"{field_name} is required",
                value=value
            ))
        else:
            if min_value is not None and value < min_value:
                errors.append(ValidationError(
                    field=field_name,
                    message=f"{field_name} must be at least {min_value}",
                    value=value
                ))
            if max_value is not None and value > max_value:
                errors.append(ValidationError(
                    field=field_name,
                    message=f"{field_name} must be at most {max_value}",
                    value=value
                ))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    @staticmethod
    def validate_date_format(date_str: str, field_name: str) -> ValidationResult:
        """Validate ISO date format"""
        errors = []
        
        if not date_str:
            return ValidationResult(is_valid=True, errors=[])  # Optional field
        
        try:
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            errors.append(ValidationError(
                field=field_name,
                message=f"Invalid date format for {field_name}. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
                value=date_str
            ))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    @staticmethod
    def validate_pagination(limit: int, offset: int) -> ValidationResult:
        """Validate pagination parameters"""
        errors = []
        
        if limit < 1:
            errors.append(ValidationError(
                field="limit",
                message="Limit must be at least 1",
                value=limit
            ))
        elif limit > 100:
            errors.append(ValidationError(
                field="limit",
                message="Limit cannot exceed 100",
                value=limit
            ))
        
        if offset < 0:
            errors.append(ValidationError(
                field="offset",
                message="Offset cannot be negative",
                value=offset
            ))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    @staticmethod
    def validate_image_file(file_data: bytes, max_size_mb: int = 10) -> ValidationResult:
        """Validate image file"""
        errors = []
        
        if not file_data:
            errors.append(ValidationError(
                field="image_file",
                message="Image file is required",
                value=None
            ))
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check file size
        file_size_mb = len(file_data) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            errors.append(ValidationError(
                field="image_file",
                message=f"Image file too large. Maximum size is {max_size_mb}MB",
                value=f"{file_size_mb:.2f}MB"
            ))
        
        # Check if it's a valid image (basic check for common image headers)
        image_signatures = [
            b'\xFF\xD8\xFF',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'GIF87a',  # GIF
            b'GIF89a',  # GIF
        ]
        
        is_valid_image = any(file_data.startswith(sig) for sig in image_signatures)
        if not is_valid_image:
            errors.append(ValidationError(
                field="image_file",
                message="Invalid image format. Supported formats: JPEG, PNG, GIF",
                value="Unknown format"
            ))
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


class ErrorHandler:
    """Centralized error handling for consistent API responses"""
    
    @staticmethod
    def validation_error(errors: List[ValidationError]) -> HTTPException:
        """Return validation error response"""
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "ValidationError",
                "message": "Input validation failed",
                "details": {
                    "errors": [
                        {
                            "field": err.field,
                            "message": err.message,
                            "value": err.value
                        }
                        for err in errors
                    ]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def not_found_error(resource: str, identifier: str) -> HTTPException:
        """Return not found error response"""
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFoundError",
                "message": f"{resource} not found",
                "details": {"identifier": identifier},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def bad_request_error(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
        """Return bad request error response"""
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "BadRequestError",
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def conflict_error(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
        """Return conflict error response"""
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "ConflictError",
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def internal_error(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
        """Return internal server error response"""
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def unauthorized_error(message: str = "Authentication required") -> HTTPException:
        """Return unauthorized error response"""
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "UnauthorizedError",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    @staticmethod
    def forbidden_error(message: str = "Access forbidden") -> HTTPException:
        """Return forbidden error response"""
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "ForbiddenError",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


def format_success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    """Format successful API response"""
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
