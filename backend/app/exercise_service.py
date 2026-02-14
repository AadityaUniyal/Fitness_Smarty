"""
Exercise Service Module

Provides comprehensive exercise database management including:
- Exercise CRUD operations
- Advanced search and filtering
- Difficulty classification validation
- Exercise recommendations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from .models import Exercise, ExerciseItem
from decimal import Decimal
import uuid


class ExerciseService:
    """Service for managing exercise database operations"""
    
    VALID_DIFFICULTY_LEVELS = ['beginner', 'intermediate', 'advanced']
    VALID_CATEGORIES = ['strength', 'cardio', 'flexibility', 'sports']
    
    @staticmethod
    def validate_difficulty_level(difficulty: str) -> bool:
        """Validate difficulty level classification"""
        return difficulty.lower() in ExerciseService.VALID_DIFFICULTY_LEVELS
    
    @staticmethod
    def validate_category(category: str) -> bool:
        """Validate exercise category"""
        return category.lower() in ExerciseService.VALID_CATEGORIES
    
    @staticmethod
    def create_exercise(
        db: Session,
        name: str,
        category: str,
        muscle_groups: List[str],
        equipment: List[str],
        difficulty_level: str,
        instructions: str,
        safety_notes: str
    ) -> Exercise:
        """
        Create a new exercise with validation
        
        Args:
            db: Database session
            name: Exercise name
            category: Exercise category (strength, cardio, flexibility, sports)
            muscle_groups: List of targeted muscle groups
            equipment: List of required equipment
            difficulty_level: Difficulty classification (beginner, intermediate, advanced)
            instructions: Detailed form instructions
            safety_notes: Safety considerations and warnings
            
        Returns:
            Created Exercise object
            
        Raises:
            ValueError: If validation fails
        """
        # Validate difficulty level
        if not ExerciseService.validate_difficulty_level(difficulty_level):
            raise ValueError(
                f"Invalid difficulty level: {difficulty_level}. "
                f"Must be one of: {', '.join(ExerciseService.VALID_DIFFICULTY_LEVELS)}"
            )
        
        # Validate category
        if not ExerciseService.validate_category(category):
            raise ValueError(
                f"Invalid category: {category}. "
                f"Must be one of: {', '.join(ExerciseService.VALID_CATEGORIES)}"
            )
        
        # Validate required fields
        if not name or not name.strip():
            raise ValueError("Exercise name is required")
        
        if not muscle_groups or len(muscle_groups) == 0:
            raise ValueError("At least one muscle group must be specified")
        
        if not instructions or not instructions.strip():
            raise ValueError("Exercise instructions are required")
        
        if not safety_notes or not safety_notes.strip():
            raise ValueError("Safety notes are required")
        
        # Create exercise
        exercise = Exercise(
            name=name.strip(),
            category=category.lower(),
            muscle_groups=muscle_groups,
            equipment=equipment if equipment else [],
            difficulty_level=difficulty_level.lower(),
            instructions=instructions.strip(),
            safety_notes=safety_notes.strip()
        )
        
        db.add(exercise)
        db.commit()
        db.refresh(exercise)
        
        return exercise
    
    @staticmethod
    def get_exercise_by_id(db: Session, exercise_id: uuid.UUID) -> Optional[Exercise]:
        """Get exercise by ID"""
        return db.query(Exercise).filter(Exercise.id == exercise_id).first()
    
    @staticmethod
    def search_exercises(
        db: Session,
        name_query: Optional[str] = None,
        category: Optional[str] = None,
        muscle_groups: Optional[List[str]] = None,
        equipment: Optional[List[str]] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Exercise]:
        """
        Advanced exercise search with multiple filters
        
        Args:
            db: Database session
            name_query: Partial name match (case-insensitive)
            category: Filter by category
            muscle_groups: Filter by muscle groups (exercises must target at least one)
            equipment: Filter by equipment (exercises must use at least one)
            difficulty_level: Filter by difficulty
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            List of matching exercises
        """
        query = db.query(Exercise)
        
        # Name search (case-insensitive partial match)
        if name_query:
            query = query.filter(
                func.lower(Exercise.name).contains(name_query.lower())
            )
        
        # Category filter
        if category:
            query = query.filter(Exercise.category == category.lower())
        
        # Muscle groups filter (exercises targeting at least one specified muscle group)
        if muscle_groups and len(muscle_groups) > 0:
            # PostgreSQL array overlap operator
            query = query.filter(Exercise.muscle_groups.overlap(muscle_groups))
        
        # Equipment filter (exercises using at least one specified equipment)
        if equipment and len(equipment) > 0:
            query = query.filter(Exercise.equipment.overlap(equipment))
        
        # Difficulty filter
        if difficulty_level:
            query = query.filter(Exercise.difficulty_level == difficulty_level.lower())
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    @staticmethod
    def get_exercises_by_difficulty(
        db: Session,
        difficulty_level: str
    ) -> List[Exercise]:
        """Get all exercises for a specific difficulty level"""
        if not ExerciseService.validate_difficulty_level(difficulty_level):
            raise ValueError(f"Invalid difficulty level: {difficulty_level}")
        
        return db.query(Exercise).filter(
            Exercise.difficulty_level == difficulty_level.lower()
        ).all()
    
    @staticmethod
    def get_exercises_by_muscle_group(
        db: Session,
        muscle_group: str
    ) -> List[Exercise]:
        """Get all exercises targeting a specific muscle group"""
        return db.query(Exercise).filter(
            Exercise.muscle_groups.contains([muscle_group])
        ).all()
    
    @staticmethod
    def update_exercise(
        db: Session,
        exercise_id: uuid.UUID,
        **kwargs
    ) -> Optional[Exercise]:
        """
        Update exercise fields
        
        Args:
            db: Database session
            exercise_id: Exercise UUID
            **kwargs: Fields to update
            
        Returns:
            Updated Exercise object or None if not found
        """
        exercise = ExerciseService.get_exercise_by_id(db, exercise_id)
        if not exercise:
            return None
        
        # Validate difficulty level if being updated
        if 'difficulty_level' in kwargs:
            if not ExerciseService.validate_difficulty_level(kwargs['difficulty_level']):
                raise ValueError(f"Invalid difficulty level: {kwargs['difficulty_level']}")
            kwargs['difficulty_level'] = kwargs['difficulty_level'].lower()
        
        # Validate category if being updated
        if 'category' in kwargs:
            if not ExerciseService.validate_category(kwargs['category']):
                raise ValueError(f"Invalid category: {kwargs['category']}")
            kwargs['category'] = kwargs['category'].lower()
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(exercise, key):
                setattr(exercise, key, value)
        
        db.commit()
        db.refresh(exercise)
        
        return exercise
    
    @staticmethod
    def delete_exercise(db: Session, exercise_id: uuid.UUID) -> bool:
        """Delete an exercise"""
        exercise = ExerciseService.get_exercise_by_id(db, exercise_id)
        if not exercise:
            return False
        
        db.delete(exercise)
        db.commit()
        return True
    
    @staticmethod
    def get_exercise_modifications(
        db: Session,
        base_exercise_id: uuid.UUID
    ) -> Dict[str, List[Exercise]]:
        """
        Get exercise modifications and alternatives
        
        Returns exercises with same muscle groups but different difficulty levels
        
        Returns:
            Dictionary with 'easier' and 'harder' exercise lists
        """
        base_exercise = ExerciseService.get_exercise_by_id(db, base_exercise_id)
        if not base_exercise:
            return {'easier': [], 'harder': []}
        
        # Get exercises targeting same muscle groups
        similar_exercises = db.query(Exercise).filter(
            and_(
                Exercise.id != base_exercise_id,
                Exercise.muscle_groups.overlap(base_exercise.muscle_groups)
            )
        ).all()
        
        # Difficulty hierarchy
        difficulty_order = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
        base_difficulty = difficulty_order.get(base_exercise.difficulty_level, 1)
        
        easier = []
        harder = []
        
        for ex in similar_exercises:
            ex_difficulty = difficulty_order.get(ex.difficulty_level, 1)
            if ex_difficulty < base_difficulty:
                easier.append(ex)
            elif ex_difficulty > base_difficulty:
                harder.append(ex)
        
        return {
            'easier': easier,
            'harder': harder
        }
    
    @staticmethod
    def recommend_exercises(
        db: Session,
        user_experience_level: str,
        target_muscle_groups: List[str],
        available_equipment: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Exercise]:
        """
        Recommend exercises based on user profile
        
        Args:
            db: Database session
            user_experience_level: User's fitness level (beginner, intermediate, advanced)
            target_muscle_groups: Muscle groups to target
            available_equipment: Equipment user has access to
            limit: Maximum recommendations
            
        Returns:
            List of recommended exercises
        """
        if not ExerciseService.validate_difficulty_level(user_experience_level):
            raise ValueError(f"Invalid experience level: {user_experience_level}")
        
        query = db.query(Exercise).filter(
            and_(
                Exercise.difficulty_level == user_experience_level.lower(),
                Exercise.muscle_groups.overlap(target_muscle_groups)
            )
        )
        
        # Filter by available equipment if specified
        if available_equipment:
            # Include bodyweight exercises (empty equipment array) or exercises using available equipment
            query = query.filter(
                or_(
                    Exercise.equipment == [],
                    Exercise.equipment.overlap(available_equipment)
                )
            )
        
        return query.limit(limit).all()
    
    @staticmethod
    def validate_exercise_completeness(exercise: Exercise) -> Dict[str, Any]:
        """
        Validate that an exercise has all required information
        
        Returns:
            Dictionary with 'is_complete' boolean and 'missing_fields' list
        """
        missing_fields = []
        
        if not exercise.name or not exercise.name.strip():
            missing_fields.append('name')
        
        if not exercise.category:
            missing_fields.append('category')
        
        if not exercise.muscle_groups or len(exercise.muscle_groups) == 0:
            missing_fields.append('muscle_groups')
        
        if not exercise.difficulty_level:
            missing_fields.append('difficulty_level')
        elif not ExerciseService.validate_difficulty_level(exercise.difficulty_level):
            missing_fields.append('difficulty_level (invalid value)')
        
        if not exercise.instructions or not exercise.instructions.strip():
            missing_fields.append('instructions')
        
        if not exercise.safety_notes or not exercise.safety_notes.strip():
            missing_fields.append('safety_notes')
        
        return {
            'is_complete': len(missing_fields) == 0,
            'missing_fields': missing_fields
        }
