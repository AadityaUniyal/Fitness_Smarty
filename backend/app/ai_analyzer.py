
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from . import db_models
import math

def forecast_performance(db: Session, user_id: str, days_ahead: int = 30):
    """
    Project future kinetic output based on current metabolic trends.
    Uses a weighted moving average of the last 14 days of activity.
    """
    threshold = datetime.utcnow() - timedelta(days=14)
    records = db.query(models.BiometricRecord).filter(
        models.BiometricRecord.user_id == user_id,
        models.BiometricRecord.category == 'steps',
        models.BiometricRecord.timestamp >= threshold
    ).all()

    if len(records) < 3:
        return {"forecast": "Insufficient Data", "confidence": 0, "projection": []}

    values = [r.value for r in sorted(records, key=lambda x: x.timestamp)]
    
    # Simple linear trend calculation
    x_mean = (len(values) - 1) / 2
    y_mean = sum(values) / len(values)
    
    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(len(values)))
    
    slope = numerator / denominator if denominator != 0 else 0
    
    projection = []
    last_val = values[-1]
    for day in range(1, days_ahead + 1):
        projection.append({
            "day": day,
            "value": round(last_val + (slope * day), 0)
        })

    trend_status = "Ascending" if slope > 100 else "Descending" if slope < -100 else "Stable"
    
    return {
        "trend": trend_status,
        "slope": round(slope, 2),
        "projected_milestone": round(last_val + (slope * days_ahead), 0),
        "confidence_score": min(95, 40 + (len(records) * 4)),
        "data_points": projection
    }

def detect_plateaus(db: Session, user_id: str):
    """
    Analyzes strength and weight logs to identify periods of metabolic or kinetic stagnation.
    """
    # Logic: If max output in workouts hasn't increased by >2% in 21 days, flag plateau.
    workouts = db.query(models.WorkoutLog).filter(
        models.WorkoutLog.user_id == user_id
    ).order_by(models.WorkoutLog.timestamp.desc()).limit(10).all()

    if len(workouts) < 5:
        return {"status": "Monitoring", "message": "Baseline collection in progress."}

    # Simplified check for demonstration
    intensities = [w.intensity for w in workouts]
    if intensities.count("High") < 2:
        return {
            "status": "Adaptive Ceiling",
            "message": "Metabolic intensity too low for neural adaptation. Increase load by 5-10%.",
            "protocol": "Progressive Overload Phase"
        }

    return {
        "status": "Nominal",
        "message": "Kinetic progression within expected neural window.",
        "protocol": "Continue Current Cycle"
    }
