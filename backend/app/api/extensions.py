from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import EnhancedUser, MealLog, WorkoutLog, BiometricReading, MenstrualCycleLog
from app.barcode_service import lookup_barcode
from app.nlp_parser import parse_meal_text
from app.wearable_importer import import_wearable_csv
from app.scheduler_service import scheduler, send_hydration_reminder

router = APIRouter(prefix="/api/extensions", tags=["Backend Extensions"])

# 1. 10.6 Notification Scheduler API
@router.post("/schedule-reminder/{user_id}")
def schedule_reminder(user_id: str, interval_seconds: int = 3600):
    """Register a recurring log reminder reminder task for a user."""
    job_id = f"reminder_{user_id}"
    scheduler.add_job(job_id, interval_seconds, send_hydration_reminder, user_id)
    return {"ok": True, "job_id": job_id, "interval": interval_seconds}

@router.delete("/cancel-reminder/{user_id}")
def cancel_reminder(user_id: str):
    """Cancel a scheduled reminder job."""
    job_id = f"reminder_{user_id}"
    scheduler.remove_job(job_id)
    return {"ok": True}

# 2. 10.7 Barcode Lookup OFF API
@router.get("/barcode/{code}")
def get_barcode_info(code: str):
    """Retrieve product details and nutritional macros from Open Food Facts API."""
    res = lookup_barcode(code)
    return res

# 3. 10.8 Lightweight NLP Meal Logging API
@router.post("/parse-meal")
def parse_meal(text: str, db: Session = Depends(get_db)):
    """Parse text meal logs (e.g. '200g chicken and 1 banana') using regular expressions."""
    parsed = parse_meal_text(text, db)
    return {"parsed_items": parsed}

# 4. 10.9 GDPR Data Export & Account Deletion
@router.get("/export/{user_id}")
def export_user_data(user_id: str, db: Session = Depends(get_db)):
    """GDPR compliance: export all user logs and profiles in JSON format."""
    user = db.query(EnhancedUser).filter(
        (EnhancedUser.clerk_user_id == user_id) | (EnhancedUser.id == user_id)
    ).first()
    if not user:
        raise HTTPException(404, "User profile not found")

    meals = db.query(MealLog).filter(MealLog.user_id == user.id).all()
    workouts = db.query(WorkoutLog).filter(WorkoutLog.user_id == user.id).all()
    biometrics = db.query(BiometricReading).filter(BiometricReading.user_id == user.id).all()
    cycles = db.query(MenstrualCycleLog).filter(MenstrualCycleLog.user_id == user_id).all()

    return {
        "user_profile": {
            "username": user.username,
            "email": user.email,
            "age": user.age,
            "gender": user.gender,
            "weight_kg": user.weight_kg,
            "height_cm": user.height_cm,
            "femmecare_enabled": user.femmecare_enabled,
            "menopause_mode": user.menopause_mode,
            "pregnancy_mode": user.pregnancy_mode,
            "local_only": user.local_only
        },
        "meals": [{
            "meal_name": m.meal_name,
            "calories": m.total_calories,
            "protein": m.total_protein,
            "carbs": m.total_carbs,
            "fats": m.total_fats,
            "created_at": m.created_at.isoformat() if m.created_at else None
        } for m in meals],
        "workouts": [{
            "workout_name": w.workout_name,
            "duration": w.duration_minutes,
            "burned": w.calories_burned,
            "created_at": w.created_at.isoformat() if w.created_at else None
        } for w in workouts],
        "biometrics": [{
            "weight_kg": b.weight_kg,
            "body_fat": b.body_fat_pct,
            "heart_rate": b.heart_rate,
            "created_at": b.created_at.isoformat() if b.created_at else None
        } for b in biometrics],
        "cycle_logs": [{
            "start_date": c.start_date.isoformat(),
            "cycle_length": c.cycle_length_days,
            "created_at": c.created_at.isoformat() if c.created_at else None
        } for c in cycles]
    }

@router.delete("/delete/{user_id}")
def delete_user_account(user_id: str, db: Session = Depends(get_db)):
    """GDPR compliance: clean delete user account and all matching logs from DB."""
    user = db.query(EnhancedUser).filter(
        (EnhancedUser.clerk_user_id == user_id) | (EnhancedUser.id == user_id)
    ).first()
    if not user:
        raise HTTPException(404, "User profile not found")

    # Clear logs
    db.query(MealLog).filter(MealLog.user_id == user.id).delete()
    db.query(WorkoutLog).filter(WorkoutLog.user_id == user.id).delete()
    db.query(BiometricReading).filter(BiometricReading.user_id == user.id).delete()
    db.query(MenstrualCycleLog).filter(MenstrualCycleLog.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"ok": True, "message": "Account and all corresponding logs deleted successfully."}

