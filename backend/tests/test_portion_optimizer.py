import pytest
from app.recommendation_engine import PortionOptimizer


def test_portion_optimizer():
    optimizer = PortionOptimizer()
    
    # Define food components
    meal_components = [
        {
            "name": "Chicken Breast",
            "nutrition_per_100g": {"calories": 165.0, "protein": 31.0, "carbs": 0.0, "fat": 3.6}
        },
        {
            "name": "White Rice",
            "nutrition_per_100g": {"calories": 130.0, "protein": 2.7, "carbs": 28.0, "fat": 0.3}
        }
    ]
    
    # Target: 500 kcal, 40g protein
    result = optimizer.optimize_portions(meal_components, target_calories=500.0, target_protein=40.0)
    
    assert "portions_grams" in result
    assert "total_nutrition" in result
    assert "accuracy" in result
    
    portions = result["portions_grams"]
    assert "Chicken Breast" in portions
    assert "White Rice" in portions
    
    # Portions should be bounded
    for food, amount in portions.items():
        assert 30.0 <= amount <= 400.0
        
    # Verify resulting nutrition math
    chicken_mult = portions["Chicken Breast"] / 100.0
    rice_mult = portions["White Rice"] / 100.0
    expected_calories = (165.0 * chicken_mult) + (130.0 * rice_mult)
    expected_protein = (31.0 * chicken_mult) + (2.7 * rice_mult)
    
    assert abs(result["total_nutrition"]["calories"] - expected_calories) < 1.0
    assert abs(result["total_nutrition"]["protein_g"] - expected_protein) < 1.0
