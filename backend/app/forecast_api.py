from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import get_db

router = APIRouter(prefix="/api/forecast", tags=["time-series"])


class WeightDataPoint(BaseModel):
    """Single day of weight data"""

    date: str
    weight: float
    calories: float = 2000
    activity_minutes: int = 30


class NutritionDataPoint(BaseModel):
    """Single day of nutrition data"""

    date: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float


class PredictWeightRequest(BaseModel):
    """Payload wrapper for predict-weight endpoint"""

    historical_data: List[WeightDataPoint]
    days_ahead: int = 7


class AnalyzeNutritionRequest(BaseModel):
    """Payload wrapper for analyze-nutrition-trends endpoint"""

    historical_data: List[NutritionDataPoint]
    forecast_days: int = 14


@router.post("/predict-weight")
async def predict_future_weight(request: PredictWeightRequest):
    try:
        # Get LSTM predictor
        from .ml_models.lstm_predictor import get_weight_predictor

        predictor = get_weight_predictor()

        data_dicts = [point.model_dump() for point in request.historical_data]

        results = predictor.predict_weight(data_dicts, request.days_ahead)
        return results

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Weight prediction failed: {str(e)}"
        )


@router.post("/analyze-nutrition-trends")
async def analyze_nutrition_trends(request: AnalyzeNutritionRequest):
    try:
        # Get Prophet analyzer
        from .ml_models.prophet_analyzer import get_trend_analyzer

        analyzer = get_trend_analyzer()

        data_dicts = [point.model_dump() for point in request.historical_data]

        results = analyzer.analyze_nutrition_trends(
            data_dicts, request.forecast_days
        )

        return results

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Trend analysis failed: {str(e)}"
        )


@router.get("/goal-projection")
async def project_goal_achievement(
    user_id: int, goal_weight: float, db: Session = Depends(get_db)
):
    try:
        mock_history = [
            {
                "date": f"2024-02-{i:02d}",
                "weight": 78 - (i * 0.1),
                "calories": 1800,
                "activity_minutes": 45,
            }
            for i in range(1, 15)
        ]

        from .ml_models.lstm_predictor import get_weight_predictor

        predictor = get_weight_predictor()

        predictions = predictor.predict_weight(mock_history, days_ahead=30)

        goal_date = None
        for pred in predictions["predictions"]:
            if pred["predicted_weight"] <= goal_weight:
                goal_date = pred["date"]
                break

        if goal_date:
            return {
                "goal_weight": goal_weight,
                "current_weight": mock_history[-1]["weight"],
                "projected_date": goal_date,
                "days_remaining": len([
                    p
                    for p in predictions["predictions"]
                    if p["date"] <= goal_date
                ]),
                "achievable": True,
                "confidence": predictions["confidence_score"],
            }
        else:
            return {
                "goal_weight": goal_weight,
                "current_weight": mock_history[-1]["weight"],
                "projected_date": None,
                "achievable": False,
                "message": (
                    "Goal not reached in 30-day forecast. "
                    "Adjust diet/activity or extend timeline."
                ),
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Goal projection failed: {str(e)}"
        )


@router.get("/models/status")
async def get_forecast_models_status():
    """
    Check time-series model availability
    """
    try:
        import torch  # noqa: F401

        TORCH_AVAILABLE = True
    except Exception:
        TORCH_AVAILABLE = False

    try:
        from prophet import Prophet  # noqa: F401
        PROPHET_AVAILABLE = True
    except Exception:
        PROPHET_AVAILABLE = False

    status = {
        "lstm": {
            "available": TORCH_AVAILABLE,
            "status": "ready" if TORCH_AVAILABLE else "not_installed",
            "description": "Weight prediction using LSTM neural networks",
        },
        "prophet": {
            "available": PROPHET_AVAILABLE,
            "status": "ready" if PROPHET_AVAILABLE else "not_installed",
            "description": "Nutrition trend analysis and forecasting",
        },
    }

    available_count = sum(1 for model in status.values() if model["available"])

    return {
        "models": status,
        "available_count": available_count,
        "total_count": len(status),
        "recommended_setup": "Install torch and prophet",
        "phase": 3,
    }