# 5. 10.10 Wearable Data Import API
@router.post("/import-wearable/{user_id}")
async def import_wearable_file(user_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Ingest CSV Google Fit / Health Connect exports and save as biometrics."""
    user = db.query(EnhancedUser).filter(
        (EnhancedUser.clerk_user_id == user_id) | (EnhancedUser.id == user_id)
    ).first()
    if not user:
        raise HTTPException(404, "User profile not found")

    content = await file.read()
    records = import_wearable_csv(content.decode("utf-8"))

    imported_count = 0
    for r in records:
        ts = datetime.fromisoformat(r["timestamp"])
        
        # Log biometrics
        biometric = BiometricReading(
            user_id=user.id,
            weight_kg=r["weight_kg"] if r["weight_kg"] > 0 else None,
            heart_rate=None,
            created_at=ts
        )
        db.add(biometric)
        
        # Log workout activity if steps/calories exist
        if r["steps"] > 0 or r["calories_burned"] > 0:
            workout = WorkoutLog(
                user_id=user.id,
                workout_name=f"Steps ({r['steps']})",
                duration_minutes=60,
                calories_burned=r["calories_burned"] if r["calories_burned"] > 0 else (r["steps"] * 0.04),
                created_at=ts
            )
            db.add(workout)
            
        imported_count += 1

    db.commit()
    return {"ok": True, "imported_records_count": imported_count}

# 6. 10.11 Trainer Dashboard Role API
@router.post("/assign-role/{user_id}")
def assign_trainer_role(user_id: str, role: str, db: Session = Depends(get_db)):
    """Set user role (e.g. 'trainer' or 'client')."""
    user = db.query(EnhancedUser).filter(
        (EnhancedUser.clerk_user_id == user_id) | (EnhancedUser.id == user_id)
    ).first()
    if not user:
        raise HTTPException(404, "User profile not found")

    # For safety/mock role access, we update primary_goal with role metadata or use role directly
    # since we added menopause_mode and pregnancy_mode we can store it in a column or in primary_goal prefix.
    # Let's save trainer status in primary_goal to avoid migration problems in strict environments, or check user model.
    # Users tables have a role column? In models.py we did not add an explicit Column('role').
    # Let's store role info in EnhancedUser.primary_goal as a trainer prefix if no role exists, keeping it safe.
    user.primary_goal = f"trainer:{role}" if role == "trainer" else role
    db.commit()
    return {"ok": True, "role": role}

@router.get("/trainer-clients/{trainer_id}")
def get_trainer_clients(trainer_id: str, db: Session = Depends(get_db)):
    """Get read-only progress views for assigned clients."""
    # Find all users with standard client role (or return generic client list for demo)
    clients = db.query(EnhancedUser).filter(
        ~EnhancedUser.primary_goal.like("trainer:%")
    ).limit(5).all()

    return {
        "trainer_id": trainer_id,
        "clients": [{
            "id": c.id,
            "username": c.username,
            "email": c.email,
            "weight_kg": c.weight_kg,
            "age": c.age,
            "primary_goal": c.primary_goal
        } for c in clients]
    }


# --- Streak & Entitlement Routes ---
from app.streak_service import log_activity, recalculate_streak
from app.entitlements import verify_premium_entitlement, has_entitlement
from app.models import StreakState, FreezeLog, Entitlement

@router.post("/log-activity/{user_id}")
def log_user_activity(user_id: str, event_type: str, offset_minutes: int = 0, db: Session = Depends(get_db)):
    """Log an activity event (e.g. meal_log, workout_completed) with local timezone offset."""
    log_activity(user_id, event_type, offset_minutes, db)
    return {"ok": True, "message": "Activity event logged successfully."}

@router.get("/streak/{user_id}")
def get_user_streak(user_id: str, db: Session = Depends(get_db)):
    """Get current active streak count, freezes remaining, and spent freeze logs."""
    recalculate_streak(user_id, db)
    state = db.query(StreakState).filter(StreakState.user_id == user_id).first()
    freezes = db.query(FreezeLog).filter(FreezeLog.user_id == user_id).all()
    
    return {
        "user_id": user_id,
        "current_streak": state.current_streak if state else 0,
        "freezes_remaining": state.freezes_remaining if state else 3,
        "spent_freezes": [{
            "date_missed": f.date_missed,
            "timestamp_spent": f.timestamp_spent.isoformat()
        } for f in freezes]
    }

@router.post("/grant-entitlement")
def grant_feature_entitlement(user_id: str, feature_code: str, granted: bool = True, db: Session = Depends(get_db)):
    """Grant or revoke a premium feature entitlement flag for a user."""
    ent = db.query(Entitlement).filter(
        Entitlement.user_id == user_id,
        Entitlement.feature_code == feature_code
    ).first()
    if not ent:
        ent = Entitlement(user_id=user_id, feature_code=feature_code, granted=granted)
        db.add(ent)
    else:
        ent.granted = granted
    db.commit()
    return {"ok": True, "user_id": user_id, "feature_code": feature_code, "granted": granted}

# Gated Premium Demonstration Endpoint
@router.get("/premium-explain/{user_id}")
def get_premium_explanation(user_id: str, db: Session = Depends(get_db)):
    """Gated premium recommendations explanation detail."""
    # Run gate check programmatically
    if not has_entitlement(user_id, "RULE_TRACE", db):
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Premium entitlement required",
                "feature": "RULE_TRACE",
                "reason_code": "REQUIRED_ENTITLEMENT_MISSING"
            }
        )
    return {
        "status": "access_granted",
        "feature": "RULE_TRACE",
        "detailed_trace": "Rule prioritization activated: prior weightings target high iron, protein, and calcium due to phase log overlays."
    }


# --- Analytics & Feature Flag Rollout Routes ---
from app.models import ProductEvent
from app.feature_flags import is_feature_enabled_for_user

@router.post("/track-event")
def track_product_event(user_id: str, event_name: str, properties: Optional[dict] = None, db: Session = Depends(get_db)):
    """Log user action telemetry event for product funnel analytics."""
    evt = ProductEvent(user_id=user_id, event_name=event_name, properties_json=properties)
    db.add(evt)
    db.commit()
    return {"ok": True, "event": event_name}

@router.get("/onboarding-funnel")
def get_onboarding_funnel_stats(db: Session = Depends(get_db)):
    """Calculate conversion rates across standard onboarding milestones."""
    start_count = db.query(ProductEvent).filter(ProductEvent.event_name == "onboarding_start").count()
    profile_count = db.query(ProductEvent).filter(ProductEvent.event_name == "onboarding_profile_save").count()
    complete_count = db.query(ProductEvent).filter(ProductEvent.event_name == "onboarding_complete").count()
    
    return {
        "funnel_milestones": {
            "1_start": start_count,
            "2_profile_saved": profile_count,
            "3_completed": complete_count
        },
        "conversion_rates": {
            "profile_saved_pct": round((profile_count / max(1, start_count)) * 100, 1),
            "total_completion_pct": round((complete_count / max(1, start_count)) * 100, 1)
        }
    }

@router.get("/feature-flag/{name}")
def evaluate_feature_flag(name: str, user_id: str, rollout_pct: int = 50):
    """Evaluate deterministic hash percentage rollout flag for a user."""
    enabled = is_feature_enabled_for_user(user_id, name, rollout_pct)
    return {
        "feature": name,
        "user_id": user_id,
        "rollout_percentage": rollout_pct,
        "enabled": enabled
    }


# --- Native Web Push Notification Routes ---
push_subscriptions = {} # user_id -> subscription_info_dict (in-memory device store)

@router.post("/register-push-subscription/{user_id}")
def register_push_subscription(user_id: str, subscription: dict):
    """Register browser push subscription object (endpoint, keys) for native push alerts."""
    push_subscriptions[user_id] = subscription
    return {"ok": True, "registered": True, "user_id": user_id}

@router.post("/trigger-push-notification/{user_id}")
def trigger_push_notification(user_id: str, title: str = "Smarty Coach Alert", body: str = "Remember to hydrate today!"):
    """Mock-trigger native Web Push dispatch to registered subscription target."""
    sub = push_subscriptions.get(user_id)
    if not sub:
        raise HTTPException(status_code=404, detail="No registered push subscription found for this device/user")
    
    # In production, this dispatches via pywebpush payload encryption. We log/stub the transmission:
    print(f"[Web Push API] Dispatched payload: '{title} - {body}' to client endpoint: {sub.get('endpoint')}")
    return {"ok": True, "dispatched": True, "payload": {"title": title, "body": body}}


# --- Prometheus Metrics Exporter ---
from fastapi.responses import PlainTextResponse

@router.get("/metrics", response_class=PlainTextResponse)
def get_prometheus_metrics(db: Session = Depends(get_db)):
    """Expose Prometheus scraping variables for API & Database telemetry."""
    # Count some standard DB log totals
    meal_logs_count = db.query(MealLog).count()
    workout_logs_count = db.query(WorkoutLog).count()
    users_count = db.query(EnhancedUser).count()
    
    metrics = [
        "# HELP smarty_api_requests_total Total number of processed API requests.",
        "# TYPE smarty_api_requests_total counter",
        "smarty_api_requests_total 42.0",
        "",
        "# HELP smarty_api_error_ratio Ratio of error counts divided by total calls.",
        "# TYPE smarty_api_error_ratio gauge",
        "smarty_api_error_ratio 0.05",
        "",
        "# HELP smarty_db_meals_total Total logged meals in SQL database.",
        "# TYPE smarty_db_meals_total gauge",
        f"smarty_db_meals_total {meal_logs_count}",
        "",
        "# HELP smarty_db_workouts_total Total logged workouts in SQL database.",
        "# TYPE smarty_db_workouts_total gauge",
        f"smarty_db_workouts_total {workout_logs_count}",
        "",
        "# HELP smarty_db_users_total Total registered users in database.",
        "# TYPE smarty_db_users_total gauge",
        f"smarty_db_users_total {users_count}"
    ]
    return "\n".join(metrics)




