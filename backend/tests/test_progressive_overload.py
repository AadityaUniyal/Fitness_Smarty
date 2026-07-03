import pytest
from app.progressive_overload import (
    calculate_session_volume,
    calculate_one_rep_max,
    detect_plateau,
    prescribe_next_session
)


def test_calculate_session_volume():
    sets = [
        {"reps": 10, "weight": 50.0},
        {"reps": 8, "weight": 52.5},
        {"reps": 6, "weight": 55.0}
    ]
    # (10 * 50) + (8 * 52.5) + (6 * 55) = 500 + 420 + 330 = 1250.0
    assert calculate_session_volume(sets) == 1250.0


def test_calculate_one_rep_max():
    # Epley: 1RM = 100 * (1 + 10/30) = 133.333
    assert abs(calculate_one_rep_max(100.0, 10) - 133.33) < 0.1
    assert calculate_one_rep_max(100.0, 1) == 100.0
    assert calculate_one_rep_max(100.0, 0) == 0.0


def test_detect_plateau():
    # Volumes increasing -> no plateau
    assert not detect_plateau([1000.0, 1050.0, 1100.0, 1150.0])
    
    # Volumes flat/decreasing -> plateau detected
    assert detect_plateau([1000.0, 1100.0, 1100.0, 1090.0, 1100.0])
    
    # Too few sessions -> no plateau
    assert not detect_plateau([1000.0, 1000.0])


def test_prescribe_next_session_double_progression():
    # Initial session
    res = prescribe_next_session([], "Squats")
    assert len(res["sets"]) == 3
    assert res["progression_applied"] == "initial"
    
    # Complete max reps (e.g. max_reps = 12, min_reps = 8)
    history = [
        {"sets": [{"reps": 12, "weight": 60.0}, {"reps": 12, "weight": 60.0}, {"reps": 12, "weight": 60.0}]}
    ]
    res2 = prescribe_next_session(history, "Squats", min_reps=8, max_reps=12, weight_increment=2.5)
    assert res2["progression_applied"] == "weight_increase"
    assert res2["sets"][0]["weight"] == 62.5
    assert res2["sets"][0]["reps"] == 8
    
    # Incomplete set (some set reps < max_reps)
    history_incomplete = [
        {"sets": [{"reps": 12, "weight": 60.0}, {"reps": 10, "weight": 60.0}, {"reps": 9, "weight": 60.0}]}
    ]
    res3 = prescribe_next_session(history_incomplete, "Squats", min_reps=8, max_reps=12)
    assert res3["progression_applied"] == "rep_increase"
    # First incomplete set reps was 10, should increment to 11
    assert res3["sets"][1]["reps"] == 11
    assert res3["sets"][1]["weight"] == 60.0


def test_prescribe_next_session_1rm():
    history = [
        {"sets": [{"reps": 10, "weight": 60.0}, {"reps": 10, "weight": 60.0}]}
    ]
    # 1RM estimated at 60 * (1 + 10/30) = 80kg
    # Target 1RM step-up is 80 * 1.025 = 82kg
    # Target reps: 10. Weight = 82 / (1 + 10/30) = 61.5 -> rounded to 61.5
    res = prescribe_next_session(history, "Squats", progression_type="one_rep_max")
    assert res["progression_applied"] == "1rm_stepping"
    assert len(res["sets"]) == 2
    assert res["sets"][0]["reps"] == 10
    assert res["sets"][0]["weight"] > 60.0


def test_prescribe_next_session_plateau():
    history = [
        {"sets": [{"reps": 10, "weight": 60.0}]},
        {"sets": [{"reps": 10, "weight": 60.0}]},
        {"sets": [{"reps": 10, "weight": 60.0}]},
        {"sets": [{"reps": 10, "weight": 60.0}]}
    ]
    res = prescribe_next_session(history, "Squats")
    assert res["plateau_detected"]
    assert res["progression_applied"] == "deload"
    # Weight should deload by 10%: 60 * 0.9 = 54
    assert res["sets"][0]["weight"] == 54.0
