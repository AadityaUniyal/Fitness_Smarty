"""
App Package Initialization

Exports all models and services for easy import
"""

# Import Base first
from .database import Base

# Export database models from models module
from .models import (
    EnhancedUser,
    ExerciseCategory,
    ExerciseItem,
    FoodCategory,
    FoodItem,
    MealLog,
    FoodDetection,
    WorkoutLog,
    BiometricReading,
    ProgressSnapshot
)

# Compatibility alias
User = EnhancedUser

__all__ = [
    'EnhancedUser',
    'User',
    'ExerciseCategory',
    'ExerciseItem',
    'FoodCategory',
    'FoodItem',
    'MealLog',
    'FoodDetection',
    'WorkoutLog',
    'BiometricReading',
    'ProgressSnapshot',
    'Base'
]