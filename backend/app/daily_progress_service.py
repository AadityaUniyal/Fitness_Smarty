from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from . import models


def _today_start(ref: Optional[datetime] = None) -> datetime:
    ref = ref or datetime.utcnow()
    return datetime(ref.year, ref.month, ref.day)


@dataclass
class PlannedExercise:
    id: int
    name: str
    sets: int
    reps: str
    duration_sec: int
    rest_sec: int
    calories_per_set: float


class DailyProgressService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_today(self, user_id: int) -> models.DailyProgress:
        today = _today_start()
        row = (
            self.db.query(models.DailyProgress)
            .filter(models.DailyProgress.user_id == user_id)
            .filter(models.DailyProgress.date >= today)
            .order_by(models.DailyProgress.date.desc())
            .first()
        )
        if row:
            return row
        return self.create_today(user_id)

    def create_today(
        self,
        user_id: int,
        workout_planned_id: Optional[int] = None,
        sets_planned: int = 0,
        targets: Optional[Dict[str, float]] = None,
    ) -> models.DailyProgress:
        targets = targets or {}
        today = _today_start()
        row = models.DailyProgress(
            user_id=user_id,
            date=today,
            workout_planned_id=workout_planned_id,
            sets_planned=sets_planned,
            calories_target=targets.get("calories", 0) or 0,
            protein_target=targets.get("protein", 0) or 0,
            carbs_target=targets.get("carbs", 0) or 0,
            fats_target=targets.get("fats", 0) or 0,
            water_target_ml=targets.get("water_ml", 0) or 0,
            calories_remaining=targets.get("calories", 0) or 0,
            protein_remaining=targets.get("protein", 0) or 0,
            carbs_remaining=targets.get("carbs", 0) or 0,
            fats_remaining=targets.get("fats", 0) or 0,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def sync_from_logs(self, user_id: int) -> models.DailyProgress:
        row = self.get_or_create_today(user_id)
        today = _today_start()
        meals = (
            self.db.query(models.MealLog)
            .filter(models.MealLog.user_id == user_id)
            .filter(models.MealLog.created_at >= today)
            .all()
        )
        workouts = (
            self.db.query(models.WorkoutLog)
            .filter(models.WorkoutLog.user_id == user_id)
            .filter(models.WorkoutLog.created_at >= today)
            .all()
        )
        row.calories_consumed = round(sum(m.total_calories or 0 for m in meals), 1)
        row.protein_consumed = round(sum(m.total_protein or 0 for m in meals), 1)
        row.carbs_consumed = round(sum(m.total_carbs or 0 for m in meals), 1)
        row.fats_consumed = round(sum(m.total_fats or 0 for m in meals), 1)
        row.calories_remaining = max(0, (row.calories_target or 0) - row.calories_consumed)
        row.protein_remaining = max(0, (row.protein_target or 0) - row.protein_consumed)
        row.carbs_remaining = max(0, (row.carbs_target or 0) - row.carbs_consumed)
        row.fats_remaining = max(0, (row.fats_target or 0) - row.fats_consumed)
        row.sets_completed = sum(len((w.exercises_data or [])) for w in workouts)
        if row.sets_planned and row.sets_completed >= row.sets_planned:
            row.workout_status = "done"
        elif row.sets_completed > 0:
            row.workout_status = "in_progress"
        else:
            row.workout_status = "not_started"
        self.db.commit()
        self.db.refresh(row)
        return row

    def log_meal(self, user_id: int, meal_log: models.MealLog) -> models.DailyProgress:
        return self.sync_from_logs(user_id)

    def log_workout_set(
        self,
        user_id: int,
        sets_added: int = 1,
        workout_planned_id: Optional[int] = None,
    ) -> models.DailyProgress:
        row = self.get_or_create_today(user_id)
        if workout_planned_id is not None:
            row.workout_planned_id = workout_planned_id
        row.sets_completed = (row.sets_completed or 0) + max(1, sets_added)
        if row.sets_planned and row.sets_completed >= row.sets_planned:
            row.workout_status = "done"
        else:
            row.workout_status = "in_progress"
        self.db.commit()
        self.db.refresh(row)
        return row

    def summary(self, user_id: int) -> Dict[str, Any]:
        row = self.get_or_create_today(user_id)
        return {
            "id": row.id,
            "date": row.date.isoformat() if row.date else None,
            "calories": {
                "target": row.calories_target,
                "consumed": row.calories_consumed,
                "remaining": row.calories_remaining,
            },
            "protein": {
                "target": row.protein_target,
                "consumed": row.protein_consumed,
                "remaining": row.protein_remaining,
            },
            "carbs": {
                "target": row.carbs_target,
                "consumed": row.carbs_consumed,
                "remaining": row.carbs_remaining,
            },
            "fats": {
                "target": row.fats_target,
                "consumed": row.fats_consumed,
                "remaining": row.fats_remaining,
            },
            "workout": {
                "planned_id": row.workout_planned_id,
                "status": row.workout_status,
                "sets_completed": row.sets_completed,
                "sets_planned": row.sets_planned,
            },
            "water": {
                "intake_ml": row.water_intake_ml,
                "target_ml": row.water_target_ml,
            },
            "check_in": {
                "energy_level": row.energy_level,
                "soreness_level": row.soreness_level,
                "symptom_severity": row.symptom_severity,
            },
        }

