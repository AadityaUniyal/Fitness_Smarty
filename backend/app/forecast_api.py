"""
Time-Series API Router

Endpoints for weight prediction and nutrition trend forecasting
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from app.database import get_db

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


@router.post("/predict-weight")
async def predict_future_weight(
    historical_data: List[WeightDataPoint],
    days_ahead: int = 7
):
    """
    Predict future weight using LSTM
    
    - **historical_data**: List of weight measurements with dates
    - **days_ahead**: Number of days to forecast (default: 7)
    
    Returns predictions with confidence intervals
    """
    try:
        # Get LSTM predictor
        from app.models.lstm_predictor import get_weight_predictor
        predictor = get_weight_predictor()
        
        # Convert Pydantic models to dicts
        data_dicts = [point.dict() for point in historical_data]
        
        # Predict
        results = predictor.predict_weight(data_dicts, days_ahead)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weight prediction failed: {str(e)}")


@router.post("/analyze-nutrition-trends")
async def analyze_nutrition_trends(
    historical_data: List[NutritionDataPoint],
    forecast_days: int = 14
):
    """
    Analyze nutrition trends using Prophet
    
    - **historical_data**: List of daily nutrition logs
    - **forecast_days**: Days to forecast (default: 14)
    
    Returns trends, forecasts, and actionable insights
    """
    try:
        # Get Prophet analyzer
        from app.models.prophet_analyzer import get_trend_analyzer
        analyzer = get_trend_analyzer()
        
        # Convert to dicts
        data_dicts = [point.dict() for point in historical_data]
        
        # Analyze
        results = analyzer.analyze_nutrition_trends(data_dicts, forecast_days)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/goal-projection")
async def project_goal_achievement(
    user_id: int,
    goal_weight: float,
    db: Session = Depends(get_db)
):
    """
    Project when user will reach their weight goal
    
    Uses historical data + LSTM to estimate time to goal
    """
    try:
        # In production: fetch user's weight history from DB
        # For now: mock data
        mock_history = [
            {"date": f"2024-02-{i:02d}", "weight": 78 - (i * 0.1), "calories": 1800, "activity_minutes": 45}
            for i in range(1, 15)
        ]
        
        from app.models.lstm_predictor import get_weight_predictor
        predictor = get_weight_predictor()
        
        # Predict next 30 days
        predictions = predictor.predict_weight(mock_history, days_ahead=30)
        
        # Find when goal is reached
        goal_date = None
        for pred in predictions['predictions']:
            if pred['predicted_weight'] <= goal_weight:
                goal_date = pred['date']
                break
        
        if goal_date:
            return {
                'goal_weight': goal_weight,
                'current_weight': mock_history[-1]['weight'],
                'projected_date': goal_date,
                'days_remaining': len([p for p in predictions['predictions'] if p['date'] <= goal_date]),
                'achievable': True,
                'confidence': predictions['confidence_score']
            }
        else:
            return {
                'goal_weight': goal_weight,
                'current_weight': mock_history[-1]['weight'],
                'projected_date': None,
                'achievable': False,
                'message': 'Goal not reached in 30-day forecast. Adjust diet/activity or extend timeline.'
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Goal projection failed: {str(e)}")


@router.get("/models/status")
async def get_forecast_models_status():
    """
    Check time-series model availability
    """
    try:
        import torch
        TORCH_AVAILABLE = True
    except:
        TORCH_AVAILABLE = False
    
    try:
        from prophet import Prophet
        PROPHET_AVAILABLE = True
    except:
        PROPHET_AVAILABLE = False
    
    status = {
        'lstm': {
            'available': TORCH_AVAILABLE,
            'status': 'ready' if TORCH_AVAILABLE else 'not_installed',
            'description': 'Weight prediction using LSTM neural networks'
        },
        'prophet': {
            'available': PROPHET_AVAILABLE,
            'status': 'ready' if PROPHET_AVAILABLE else 'not_installed',
            'description': 'Nutrition trend analysis and forecasting'
        }
    }
    
    available_count = sum(1 for model in status.values() if model['available'])
    
    return {
        'models': status,
        'available_count': available_count,
        'total_count': len(status),
        'recommended_setup': 'Install torch and prophet',
        'phase': 3
    }
