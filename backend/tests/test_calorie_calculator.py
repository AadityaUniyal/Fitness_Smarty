"""
Unit Tests for Calorie / BMR / TDEE Calculations

Tests the Mifflin-St Jeor equation implementation and macro target logic
with known reference values.
"""

import pytest
from unittest.mock import MagicMock


def _make_analytics():
    """Create a NutritionAnalytics with a mocked DB session."""
    from app.nutrition_analytics import NutritionAnalytics

    mock_db = MagicMock()
    return NutritionAnalytics(db=mock_db)


class TestBMRCalculation:
    """Mifflin-St Jeor equation: BMR = 10w + 6.25h - 5a + s"""

    def test_male_standard(self):
        svc = _make_analytics()
        # 80kg, 180cm, 25yo male → 10(80) + 6.25(180) - 5(25) + 5 = 1805
        result = svc.calculate_bmr(80, 180, 25, "male")
        assert result == 1805.0

    def test_female_standard(self):
        svc = _make_analytics()
        # 60kg, 165cm, 30yo female → 10(60) + 6.25(165) - 5(30) - 161 = 1320.25
        result = svc.calculate_bmr(60, 165, 30, "female")
        assert result == 1320.2  # rounded to 1 decimal

    def test_male_lightweight(self):
        svc = _make_analytics()
        # 55kg, 170cm, 20yo male → 10(55) + 6.25(170) - 5(20) + 5 = 1517.5
        result = svc.calculate_bmr(55, 170, 20, "male")
        assert result == 1517.5

    def test_female_older(self):
        svc = _make_analytics()
        # 70kg, 160cm, 55yo female → 10(70) + 6.25(160) - 5(55) - 161 = 1264
        result = svc.calculate_bmr(70, 160, 55, "female")
        assert result == 1264.0

    def test_gender_case_insensitive(self):
        svc = _make_analytics()
        result_lower = svc.calculate_bmr(80, 180, 25, "male")
        result_upper = svc.calculate_bmr(80, 180, 25, "Male")
        assert result_lower == result_upper


class TestTDEECalculation:
    """TDEE = BMR × activity multiplier"""

    def test_sedentary(self):
        svc = _make_analytics()
        bmr = 1800.0
        result = svc.calculate_tdee(bmr, "sedentary")
        assert result == round(1800 * 1.2, 1)

    def test_moderate(self):
        svc = _make_analytics()
        bmr = 1800.0
        result = svc.calculate_tdee(bmr, "moderate")
        assert result == round(1800 * 1.55, 1)

    def test_active(self):
        svc = _make_analytics()
        bmr = 1800.0
        result = svc.calculate_tdee(bmr, "active")
        assert result == round(1800 * 1.725, 1)

    def test_very_active(self):
        svc = _make_analytics()
        bmr = 1800.0
        result = svc.calculate_tdee(bmr, "very_active")
        assert result == round(1800 * 1.9, 1)

    def test_unknown_activity_defaults_moderate(self):
        svc = _make_analytics()
        bmr = 1800.0
        result = svc.calculate_tdee(bmr, "unknown_level")
        assert result == round(1800 * 1.55, 1)


class TestBMRTDEEIntegration:
    """End-to-end BMR → TDEE calculation."""

    def test_full_pipeline_male_active(self):
        svc = _make_analytics()
        bmr = svc.calculate_bmr(80, 180, 25, "male")
        tdee = svc.calculate_tdee(bmr, "active")
        # BMR = 1805, TDEE = 1805 * 1.725 = 3113.625
        assert tdee == 3113.6

    def test_full_pipeline_female_sedentary(self):
        svc = _make_analytics()
        bmr = svc.calculate_bmr(60, 165, 30, "female")
        tdee = svc.calculate_tdee(bmr, "sedentary")
        # BMR = 1320.2, TDEE = 1320.2 * 1.2 = 1584.24
        assert tdee == round(1320.2 * 1.2, 1)
