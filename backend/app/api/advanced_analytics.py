"""
Advanced Analytics API - Visualization Data Endpoints
Provides chart/graph data for frontend visualization
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from app import database, models
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Advanced Analytics"])


@router.get("/weekly-trends/{user_id}")
def get_weekly_trends(
    user_id: str,
    weeks: int = Query(4, ge=1, le=12, description="Number of weeks to analyze"),
    db: Session = Depends(database.get_db),
):
    """
    Get weekly aggregated trends for calories, macros, and exercise.
    Returns data suitable for line charts and trend visualization.
    """
    try:
        start_date = datetime.utcnow() - timedelta(weeks=weeks)
        
        # Get meal data grouped by week
        meal_data = db.query(
            func.strftime('%Y-%W', models.MealLog.created_at).label('week'),
            func.sum(models.MealLog.total_calories).label('total_calories'),
            func.sum(models.MealLog.total_protein).label('total_protein'),
            func.sum(models.MealLog.total_carbs).label('total_carbs'),
            func.sum(models.MealLog.total_fats).label('total_fats'),
            func.count(models.MealLog.id).label('meal_count')
        ).filter(
            and_(
                models.MealLog.user_id == user_id,
                models.MealLog.created_at >= start_date
            )
        ).group_by('week').order_by('week').all()
        
        # Get workout data grouped by week
        workout_data = db.query(
            func.strftime('%Y-%W', models.WorkoutLog.created_at).label('week'),
            func.sum(models.WorkoutLog.calories_burned).label('calories_burned'),
            func.sum(models.WorkoutLog.duration_minutes).label('total_minutes'),
            func.count(models.WorkoutLog.id).label('workout_count')
        ).filter(
            and_(
                models.WorkoutLog.user_id == user_id,
                models.WorkoutLog.created_at >= start_date
            )
        ).group_by('week').order_by('week').all()
        
        # Format data for frontend
        weekly_data = []
        meal_dict = {row.week: row for row in meal_data}
        workout_dict = {row.week: row for row in workout_data}
        
        all_weeks = sorted(set(list(meal_dict.keys()) + list(workout_dict.keys())))
        
        for week in all_weeks:
            meal = meal_dict.get(week)
            workout = workout_dict.get(week)
            
            weekly_data.append({
                "week": week,
                "nutrition": {
                    "calories_consumed": float(meal.total_calories) if meal else 0,
                    "protein": float(meal.total_protein) if meal else 0,
                    "carbs": float(meal.total_carbs) if meal else 0,
                    "fats": float(meal.total_fats) if meal else 0,
                    "meal_count": int(meal.meal_count) if meal else 0
                },
                "exercise": {
                    "calories_burned": float(workout.calories_burned) if workout else 0,
                    "total_minutes": int(workout.total_minutes) if workout else 0,
                    "workout_count": int(workout.workout_count) if workout else 0
                },
                "net_calories": (
                    (float(meal.total_calories) if meal else 0) - 
                    (float(workout.calories_burned) if workout else 0)
                )
            })
        
        return {
            "user_id": user_id,
            "weeks_analyzed": weeks,
            "data": weekly_data
        }
        
    except Exception as e:
        logger.error(f"Weekly trends error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calorie-balance/{user_id}")
def get_calorie_balance(
    user_id: str,
    days: int = Query(30, ge=7, le=90, description="Number of days to analyze"),
    db: Session = Depends(database.get_db),
):
    """
    Get daily calorie consumption vs burn data for visualization.
    Perfect for stacked bar charts or area charts.
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily meal calories
        meals = db.query(
            func.date(models.MealLog.created_at).label('date'),
            func.sum(models.MealLog.total_calories).label('consumed')
        ).filter(
            and_(
                models.MealLog.user_id == user_id,
                models.MealLog.created_at >= start_date
            )
        ).group_by('date').all()
        
        # Daily workout calories
        workouts = db.query(
            func.date(models.WorkoutLog.created_at).label('date'),
            func.sum(models.WorkoutLog.calories_burned).label('burned')
        ).filter(
            and_(
                models.WorkoutLog.user_id == user_id,
                models.WorkoutLog.created_at >= start_date
            )
        ).group_by('date').all()
        
        meal_dict = {str(row.date): float(row.consumed) for row in meals}
        workout_dict = {str(row.date): float(row.burned) for row in workouts}
        
        # Generate daily data for all days in range
        daily_data = []
        current_date = start_date.date()
        end_date = datetime.utcnow().date()
        
        while current_date <= end_date:
            date_str = str(current_date)
            consumed = meal_dict.get(date_str, 0)
            burned = workout_dict.get(date_str, 0)
            
            daily_data.append({
                "date": date_str,
                "consumed": consumed,
                "burned": burned,
                "net": consumed - burned,
                "surplus": max(0, consumed - burned),
                "deficit": max(0, burned - consumed)
            })
            
            current_date += timedelta(days=1)
        
        # Calculate summary stats
        total_consumed = sum(d["consumed"] for d in daily_data)
        total_burned = sum(d["burned"] for d in daily_data)
        
        return {
            "user_id": user_id,
            "period": {
                "start": str(start_date.date()),
                "end": str(end_date),
                "days": days
            },
            "summary": {
                "total_consumed": round(total_consumed, 1),
                "total_burned": round(total_burned, 1),
                "net_balance": round(total_consumed - total_burned, 1),
                "avg_daily_consumed": round(total_consumed / days, 1),
                "avg_daily_burned": round(total_burned / days, 1)
            },
            "daily_data": daily_data
        }
        
    except Exception as e:
        logger.error(f"Calorie balance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/macro-distribution/{user_id}")
