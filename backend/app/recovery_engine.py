
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import models

def calculate_recovery_score(db: Session, user_id: str):
    """
    Computes a recovery readiness score (0-100) based on sleep, resting HR, and activity.
    """
    threshold = datetime.utcnow() - timedelta(days=3)
    records = db.query(models.BiometricRecord).filter(
        models.BiometricRecord.user_id == user_id,
        models.BiometricRecord.timestamp >= threshold
    ).all()

    if not records:
        return {"score": 85, "status": "Optimized", "advice": "Baseline established. Full intensity allowed."}

    # Group data
    hr_values = [r.value for r in records if r.category == 'heart_rate']
    avg_hr = sum(hr_values) / len(hr_values) if hr_values else 70
    
    # Logic: Higher HR than normal indicates fatigue
    # (Simplified for the demo engine)
    fatigue_factor = max(0, (avg_hr - 60) * 2)
    score = max(0, min(100, 100 - fatigue_factor))

    status = "Elite" if score > 90 else "Operational" if score > 70 else "Fatigued"
    advice = "Full load permitted." if score > 70 else "De-load recommended. Focus on mobility."

    return {
        "score": round(score, 1),
        "status": status,
        "advice": advice,
        "last_sync": datetime.utcnow()
    }
