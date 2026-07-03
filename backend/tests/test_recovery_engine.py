import pytest
from datetime import datetime, timedelta
from app.recovery_engine import (
    calculate_muscle_fatigue,
    is_exercise_gated,
    EXERCISE_MUSCLE_MAP
)


class MockWorkoutLog:
    def __init__(self, created_at, exercises_data):
        self.created_at = created_at
        self.exercises_data = exercises_data


def test_calculate_muscle_fatigue():
    # Setup some mock workouts
    # Squats fatigue Quads (Primary=1.0) and Glutes (Secondary=0.6)
    w1 = MockWorkoutLog(
        created_at=datetime.utcnow() - timedelta(hours=24),
        exercises_data=[
            {
                "name": "Barbell Squats",
                "sets": [{"reps": 10, "weight": 100.0}]  # volume = 1000.0
            }
        ]
    )
    
    # 1. Test immediate/decayed fatigue
    # Fatigue generation formula: (volume/1000) * multiplier * 20.0
    # For Quads: (1000/1000) * 1.0 * 20.0 = 20.0 fatigue added
    # Decay rate hourly is 0.0144. After 24 hours: 20.0 * e^(-0.0144 * 24) = 20.0 * e^(-0.3456) approx 20.0 * 0.7078 = 14.15
    fatigue = calculate_muscle_fatigue([w1], current_time=datetime.utcnow())
    
    assert fatigue["Quads"] > 0
    assert abs(fatigue["Quads"] - 14.15) < 1.0
    # Glutes secondary (0.6): 12.0 fatigue added. After 24 hours: approx 8.5
    assert abs(fatigue["Glutes"] - 8.49) < 1.0


def test_is_exercise_gated():
    # If Quads are highly fatigued (recovery score < 50, i.e., fatigue > 50)
    muscle_scores = {
        "Quads": 45.0,
        "Chest": 90.0
    }
    
    gated, reason = is_exercise_gated("Barbell Squat", muscle_scores)
    assert gated is True
    assert "Quads" in reason
    
    gated_chest, reason_chest = is_exercise_gated("Bench Press", muscle_scores)
    assert gated_chest is False
    assert reason_chest == ""
