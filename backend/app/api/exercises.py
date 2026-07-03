from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import schemas, models
from app.exercise_service import ExerciseService

router = APIRouter(prefix="/api/exercises", tags=["Exercises"])

@router.get("/library")
def get_exercise_library(db: Session = Depends(get_db)):
    cats = db.query(models.ExerciseCategory).all()
    result = []
    for cat in cats:
        result.append({
            "id": cat.id,
            "name": cat.name,
            "description": cat.description or "",
            "items": [{
                "id": ex.id,
                "name": ex.name,
                "description": ex.description or "",
                "targeted_muscle": ex.targeted_muscle or "",
                "difficulty": ex.difficulty or "beginner",
                "equipment": ex.equipment or "",
                "calories_per_min": ex.calories_per_min or 5.0,
                "calories_per_rep": getattr(ex, 'calories_per_rep', 0.1)
            } for ex in cat.exercises]
        })
    return result

@router.post("/")
def create_exercise(
    name: str = Body(...),
    category: str = Body(...),
    targeted_muscle: str = Body(default=""),
    difficulty: str = Body(default="beginner"),
    equipment: str = Body(default=""),
    calories_per_min: float = Body(default=5.0),
    description: str = Body(default=""),
    fitness_goal: str = Body(default="maintenance"),
    db: Session = Depends(get_db)
):
    try:
        return ExerciseService.create_exercise(
            db=db, name=name, category=category,
            targeted_muscle=targeted_muscle, difficulty=difficulty,
            equipment=equipment, calories_per_min=calories_per_min,
            description=description, fitness_goal=fitness_goal
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search")
def search_exercises(
    name_query: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    muscle_group: Optional[str] = Query(None),
    equipment: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    return ExerciseService.search_exercises(
        db=db, name_query=name_query, category=category,
        muscle_group=muscle_group, equipment=equipment,
        difficulty=difficulty, limit=limit, offset=offset
    )

@router.get("/difficulty/{difficulty_level}")
def get_exercises_by_difficulty(difficulty_level: str, db: Session = Depends(get_db)):
    try:
        return ExerciseService.get_exercises_by_difficulty(db, difficulty_level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/muscle-group/{muscle_group}")
def get_exercises_by_muscle_group(muscle_group: str, db: Session = Depends(get_db)):
    return ExerciseService.get_exercises_by_muscle_group(db, muscle_group)

@router.put("/{exercise_id}")
def update_exercise(exercise_id: int, db: Session = Depends(get_db), **kwargs):
    try:
        exercise = ExerciseService.update_exercise(db, exercise_id, **kwargs)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return exercise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{exercise_id}")
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    success = ExerciseService.delete_exercise(db, exercise_id)
    if not success:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return {"message": "Exercise deleted successfully"}

@router.get("/{exercise_id}/modifications")
def get_exercise_modifications(exercise_id: int, db: Session = Depends(get_db)):
    base = ExerciseService.get_exercise_by_id(db, exercise_id)
    if not base:
        raise HTTPException(status_code=404, detail="Exercise not found")
    mods = ExerciseService.get_exercise_modifications(db, exercise_id)
    return {"base_exercise": base, "easier": mods['easier'], "harder": mods['harder']}

@router.post("/recommend")
def recommend_exercises(
    user_experience_level: str = Body(...),
    target_muscle_groups: List[str] = Body(...),
    available_equipment: Optional[List[str]] = Body(None),
    limit: int = Body(10),
    db: Session = Depends(get_db)
):
    try:
        return ExerciseService.recommend_exercises(
            db=db, user_experience_level=user_experience_level,
            target_muscle_groups=target_muscle_groups,
            available_equipment=available_equipment, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
