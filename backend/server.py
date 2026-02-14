
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from app import EnhancedUser, MealLog, WorkoutLog, BiometricReading
from app import schemas, database, ai_analyzer
import random
from datetime import datetime, timedelta

app = FastAPI(title="Smarty AI Neural Infrastructure")

# Enable CORS for frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
models.Base.metadata.create_all(bind=database.engine)

# --- USER DEPARTMENT ---

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user_profile(user_id: str, db: Session = Depends(database.get_db)):
    user = db.query(EnhancedUser).filter(EnhancedUser.id == user_id).first()
    if not user:
        # Initial user provisioning
        user = EnhancedUser(
            id=user_id, 
            username=f"operator_{user_id}", 
            email=f"{user_id}@smarty.com",
            weight_kg=80.0, 
            height_cm=180.0, 
            primary_goal="Athletic"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Computed metrics (would normally involve complex SQL aggregates)
    return {
        **user.__dict__,
        "daily_calories": 2450,
        "daily_steps": 12402,
        "active_minutes": 84,
        "heart_rate": 72
    }

# --- BIOMETRICS & ANALYTICS DEPARTMENT ---

@app.post("/log/biometric")
def log_biometric(entry: schemas.BiometricCreate, user_id: str = "user-1", db: Session = Depends(database.get_db)):
    new_record = BiometricRecord(
        user_id=user_id,
        category=entry.category,
        value=entry.value
    )
    db.add(new_record)
    db.commit()
    return {"status": "synchronized", "timestamp": datetime.utcnow()}

@app.post("/log/fault")
def log_biomechanical_event(entry: schemas.FaultCreate, user_id: str = "user-1", db: Session = Depends(database.get_db)):
    new_record = BiomechanicalFault(
        user_id=user_id,
        part=entry.part,
        status=entry.status,
        feedback=entry.feedback
    )
    db.add(new_record)
    db.commit()
    return {"status": "node_synced"}

@app.get("/neural/integrity")
def get_neural_integrity(user_id: str = "user-1", db: Session = Depends(database.get_db)):
    """Computes high-level biomechanical integrity based on recent faults."""
    recent_faults = db.query(BiomechanicalFault).filter(
        BiomechanicalFault.user_id == user_id
    ).order_by(models.BiomechanicalFault.timestamp.desc()).limit(20).all()
    
    if not recent_faults:
        return {"integrity_score": 100, "status": "NOMINAL", "directive": "System synchronized. No kinetic faults detected."}
    
    # Weighting logic
    scores = {"optimal": 100, "warning": 70, "critical": 30}
    avg_score = sum(scores.get(f.status, 100) for f in recent_faults) / len(recent_faults)
    
    # Find most common fault area
    parts = [f.part for f in recent_faults if f.status != 'optimal']
    most_common = max(set(parts), key=parts.count) if parts else "N/A"
    
    directive = "Focus on stabilizing the " + most_common + " during metabolic load." if most_common != "N/A" else "System stable."
    
    return {
        "integrity_score": round(avg_score, 1),
        "status": "VULNERABLE" if avg_score < 75 else "STABLE",
        "focus_area": most_common,
        "directive": directive,
        "fault_history": recent_faults[:5]
    }

@app.get("/analytics/{user_id}", response_model=schemas.AnalyticsReport)
def get_neural_analytics(
    user_id: str, 
    category: str = "steps", 
    days: int = Query(14, description="Number of days to retrieve"),
    db: Session = Depends(database.get_db)
):
    # Calculate time threshold
    threshold = datetime.utcnow() - timedelta(days=days)
    
    # Fetch filtered history
    query = db.query(BiometricRecord).filter(
        BiometricRecord.user_id == user_id,
        BiometricRecord.category == category
    )
    
    if days > 0:
        query = query.filter(BiometricRecord.timestamp >= threshold)
        
    logs = query.order_by(models.BiometricRecord.timestamp.desc()).all()
    
    if not logs:
        # Generate algorithmic mock data for visual consistency if no real data exists
        now = datetime.now()
        limit = days if days > 0 else 30
        logs = [
            BiometricRecord(
                timestamp=now - timedelta(days=i),
                value=8000 + random.randint(0, 5000) if category == "steps" else 75 + random.uniform(-2, 2),
                category=category
            ) for i in range(limit)
        ]

    values = [log.value for log in logs]
    avg = sum(values) / len(values) if values else 0
    trend = "ASCENDING" if len(values) > 1 and values[0] > values[-1] else "STABLE"
    
    return {
        "category": category,
        "average": avg,
        "trend": trend,
        "data_points": sorted(logs, key=lambda x: x.timestamp)
    }

# --- NUTRITION DEPARTMENT ---

@app.post("/log/meal")
def log_meal(meal: schemas.MealCreate, user_id: str = "user-1", db: Session = Depends(database.get_db)):
    db_meal = MealLog(user_id=user_id, **meal.dict())
    db.add(db_meal)
    db.commit()
    return {"status": "logged", "meal": meal.food_name}

@app.get("/nutrition/summary/{user_id}")
def get_daily_biofuel(user_id: str, db: Session = Depends(database.get_db)):
    today = datetime.utcnow().date()
    meals = db.query(MealLog).filter(
        MealLog.user_id == user_id,
        MealLog.timestamp >= today
    ).all()
    
    return {
        "total_calories": sum(m.calories for m in meals),
        "protein": sum(m.protein for m in meals),
        "carbs": sum(m.carbs for m in meals),
        "fats": sum(m.fats for m in meals),
        "count": len(meals)
    }

# --- MEAL ANALYSIS AND TRACKING ENDPOINTS ---

@app.get("/meals/{meal_log_id}")
def get_meal_log(meal_log_id: str, db: Session = Depends(database.get_db)):
    """
    Retrieve a specific meal log with all components
    """
    from app.meal_analysis_service import MealAnalysisService
    
    service = MealAnalysisService(db)
    meal_log = service.get_meal_log(meal_log_id)
    
    if not meal_log:
        raise HTTPException(status_code=404, detail="Meal log not found")
    
    return meal_log

@app.get("/meals/user/{user_id}/history")
def get_meal_history(
    user_id: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    meal_type: Optional[str] = Query(None, description="Filter by meal type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(database.get_db)
):
    """
    Get historical meal logs for a user with filtering and pagination
    """
    from app.meal_analysis_service import MealAnalysisService
    
    # Parse dates if provided
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
    
    service = MealAnalysisService(db)
    history = service.get_user_meal_history(
        user_id=user_id,
        start_date=start_dt,
        end_date=end_dt,
        meal_type=meal_type,
        limit=limit,
        offset=offset
    )
    
    return history

@app.get("/meals/user/{user_id}/daily-summary")
def get_daily_summary(
    user_id: str,
    date: Optional[str] = Query(None, description="Date (ISO format, defaults to today)"),
    db: Session = Depends(database.get_db)
):
    """
    Get nutrition summary for a specific day
    """
    from app.meal_analysis_service import MealAnalysisService
    
    # Parse date if provided
    target_date = None
    if date:
        try:
            target_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
    
    service = MealAnalysisService(db)
    summary = service.get_daily_nutrition_summary(user_id=user_id, date=target_date)
    
    return summary

@app.get("/meals/user/{user_id}/trends")
def get_nutrition_trends(
    user_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(database.get_db)
):
    """
    Get nutrition trends over a period of days
    """
    from app.meal_analysis_service import MealAnalysisService
    
    service = MealAnalysisService(db)
    trends = service.get_nutrition_trends(user_id=user_id, days=days)
    
    return trends

# --- WORKOUT DEPARTMENT ---

@app.post("/log/workout")
def save_workout_plan(plan: dict, user_id: str = "user-1", db: Session = Depends(database.get_db)):
    # Persist AI-generated training nodes
    db_workout = WorkoutLog(
        user_id=user_id,
        plan_data=plan,
        intensity=plan.get("intensity", "Medium"),
        duration=int(plan.get("duration", "45").split()[0])
    )
    db.add(db_workout)
    db.commit()
    return {"status": "plan_archived"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
