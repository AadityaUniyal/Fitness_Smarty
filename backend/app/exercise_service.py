from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from .models import ExerciseItem, ExerciseCategory
from decimal import Decimal
import uuid


class ExerciseService:
    """Service for managing exercise database operations"""

    VALID_DIFFICULTY_LEVELS = ['beginner', 'intermediate', 'advanced']
    
    @staticmethod
    def validate_difficulty_level(difficulty: str) -> bool:
        return difficulty.lower() in ExerciseService.VALID_DIFFICULTY_LEVELS

    @staticmethod
    def create_exercise(
        db: Session,
        name: str,
        category: str,
        targeted_muscle: str = "",
        difficulty: str = "beginner",
        equipment: str = "",
        calories_per_min: float = 5.0,
        description: str = "",
        fitness_goal: str = "maintenance"
    ) -> ExerciseItem:
        if not name or not name.strip():
            raise ValueError("Exercise name is required")
        cat = db.query(ExerciseCategory).filter(
            func.lower(ExerciseCategory.name) == category.lower()
        ).first()
        if not cat:
            cat = ExerciseCategory(name=category, description=f"{category} exercises")
            db.add(cat)
            db.commit()
            db.refresh(cat)
        exercise = ExerciseItem(
            category_id=cat.id,
            name=name.strip(),
            targeted_muscle=targeted_muscle,
            difficulty=difficulty.lower(),
            equipment=equipment,
            calories_per_min=calories_per_min,
            description=description,
            fitness_goal=fitness_goal
        )
        db.add(exercise)
        db.commit()
        db.refresh(exercise)
        return exercise

    @staticmethod
    def get_exercise_by_id(db: Session, exercise_id: int) -> Optional[ExerciseItem]:
        return db.query(ExerciseItem).filter(ExerciseItem.id == exercise_id).first()

    @staticmethod
    def search_exercises(
        db: Session,
        name_query: Optional[str] = None,
        category: Optional[str] = None,
        muscle_group: Optional[str] = None,
        equipment: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ExerciseItem]:
        query = db.query(ExerciseItem).join(ExerciseCategory)
        if name_query:
            query = query.filter(func.lower(ExerciseItem.name).contains(name_query.lower()))
        if category:
            query = query.filter(func.lower(ExerciseCategory.name) == category.lower())
        if muscle_group:
            query = query.filter(func.lower(ExerciseItem.targeted_muscle).contains(muscle_group.lower()))
        if equipment:
            query = query.filter(func.lower(ExerciseItem.equipment).contains(equipment.lower()))
        if difficulty:
            query = query.filter(ExerciseItem.difficulty == difficulty.lower())
        return query.limit(limit).offset(offset).all()

    @staticmethod
    def get_exercises_by_difficulty(db: Session, difficulty_level: str) -> List[ExerciseItem]:
        if not ExerciseService.validate_difficulty_level(difficulty_level):
            raise ValueError(f"Invalid difficulty level: {difficulty_level}")
        return db.query(ExerciseItem).filter(
            ExerciseItem.difficulty == difficulty_level.lower()
        ).all()

    @staticmethod
    def get_exercises_by_muscle_group(db: Session, muscle_group: str) -> List[ExerciseItem]:
        return db.query(ExerciseItem).filter(
            func.lower(ExerciseItem.targeted_muscle).contains(muscle_group.lower())
        ).all()

    @staticmethod
    def update_exercise(db: Session, exercise_id: int, **kwargs) -> Optional[ExerciseItem]:
        exercise = ExerciseService.get_exercise_by_id(db, exercise_id)
        if not exercise:
            return None
        if 'difficulty' in kwargs and not ExerciseService.validate_difficulty_level(kwargs['difficulty']):
            raise ValueError(f"Invalid difficulty level: {kwargs['difficulty']}")
        allowed = {'name', 'targeted_muscle', 'difficulty', 'equipment', 'calories_per_min', 'description', 'fitness_goal'}
        for key, value in kwargs.items():
            if key in allowed and hasattr(exercise, key):
                setattr(exercise, key, value)
        db.commit()
        db.refresh(exercise)
        return exercise

    @staticmethod
    def delete_exercise(db: Session, exercise_id: int) -> bool:
        exercise = ExerciseService.get_exercise_by_id(db, exercise_id)
        if not exercise:
            return False
        db.delete(exercise)
        db.commit()
        return True

    @staticmethod
    def get_exercise_modifications(db: Session, base_exercise_id: int) -> Dict[str, List[ExerciseItem]]:
        base = ExerciseService.get_exercise_by_id(db, base_exercise_id)
        if not base:
            return {'easier': [], 'harder': []}
        similar = db.query(ExerciseItem).filter(
            and_(
                ExerciseItem.id != base_exercise_id,
                func.lower(ExerciseItem.targeted_muscle).contains(
                    base.targeted_muscle.split('/')[0].strip().lower()
                ) if base.targeted_muscle else True
            )
        ).all()
        diff_map = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
        base_diff = diff_map.get(base.difficulty, 1)
        easier, harder = [], []
        for ex in similar:
            ex_diff = diff_map.get(ex.difficulty, 1)
            if ex_diff < base_diff:
                easier.append(ex)
            elif ex_diff > base_diff:
                harder.append(ex)
        return {'easier': easier, 'harder': harder}

    @staticmethod
    def recommend_exercises(db: Session, user_experience_level: str, target_muscle_groups: List[str], available_equipment: Optional[List[str]] = None, limit: int = 10) -> List[ExerciseItem]:
        if not ExerciseService.validate_difficulty_level(user_experience_level):
            raise ValueError(f"Invalid experience level: {user_experience_level}")
        query = db.query(ExerciseItem).filter(
            ExerciseItem.difficulty == user_experience_level.lower()
        )
        if target_muscle_groups:
            mg_filter = [func.lower(ExerciseItem.targeted_muscle).contains(mg.lower()) for mg in target_muscle_groups]
            query = query.filter(or_(*mg_filter))
        if available_equipment:
            eq_filter = [func.lower(ExerciseItem.equipment).contains(eq.lower()) for eq in available_equipment]
            eq_filter.append(ExerciseItem.equipment == '')
            eq_filter.append(ExerciseItem.equipment.ilike('bodyweight'))
            query = query.filter(or_(*eq_filter))
        return query.limit(limit).all()

    @staticmethod
    def validate_exercise_completeness(exercise: ExerciseItem) -> Dict[str, Any]:
        missing = []
        if not exercise.name: missing.append('name')
        if not exercise.targeted_muscle: missing.append('targeted_muscle')
        if not exercise.difficulty: missing.append('difficulty')
        elif not ExerciseService.validate_difficulty_level(exercise.difficulty):
            missing.append('difficulty (invalid)')
        if not exercise.equipment: missing.append('equipment')
        if not exercise.description: missing.append('description')
        return {'is_complete': len(missing) == 0, 'missing_fields': missing}

    @staticmethod
    def check_exercise_coverage(db: Session) -> Dict[str, Any]:
        """Compute coverage matrix for muscle_group x equipment x difficulty.
        Returns a nested dict structure and writes the result to
        'exercise_coverage.json' in the project root.
        """
        # Retrieve distinct values
        muscle_groups = [mg[0] for mg in db.query(ExerciseItem.targeted_muscle).distinct().all()]
        equipments = [eq[0] for eq in db.query(ExerciseItem.equipment).distinct().all()]
        difficulties = ExerciseService.VALID_DIFFICULTY_LEVELS
        # Initialize matrix
        coverage = {}
        for mg in muscle_groups:
            coverage[mg] = {}
            for eq in equipments:
                coverage[mg][eq] = {}
                for diff in difficulties:
                    count = db.query(ExerciseItem).filter(
                        func.lower(ExerciseItem.targeted_muscle) == mg.lower(),
                        func.lower(ExerciseItem.equipment) == eq.lower(),
                        ExerciseItem.difficulty == diff
                    ).count()
                    coverage[mg][eq][diff] = count
        # Write to JSON file
        output_path = Path(__file__).resolve().parents[2] / 'exercise_coverage.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(coverage, f, indent=2)
        return coverage