def get_macro_distribution(
    user_id: str,
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(database.get_db),
):
    """
    Get macronutrient distribution over time.
    Returns data for pie charts and stacked area charts.
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Daily macro breakdown
        daily_macros = db.query(
            func.date(models.MealLog.created_at).label('date'),
            func.sum(models.MealLog.total_protein).label('protein'),
            func.sum(models.MealLog.total_carbs).label('carbs'),
            func.sum(models.MealLog.total_fats).label('fats')
        ).filter(
            and_(
                models.MealLog.user_id == user_id,
                models.MealLog.created_at >= start_date
            )
        ).group_by('date').order_by('date').all()
        
        # Format for frontend
        daily_data = []
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        
        for row in daily_macros:
            protein = float(row.protein or 0)
            carbs = float(row.carbs or 0)
            fats = float(row.fats or 0)
            
            total_protein += protein
            total_carbs += carbs
            total_fats += fats
            
            # Calculate calories from macros
            protein_cals = protein * 4
            carbs_cals = carbs * 4
            fats_cals = fats * 9
            total_cals = protein_cals + carbs_cals + fats_cals
            
            daily_data.append({
                "date": str(row.date),
                "protein": round(protein, 1),
                "carbs": round(carbs, 1),
                "fats": round(fats, 1),
                "protein_percentage": round((protein_cals / total_cals * 100) if total_cals > 0 else 0, 1),
                "carbs_percentage": round((carbs_cals / total_cals * 100) if total_cals > 0 else 0, 1),
                "fats_percentage": round((fats_cals / total_cals * 100) if total_cals > 0 else 0, 1)
            })
        
        # Overall distribution
        total_protein_cals = total_protein * 4
        total_carbs_cals = total_carbs * 4
        total_fats_cals = total_fats * 9
        grand_total_cals = total_protein_cals + total_carbs_cals + total_fats_cals
        
        return {
            "user_id": user_id,
            "period_days": days,
            "overall_distribution": {
                "protein": {
                    "grams": round(total_protein, 1),
                    "calories": round(total_protein_cals, 1),
                    "percentage": round((total_protein_cals / grand_total_cals * 100) if grand_total_cals > 0 else 0, 1)
                },
                "carbs": {
                    "grams": round(total_carbs, 1),
                    "calories": round(total_carbs_cals, 1),
                    "percentage": round((total_carbs_cals / grand_total_cals * 100) if grand_total_cals > 0 else 0, 1)
                },
                "fats": {
                    "grams": round(total_fats, 1),
                    "calories": round(total_fats_cals, 1),
                    "percentage": round((total_fats_cals / grand_total_cals * 100) if grand_total_cals > 0 else 0, 1)
                }
            },
            "daily_data": daily_data
        }
        
    except Exception as e:
        logger.error(f"Macro distribution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exercise-heatmap/{user_id}")
def get_exercise_heatmap(
    user_id: str,
    weeks: int = Query(12, ge=4, le=52),
    db: Session = Depends(database.get_db),
):
    """
    Get exercise frequency data for calendar heatmap visualization.
    Returns workout count and intensity per day.
    """
    try:
        start_date = datetime.utcnow() - timedelta(weeks=weeks)
        
        # Get daily workout data
        workouts = db.query(
            func.date(models.WorkoutLog.created_at).label('date'),
            func.count(models.WorkoutLog.id).label('workout_count'),
            func.sum(models.WorkoutLog.duration_minutes).label('total_minutes'),
            func.sum(models.WorkoutLog.calories_burned).label('total_calories')
        ).filter(
            and_(
                models.WorkoutLog.user_id == user_id,
                models.WorkoutLog.created_at >= start_date
            )
        ).group_by('date').all()
        
        # Format for heatmap
        heatmap_data = []
        for row in workouts:
            # Calculate intensity level (0-4 scale)
            workout_count = int(row.workout_count)
            total_minutes = int(row.total_minutes or 0)
            
            if workout_count == 0:
                intensity = 0
            elif total_minutes < 20:
                intensity = 1
            elif total_minutes < 40:
                intensity = 2
            elif total_minutes < 60:
                intensity = 3
            else:
                intensity = 4
            
            heatmap_data.append({
                "date": str(row.date),
                "workout_count": workout_count,
                "total_minutes": total_minutes,
                "calories_burned": float(row.total_calories or 0),
                "intensity": intensity
            })
        
        # Calculate streak data
        workout_dates = {d["date"] for d in heatmap_data}
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        current_date = datetime.utcnow().date()
        for i in range(weeks * 7):
            check_date = str(current_date - timedelta(days=i))
            if check_date in workout_dates:
                temp_streak += 1
                if i < 7:  # Only count recent days for current streak
                    current_streak = temp_streak
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 0
                if i < 7:
                    current_streak = 0
        
        longest_streak = max(longest_streak, temp_streak)
        
        return {
            "user_id": user_id,
            "weeks_analyzed": weeks,
            "heatmap_data": heatmap_data,
            "statistics": {
                "total_workouts": len(heatmap_data),
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "active_days": len(workout_dates),
                "total_days": weeks * 7,
                "activity_rate": round(len(workout_dates) / (weeks * 7) * 100, 1)
            }
        }
        
    except Exception as e:
        logger.error(f"Exercise heatmap error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress-metrics/{user_id}")
def get_progress_metrics(
    user_id: str,
    days: int = Query(90, ge=30, le=365),
    db: Session = Depends(database.get_db),
):
    """
    Get comprehensive progress metrics including weight, body composition,
    and performance trends over time.
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get biometric readings
        biometrics = db.query(models.BiometricReading).filter(
            and_(
                models.BiometricReading.user_id == user_id,
                models.BiometricReading.created_at >= start_date
            )
        ).order_by(models.BiometricReading.created_at).all()
        
        # Get progress snapshots
        snapshots = db.query(models.ProgressSnapshot).filter(
            and_(
                models.ProgressSnapshot.user_id == user_id,
                models.ProgressSnapshot.date >= start_date
            )
        ).order_by(models.ProgressSnapshot.date).all()
        
        # Format biometric data
        biometric_data = [{
            "date": str(b.created_at.date()),
            "weight_kg": float(b.weight_kg) if b.weight_kg else None,
            "body_fat_pct": float(b.body_fat_pct) if b.body_fat_pct else None,
            "muscle_mass_kg": float(b.muscle_mass_kg) if b.muscle_mass_kg else None,
            "heart_rate": int(b.heart_rate) if b.heart_rate else None
        } for b in biometrics]
        
        # Calculate trends
        weights = [b.weight_kg for b in biometrics if b.weight_kg]
        body_fats = [b.body_fat_pct for b in biometrics if b.body_fat_pct]
        
        weight_change = None
        body_fat_change = None
        
        if len(weights) >= 2:
            weight_change = float(weights[-1] - weights[0])
        if len(body_fats) >= 2:
            body_fat_change = float(body_fats[-1] - body_fats[0])
        
        return {
            "user_id": user_id,
            "period_days": days,
            "biometric_data": biometric_data,
            "snapshot_count": len(snapshots),
            "trends": {
                "weight_change_kg": round(weight_change, 2) if weight_change else None,
                "body_fat_change_pct": round(body_fat_change, 2) if body_fat_change else None,
                "readings_count": len(biometrics)
            }
        }
        
    except Exception as e:
        logger.error(f"Progress metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
