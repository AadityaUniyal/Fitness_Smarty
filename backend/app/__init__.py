"""
App Package Initialization

Exports all models and services for easy import
"""

# Import Base first
from .database import Base

# Export database models from db_models module
from .db_models import (
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
    'User',  # Compatibility alias
    'ExerciseCategory',
    'ExerciseItem',
    'WorkoutLog',
    'MealLog',
    'BiometricRecord',
    'BiomechanicalFault',
    'UserProfile',
    'UserGoal',
    'FoodItem',
    'FoodDetection',
    'Base'
]