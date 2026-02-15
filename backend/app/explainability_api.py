"""
Explainability API Router

Endpoints for model interpretability and explanations
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

router = APIRouter(prefix="/api/explain", tags=["explainability"])


class RecommendationToExplain(BaseModel):
    """Recommendation to explain"""
    meal_id: int
    name: str
    score: float


class UserFeatures(BaseModel):
    """User features for explanation"""
    protein_target: float = 150
    calorie_target: float = 2000
    preferred_ingredients: list = []


@router.post("/recommendation")
async def explain_recommendation(
    recommendation: RecommendationToExplain,
    user_features: UserFeatures
):
    """
    Explain why a specific meal was recommended
    
    Uses SHAP to show feature contributions
    """
    try:
        from app.ml_models.shap_explainer import get_shap_explainer
        explainer = get_shap_explainer()
        
        explanation = explainer.explain_recommendation(
            recommendation.dict(),
            user_features.dict()
        )
        
        return explanation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@router.get("/feature-importance/{model_name}")
async def get_feature_importance(model_name: str):
    """
    Get feature importance for a model
    
    Shows which features matter most for predictions
    """
    try:
        from app.ml_models.shap_explainer import get_shap_explainer
        explainer = get_shap_explainer()
        
        importance = explainer.feature_importance(model_name)
        
        return importance
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature importance failed: {str(e)}")


@router.post("/decision-path")
async def get_decision_path(prediction: Dict[str, Any]):
    """
    Show step-by-step decision path
    
    Explains how the model arrived at its prediction
    """
    try:
        from app.ml_models.shap_explainer import get_shap_explainer
        explainer = get_shap_explainer()
        
        path = explainer.decision_path(prediction)
        
        return path
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision path failed: {str(e)}")


@router.get("/models/status")
async def get_explainability_status():
    """Check explainability model status"""
    
    try:
        import shap
        SHAP_AVAILABLE = True
    except:
        SHAP_AVAILABLE = False
    
    status = {
        'shap': {
            'available': SHAP_AVAILABLE,
            'status': 'ready' if SHAP_AVAILABLE else 'mock',
            'description': 'SHAP values for feature importance'
        }
    }
    
    return {
        'models': status,
        'available_count': 1,
        'total_count': 1,
        'recommended_setup': 'Install shap',
        'phase': 6
    }
