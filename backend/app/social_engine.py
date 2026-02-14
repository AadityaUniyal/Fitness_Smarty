
from sqlalchemy import func
from sqlalchemy.orm import Session
from . import db_models

def get_peer_benchmarks(db: Session, user_id: str):
    """
    Aggregates global metrics to provide peer-group percentiles.
    """
    # In a real app, this would be cached/pre-aggregated
    avg_steps = db.query(func.avg(models.BiometricRecord.value)).filter(
        models.BiometricRecord.category == 'steps'
    ).scalar() or 8000
    
    user_avg_steps = db.query(func.avg(models.BiometricRecord.value)).filter(
        models.BiometricRecord.user_id == user_id,
        models.BiometricRecord.category == 'steps'
    ).scalar() or 0
    
    percentile = (user_avg_steps / (avg_steps * 1.5)) * 100
    
    rank_title = "Apex Operator" if percentile > 90 else "Neural Vanguard" if percentile > 70 else "Active Node"
    
    return {
        "global_average_steps": round(avg_steps, 0),
        "your_average_steps": round(user_avg_steps, 0),
        "percentile_rank": min(99, round(percentile, 1)),
        "rank_title": rank_title,
        "community_status": f"Performing better than {round(percentile, 1)}% of your neural peer group."
    }
