"""
Graph-Based Muscle Recovery & Workout Readiness Engine
Tracks muscle fatigue dynamically over time using an exponential time-decay model,
and provides gating for next workout recommendations.
"""

from datetime import datetime, timedelta
import math
from typing import Dict, List, Set, Any, Optional, Tuple
from sqlalchemy.orm import Session
from . import models

# Exponential decay constant: fatigue decays by 50% every ~48 hours
# e^(-lambda * 48) = 0.5 => lambda = ln(2) / 48 approx 0.0144
DECAY_RATE_HOURLY = 0.0144

# Muscle graph definition: Muscle nodes and their synergistic connections
MUSCLE_CONNECTIONS = {
    "Quads": {"Glutes", "Calves"},
    "Hamstrings": {"Glutes", "Lower Back"},
    "Glutes": {"Quads", "Hamstrings", "Lower Back"},
    "Chest": {"Triceps", "Anterior Deltoids"},
    "Lats": {"Biceps", "Upper Back"},
    "Upper Back": {"Lats", "Biceps"},
    "Lower Back": {"Glutes", "Hamstrings"},
    "Anterior Deltoids": {"Chest", "Triceps"},
    "Triceps": {"Chest", "Anterior Deltoids"},
    "Biceps": {"Lats", "Upper Back"},
    "Core": set()
}

# Exercise to muscle group mapping with activation factors (primary=1.0, secondary=0.4-0.6)
EXERCISE_MUSCLE_MAP = {
    "squat": {"Quads": 1.0, "Glutes": 0.6, "Lower Back": 0.3},
    "deadlift": {"Lower Back": 1.0, "Hamstrings": 0.7, "Glutes": 0.6},
    "bench press": {"Chest": 1.0, "Triceps": 0.5, "Anterior Deltoids": 0.5},
    "overhead press": {"Anterior Deltoids": 1.0, "Triceps": 0.5, "Core": 0.2},
    "pull-up": {"Lats": 1.0, "Biceps": 0.5, "Upper Back": 0.4},
    "row": {"Lats": 0.8, "Upper Back": 0.8, "Biceps": 0.4},
    "lunge": {"Quads": 0.8, "Glutes": 0.8},
    "leg curl": {"Hamstrings": 1.0},
    "calf raise": {"Calves": 1.0},
    "plank": {"Core": 1.0}
}


def get_muscle_activations(exercise_name: str) -> Dict[str, float]:
    """
    Returns the activation factors for each muscle group affected by the exercise.
    """
    name_lower = exercise_name.lower()
    for key, mappings in EXERCISE_MUSCLE_MAP.items():
        if key in name_lower:
            return mappings
    return {}  # Unknown exercise has no muscle activation


def calculate_muscle_fatigue(workout_logs: List[Any], current_time: datetime = None) -> Dict[str, float]:
    """
    Processes workout logs in chronological order to compute current fatigue levels per muscle group.
    
    workout_logs: List of models.WorkoutLog or dict representation.
    """
    if not current_time:
        current_time = datetime.utcnow()

    # Sort logs chronologically (oldest to newest)
    sorted_logs = sorted(workout_logs, key=lambda log: getattr(log, "created_at", datetime.utcnow()))
    
    # Initialize fatigue levels
    fatigue: Dict[str, float] = {muscle: 0.0 for muscle in MUSCLE_CONNECTIONS}
    fatigue["Calves"] = 0.0
    
    last_time: Optional[datetime] = None

    for log in sorted_logs:
        log_time = getattr(log, "created_at", datetime.utcnow())
        
        # 1. Decay fatigue from last_time to log_time
        if last_time is not None:
            hours_passed = (log_time - last_time).total_seconds() / 3600.0
            decay_factor = math.exp(-DECAY_RATE_HOURLY * hours_passed)
            for muscle in fatigue:
                fatigue[muscle] *= decay_factor
                
        # 2. Extract exercise data and calculate newly generated fatigue
        exercises_data = getattr(log, "exercises_data", []) or []
        if isinstance(exercises_data, dict):
            # Safe parsing if it's stored as a dict instead of a list
            exercises_data = exercises_data.get("exercises", [])

        for ex in exercises_data:
            ex_name = ex.get("name", "")
            sets = ex.get("sets", [])
            
            # Compute raw volume: sets * reps * weight
            volume = 0.0
            for s in sets:
                reps = float(s.get("reps", 0))
                weight = float(s.get("weight", 0.0))
                volume += reps * weight
                
            if volume == 0.0:
                # Fallback to duration or repetition count if weight is missing
                reps_count = sum(float(s.get("reps", 8)) for s in sets)
                volume = reps_count * 15.0 # baseline weight equivalent

            # Get muscle activation multipliers
            activations = get_muscle_activations(ex_name)
            for muscle, multiplier in activations.items():
                if muscle not in fatigue:
                    fatigue[muscle] = 0.0
                # Scale fatigue addition: volume/1000 to keep it in a reasonable [0-100] scale
                fatigue[muscle] += (volume / 1000.0) * multiplier * 20.0

        last_time = log_time

    # Decay final fatigue levels to the target current_time
    if last_time is not None:
        hours_passed = (current_time - last_time).total_seconds() / 3600.0
        decay_factor = math.exp(-DECAY_RATE_HOURLY * hours_passed)
        for muscle in fatigue:
            fatigue[muscle] *= decay_factor

    return fatigue


