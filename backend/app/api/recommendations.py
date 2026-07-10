from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas, models
from app.recommendation_engine import RecommendationEngine, RecommendationRequest
from app import ai_analyzer, sleep_optimization, recovery_engine, hydration_monitor
from app.clerk_auth import get_current_user_id_from_clerk as get_current_user_id

router = APIRouter(prefix="/api/recommendations", tags=["Smart Recommendations & AI"])

@router.get("/forecast", response_model=schemas.ForecastResponse)
def get_performance_forecast(
    db: Session = Depends(get_db), 
    user_id: str = Depends(get_current_user_id)
):
    """Predict future performance trends"""
    return ai_analyzer.forecast_performance(db, user_id)

@router.get("/plateau-status")
def check_for_plateaus(
    db: Session = Depends(get_db), 
    user_id: str = Depends(get_current_user_id)
):
    """Analyze historical progression for stagnation markers"""
    return ai_analyzer.detect_plateaus(db, user_id)

@router.get("/sleep-protocol", response_model=schemas.SleepProtocolResponse)
def get_sleep_bio_protocol(
    db: Session = Depends(get_db), 
    user_id: str = "demo_user"
):
    """Retrieve recovery protocols based on sleep quality"""
    return sleep_optimization.get_recovery_protocol(strain_score=72.5, sleep_quality=58.0)

@router.get("/recovery")
def get_recovery_diagnostics(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Fetch AI-computed recovery score"""
    return recovery_engine.calculate_recovery_score(db, user_id)

@router.get("/hydration")
def get_hydration_protocol(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Calculate personalized fluid requirements"""
    user = db.query(models.EnhancedUser).filter(models.EnhancedUser.id == user_id).first()
    return hydration_monitor.get_hydration_requirement(user, activity_minutes=84)

@router.get("/user/{user_id}", response_model=schemas.RecommendationListResponse)
def get_user_recommendations(
    user_id: str,
    include_read: bool = Query(False),
    limit: int = Query(20),
    db: Session = Depends(get_db)
):
    """Get personalized recommendations"""
    engine = RecommendationEngine(db)
    recommendations = engine.get_user_recommendations(user_id=user_id, include_read=include_read, limit=limit)
    
    formatted_recs = []
    for rec in recommendations:
        formatted_recs.append({
            "id": str(rec.id),
            "recommendation_type": rec.recommendation_type,
            "title": rec.title,
            "description": rec.description,
            "confidence_score": rec.confidence_score,
            "is_read": rec.is_read,
            "created_at": rec.created_at.isoformat() if rec.created_at else None,
            "expires_at": rec.expires_at.isoformat() if rec.expires_at else None
        })
    return {
        "recommendations": formatted_recs,
        "total_count": len(formatted_recs),
        "unread_count": sum(1 for rec in recommendations if not rec.is_read)
    }

@router.post("/generate/{user_id}")
def generate_recommendations(user_id: str, db: Session = Depends(get_db)):
    """Generate new personalized recommendations"""
    engine = RecommendationEngine(db)
    try:
        request = RecommendationRequest(user_id=user_id)
        result = engine.generate_recommendations(request)
        return {"message": "Generated", "counts": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# FemmeCare
@router.get("/femmecare/daily-advice")
async def get_femmecare_advice(user_id: str, db: Session = Depends(get_db)):
    """Get cycle-synced advice"""
    log = db.query(models.MenstrualCycleLog).filter(
        models.MenstrualCycleLog.user_id == user_id
    ).order_by(models.MenstrualCycleLog.start_date.desc()).first()
    
    engine = RecommendationEngine(db=db)
    
    # Decrypt symptoms
    latest_symptoms = []
    if log:
        if log.encrypted_symptoms:
            try:
                from app.security_encryption import decrypt_value
                dec = decrypt_value(log.encrypted_symptoms)
                latest_symptoms = dec.split(",") if dec else []
            except Exception:
                latest_symptoms = log.symptoms or []
        else:
            latest_symptoms = log.symptoms or []

    if not log:
        return engine.get_cycle_sync_advice(None, user_id=user_id, symptoms=latest_symptoms)
    return engine.get_cycle_sync_advice(log.start_date, log.cycle_length_days, user_id=user_id, symptoms=latest_symptoms)

