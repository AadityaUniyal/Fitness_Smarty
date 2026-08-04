from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import models
from app.clerk_auth import get_current_user_id_from_clerk as get_current_user_id
from app.database import get_db
from app.daily_progress_service import DailyProgressService


router = APIRouter(prefix="/api/daily-progress", tags=["Daily Progress"])


class MealLogProgressRequest(BaseModel):
    user_id: int
    meal_id: int | None = None


class WorkoutSetProgressRequest(BaseModel):
    user_id: int
    sets_added: int = Field(default=1, ge=1, le=20)
    workout_planned_id: int | None = None


class CheckInRequest(BaseModel):
    user_id: int
    energy_level: int | None = Field(default=None, ge=1, le=5)
    soreness_level: int | None = Field(default=None, ge=1, le=5)
    symptom_severity: int | None = Field(default=None, ge=1, le=5)
    water_intake_ml: int | None = Field(default=None, ge=0)


@router.get("/{user_id}")
def get_today_progress(
    user_id: int,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id),
):
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    service = DailyProgressService(db)
    return service.summary(user_id)


@router.post("/refresh/{user_id}")
def refresh_today_progress(
    user_id: int,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id),
):
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    service = DailyProgressService(db)
    return service.sync_from_logs(user_id).id


@router.post("/meal-logged")
def meal_logged(
    request: MealLogProgressRequest,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id),
):
    if str(request.user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    service = DailyProgressService(db)
    return service.sync_from_logs(request.user_id)


@router.post("/set-logged")
def set_logged(
    request: WorkoutSetProgressRequest,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id),
):
    if str(request.user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    service = DailyProgressService(db)
    return service.log_workout_set(
        user_id=request.user_id,
        sets_added=request.sets_added,
        workout_planned_id=request.workout_planned_id,
    )


@router.post("/check-in")
def daily_check_in(
    request: CheckInRequest,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id),
):
    if str(request.user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    row = (
        db.query(models.DailyProgress)
        .filter(models.DailyProgress.user_id == request.user_id)
        .order_by(models.DailyProgress.date.desc())
        .first()
    )
    if not row:
        row = DailyProgressService(db).create_today(request.user_id)
    if request.energy_level is not None:
        row.energy_level = request.energy_level
    if request.soreness_level is not None:
        row.soreness_level = request.soreness_level
    if request.symptom_severity is not None:
        row.symptom_severity = request.symptom_severity
    if request.water_intake_ml is not None:
        row.water_intake_ml = request.water_intake_ml
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


@router.get("/weekly/{user_id}")
def weekly_summary(
    user_id: int,
    days: int = 7,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id),
):
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    rows = (
        db.query(models.DailyProgress)
        .filter(models.DailyProgress.user_id == user_id)
        .order_by(models.DailyProgress.date.desc())
        .limit(days)
        .all()
    )
    rows = list(reversed(rows))
    totals = {
        "calories_target": 0,
        "calories_consumed": 0,
        "protein_target": 0,
        "protein_consumed": 0,
        "carbs_target": 0,
        "carbs_consumed": 0,
        "fats_target": 0,
        "fats_consumed": 0,
        "workouts": 0,
        "planned_workouts": 0,
        "sets_completed": 0,
        "sets_planned": 0,
    }
    daily = []
    for row in rows:
        totals["calories_target"] += row.calories_target or 0
        totals["calories_consumed"] += row.calories_consumed or 0
        totals["protein_target"] += row.protein_target or 0
        totals["protein_consumed"] += row.protein_consumed or 0
        totals["carbs_target"] += row.carbs_target or 0
        totals["carbs_consumed"] += row.carbs_consumed or 0
        totals["fats_target"] += row.fats_target or 0
        totals["fats_consumed"] += row.fats_consumed or 0
        totals["sets_completed"] += row.sets_completed or 0
        totals["sets_planned"] += row.sets_planned or 0
        if (row.sets_completed or 0) > 0:
            totals["workouts"] += 1
        if (row.sets_planned or 0) > 0:
            totals["planned_workouts"] += 1
        daily.append({
            "date": row.date.isoformat() if row.date else None,
            "calories_consumed": row.calories_consumed or 0,
            "calories_target": row.calories_target or 0,
            "protein_consumed": row.protein_consumed or 0,
            "protein_target": row.protein_target or 0,
            "sets_completed": row.sets_completed or 0,
            "sets_planned": row.sets_planned or 0,
            "workout_status": row.workout_status,
        })

    avg_days = max(len(rows), 1)
    return {
        "user_id": user_id,
        "days": days,
        "daily": daily,
        "summary": {
            "avg_daily_calories": round(totals["calories_consumed"] / avg_days, 1),
            "avg_daily_protein": round(totals["protein_consumed"] / avg_days, 1),
            "calorie_adherence_pct": round((totals["calories_consumed"] / max(totals["calories_target"], 1)) * 100, 1),
            "protein_adherence_pct": round((totals["protein_consumed"] / max(totals["protein_target"], 1)) * 100, 1),
            "workouts_completed": totals["workouts"],
            "workouts_planned": totals["planned_workouts"],
            "sets_completed": totals["sets_completed"],
            "sets_planned": totals["sets_planned"],
        }
    }