def calculate_recovery_score(db: Session, user_id: str):
    """
    Computes a recovery readiness score (0-100) based on sleep, calorie balance, 
    and dynamic muscle fatigue calculations.
    """
    # Parse user_id
    try:
        user_id_int = int(user_id)
    except ValueError:
        user_id_int = None

    current_time = datetime.utcnow()
    
    # 1. Sleep Score
    threshold = current_time - timedelta(days=3)
    sleep_records = db.query(models.BiometricRecord).filter(
        models.BiometricRecord.user_id == str(user_id),
        models.BiometricRecord.category == 'sleep',
        models.BiometricRecord.timestamp >= threshold
    ).all() if hasattr(models, "BiometricRecord") else []
    
    if sleep_records:
        avg_sleep = sum(r.value for r in sleep_records) / len(sleep_records)
    else:
        avg_sleep = 7.5
    sleep_score = min(100.0, (avg_sleep / 8.0) * 100.0) if avg_sleep > 0 else 80.0

    # 2. Yesterday's Calories
    yesterday = current_time - timedelta(days=1)
    start_of_yesterday = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)
    end_of_yesterday = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
    
    meals = []
    workouts = []
    if user_id_int is not None:
        meals = db.query(models.MealLog).filter(
            models.MealLog.user_id == user_id_int,
            models.MealLog.created_at >= start_of_yesterday,
            models.MealLog.created_at <= end_of_yesterday
        ).all()
        workouts = db.query(models.WorkoutLog).filter(
            models.WorkoutLog.user_id == user_id_int,
            models.WorkoutLog.created_at >= start_of_yesterday,
            models.WorkoutLog.created_at <= end_of_yesterday
        ).all()

    total_eaten = sum(m.total_calories for m in meals) if meals else 2000.0
    total_burned = sum(w.calories_burned for w in workouts) if workouts else 300.0
    net_calories = total_eaten - total_burned
    deviation = abs(net_calories - 1600.0)
    calorie_score = max(0.0, 100.0 - (deviation / 15.0))

    # 3. Dynamic Muscle Recovery
    all_workouts = []
    if user_id_int is not None:
        all_workouts = db.query(models.WorkoutLog).filter(
            models.WorkoutLog.user_id == user_id_int
        ).all()

    fatigue_levels = calculate_muscle_fatigue(all_workouts, current_time)
    
    muscle_scores = {}
    for muscle, f_val in fatigue_levels.items():
        muscle_scores[muscle] = max(0.0, min(100.0, 100.0 - f_val))

    # Average recovery score of key muscle groups
    avg_muscle_recovery = sum(muscle_scores.values()) / len(muscle_scores) if muscle_scores else 100.0

    # Combine scores
    overall_score = (sleep_score * 0.3) + (calorie_score * 0.2) + (avg_muscle_recovery * 0.5)
    overall_score = max(0.0, min(100.0, overall_score))

    status = "Elite" if overall_score > 85 else "Operational" if overall_score > 65 else "Fatigued"
    
    if overall_score > 85:
        advice = "Excellent recovery. Muscles are fully primed for high-intensity lifting!"
    elif overall_score > 65:
        advice = "Operational state. Muscles are mostly recovered. Standard training volumes are recommended."
    else:
        fatigued_muscles = [m for m, s in muscle_scores.items() if s < 60.0]
        advice = f"High fatigue detected. Avoid training highly fatigued muscles: {', '.join(fatigued_muscles)}."

    return {
        "score": round(overall_score, 1),
        "status": status,
        "advice": advice,
        "sleep_hours_avg": round(avg_sleep, 1),
        "calorie_balance_yesterday": round(net_calories, 1),
        "muscle_group_recovery": {m: round(s, 1) for m, s in muscle_scores.items()},
        "last_sync": current_time
    }


def is_exercise_gated(exercise_name: str, muscle_recovery_scores: Dict[str, float], threshold: float = 50.0) -> Tuple[bool, str]:
    """
    Checks if an exercise should be gated (restricted) based on current muscle recovery scores.
    """
    activations = get_muscle_activations(exercise_name)
    for muscle, multiplier in activations.items():
        if multiplier >= 0.7:  # Primary targets only
            score = muscle_recovery_scores.get(muscle, 100.0)
            if score < threshold:
                return True, f"Primary muscle target ({muscle}) is highly fatigued (Recovery: {score:.1f}%)."
    return False, ""
