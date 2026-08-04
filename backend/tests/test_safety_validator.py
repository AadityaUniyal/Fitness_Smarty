"""
Unit Tests for LLM Safety Validator

Tests the post-LLM output validation layer that enforces physiological
safety bounds on calorie suggestions and flags unsafe exercises for
users with specific health conditions.
"""

import pytest
from app.safety_validator import (
    MEDICAL_DISCLAIMER,
    sanitize_llm_response,
    validate_calorie_suggestion,
    validate_exercise_safety,
)


class TestCalorieBoundsValidation:
    """Calorie suggestions must fall within safe physiological ranges."""

    def test_normal_range_passes(self):
        result = validate_calorie_suggestion("Eat 2000 calories per day.")
        assert result.is_safe is True
        assert result.warnings == []

    def test_too_low_gets_clamped(self):
        result = validate_calorie_suggestion(
            "You should eat only 800 calories per day for rapid weight loss."
        )
        assert result.is_safe is False
        assert "1200" in result.sanitized_text
        assert len(result.warnings) == 1

    def test_too_high_gets_clamped(self):
        result = validate_calorie_suggestion(
            "Consume 6000 calories daily to bulk up."
        )
        assert result.is_safe is False
        assert "4000" in result.sanitized_text

    def test_pregnancy_mode_stricter_low_bound(self):
        result = validate_calorie_suggestion(
            "Limit to 1000 kcal while pregnant.",
            pregnancy_mode=True,
        )
        assert result.is_safe is False
        # Pregnancy lower bound is 1800
        assert "1800" in result.sanitized_text

    def test_pregnancy_mode_normal_passes(self):
        result = validate_calorie_suggestion(
            "Aim for 2200 calories daily.",
            pregnancy_mode=True,
        )
        assert result.is_safe is True

    def test_no_calorie_mention_passes(self):
        result = validate_calorie_suggestion(
            "Focus on protein-rich foods and stay hydrated."
        )
        assert result.is_safe is True
        assert result.warnings == []


class TestExerciseSafetyValidation:
    """Unsafe exercises should be flagged for specific conditions."""

    def test_no_flags_passes_everything(self):
        result = validate_exercise_safety(
            "Try deadlifts and box jumps for strength.",
        )
        assert result.is_safe is True

    def test_pregnancy_flags_unsafe_exercises(self):
        result = validate_exercise_safety(
            "Today's workout: deadlift 3x5, burpee intervals, walking lunges.",
            pregnancy_mode=True,
        )
        assert result.is_safe is False
        assert len(result.warnings) > 0
        # Both deadlift and burpee should be flagged
        warnings_text = " ".join(result.warnings)
        assert "deadlift" in warnings_text
        assert "burpee" in warnings_text

    def test_pregnancy_safe_exercises_pass(self):
        result = validate_exercise_safety(
            "Gentle yoga, walking, and light resistance bands.",
            pregnancy_mode=True,
        )
        assert result.is_safe is True

    def test_joint_issues_flag_high_impact(self):
        result = validate_exercise_safety(
            "Start with box jumps and sprinting drills.",
            has_joint_issues=True,
        )
        assert result.is_safe is False


class TestSanitizeLLMResponse:
    """Full pipeline: sanitize_llm_response runs all checks."""

    def test_clean_response_adds_disclaimer(self):
        result = sanitize_llm_response("Eat well and exercise regularly.")
        assert result["safety_passed"] is True
        assert result["disclaimer"] == MEDICAL_DISCLAIMER
        assert result["warnings"] == []

    def test_unsafe_calories_get_caught(self):
        result = sanitize_llm_response(
            "Restrict to 500 calories for rapid results!",
            user_flags={"pregnancy_mode": False},
        )
        assert result["safety_passed"] is False
        assert len(result["modifications"]) > 0

    def test_combined_flags(self):
        result = sanitize_llm_response(
            "Do burpees and eat 800 kcal daily.",
            user_flags={"pregnancy_mode": True},
        )
        assert result["safety_passed"] is False
        # Both calorie and exercise warnings
        assert len(result["warnings"]) >= 2

    def test_disclaimer_can_be_disabled(self):
        result = sanitize_llm_response(
            "Test response.", add_disclaimer=False
        )
        assert result["disclaimer"] is None
