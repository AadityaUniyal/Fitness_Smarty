import pytest
from app.ml_models.shap_explainer import get_shap_explainer


def test_explain_recommendation_rule_trace():
    explainer = get_shap_explainer()
    
    recommendation = {
        "name": "Steak and Asparagus",
        "foods": ["steak", "asparagus"],
        "macros": {
            "protein_g": 42.0,
            "carbs_g": 5.0,
            "fat_g": 22.0,
            "calories": 380.0
        }
    }
    
    user_features = {
        "protein_target": 150.0,
        "calorie_target": 2000.0,
        "preferred_ingredients": ["steak"]
    }
    
    res = explainer.explain_recommendation(recommendation, user_features)
    
    assert res["recommendation"] == "Steak and Asparagus"
    assert "rule_trace" in res
    assert len(res["rule_trace"]) > 0
    assert "Steak and Asparagus" in res["explanation"]
    assert "steak" in res["explanation"]
    assert res["model"] == "rule_trace_engine_v1"
    
    # Check trace content
    trace_str = " ".join(res["rule_trace"])
    assert "Provides 42.0g protein" in trace_str
    assert "Contains user-tagged preferred ingredients" in trace_str
    assert "Under 25% of daily calories" in trace_str
