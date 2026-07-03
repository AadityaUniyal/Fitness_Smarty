from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from app.database import get_db
from app.models import MenstrualCycleLog, EnhancedUser
from app.security_encryption import encrypt_value, decrypt_value
from app.recommendation_engine import RecommendationEngine

router = APIRouter(prefix="/api/female", tags=["Female Health"])

@router.get("/cycle-phase/{user_id}")
def get_cycle_phase(user_id: str, db: Session = Depends(get_db)):
    """Fetch current cycle details, phase advice, and statistics."""
    # Find user
    user = db.query(EnhancedUser).filter(
        (EnhancedUser.clerk_user_id == user_id) | (EnhancedUser.id == user_id)
    ).first()
    if not user:
        raise HTTPException(404, "User not found")

    # Get latest cycle log
    latest = db.query(MenstrualCycleLog).filter(
        MenstrualCycleLog.user_id == user_id
    ).order_by(MenstrualCycleLog.start_date.desc()).first()

    rec_engine = RecommendationEngine(db=db)
    
    # Defaults
    last_start = datetime.utcnow()
    cycle_len = 28
    latest_symptoms = []
    
    if latest:
        last_start = latest.start_date
        cycle_len = latest.cycle_length_days or 28
        
        # Decrypt symptoms
        if latest.encrypted_symptoms:
            try:
                dec = decrypt_value(latest.encrypted_symptoms)
                latest_symptoms = dec.split(",") if dec else []
            except Exception:
                latest_symptoms = latest.symptoms or []
        else:
            latest_symptoms = latest.symptoms or []

    # Let the recommendation engine determine phase details, adaptive rollings, etc.
    advice_payload = rec_engine.get_cycle_sync_advice(
        last_start, 
        cycle_length=cycle_len, 
        user_id=user_id, 
        symptoms=latest_symptoms
    )
    
    # Calculate cycle day
    if latest:
        cycle_day = (datetime.utcnow() - latest.start_date).days % advice_payload["learned_cycle_length"] + 1
    else:
        cycle_day = 0

    return {
        "phase": advice_payload["phase"],
        "advice": advice_payload["advice"],
        "cycle_day": cycle_day,
        "learned_cycle_length": advice_payload["learned_cycle_length"],
        "anomaly_warning": advice_payload["anomaly_warning"],
        "cycle_history_stats": advice_payload["cycle_history_stats"],
        "recommended_exercises": advice_payload["recommended_exercises"],
        "user_profile": advice_payload["user_profile"]
    }

@router.post("/log-period/{user_id}")
def log_period(
    user_id: str, 
    start_date: str, 
    symptoms: Optional[List[str]] = None, 
    mood: Optional[str] = None, 
    flow_intensity: Optional[str] = None, 
    notes: Optional[str] = None,
    cycle_length_days: Optional[int] = 28,
    db: Session = Depends(get_db)
):
    """Log a cycle start date with optional symptoms, utilizing application-layer encryption."""
    user = db.query(EnhancedUser).filter(
        (EnhancedUser.clerk_user_id == user_id) | (EnhancedUser.id == user_id)
    ).first()
    if not user:
        raise HTTPException(404, "User not found")

    parsed_date = datetime.fromisoformat(start_date.replace("Z", "+00:00")).replace(tzinfo=None)
    
    # Check if local-only is enabled or requested
    if user.local_only:
        return {"ok": True, "message": "Saved locally only (local_only is enabled). Data was not synced to database."}

    # Encrypt the sensitive fields
    symptoms_str = ",".join(symptoms) if symptoms else ""
    enc_symptoms = encrypt_value(symptoms_str)
    enc_mood = encrypt_value(mood or "")
    enc_flow = encrypt_value(flow_intensity or "")
    enc_notes = encrypt_value(notes or "")

    # Store clear text fields as placeholders/stripped or empty to guarantee DB logs can only be read with decryption key
    entry = MenstrualCycleLog(
        user_id=user_id,
        start_date=parsed_date,
        cycle_length_days=cycle_length_days or 28,
        symptoms=[], # empty/placeholder
        mood="[ENCRYPTED]",
        flow_intensity="[ENCRYPTED]",
        notes="[ENCRYPTED]",
        encrypted_symptoms=enc_symptoms,
        encrypted_mood=enc_mood,
        encrypted_flow_intensity=enc_flow,
        encrypted_notes=enc_notes
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"ok": True, "log_id": entry.id}

@router.post("/update-settings/{user_id}")
def update_female_settings(
    user_id: str,
    femmecare_enabled: Optional[bool] = None,
    menopause_mode: Optional[bool] = None,
    pregnancy_mode: Optional[bool] = None,
    local_only: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Update general FemmeCare profile toggles (menopause, pregnancy, and local-only)."""
    user = db.query(EnhancedUser).filter(
        (EnhancedUser.clerk_user_id == user_id) | (EnhancedUser.id == user_id)
    ).first()
    if not user:
        raise HTTPException(404, "User not found")

    if femmecare_enabled is not None:
        user.femmecare_enabled = femmecare_enabled
    if menopause_mode is not None:
        user.menopause_mode = menopause_mode
    if pregnancy_mode is not None:
        user.pregnancy_mode = pregnancy_mode
    if local_only is not None:
        user.local_only = local_only

    db.commit()
    return {"ok": True, "settings": {
        "femmecare_enabled": user.femmecare_enabled,
        "menopause_mode": user.menopause_mode,
        "pregnancy_mode": user.pregnancy_mode,
        "local_only": user.local_only
    }}

@router.get("/calendar-feed/{user_id}")
def get_ical_calendar_feed(user_id: str, db: Session = Depends(get_db)):
    """Generates a standard iCal (.ics) feed of cycle phases to sync with Google Calendar."""
    from fastapi.responses import Response
    from datetime import timedelta
    
    user = db.query(EnhancedUser).filter(
        (EnhancedUser.clerk_user_id == user_id) | (EnhancedUser.id == user_id)
    ).first()
    if not user:
        raise HTTPException(404, "User not found")
        
    latest = db.query(MenstrualCycleLog).filter(
        MenstrualCycleLog.user_id == user_id
    ).order_by(MenstrualCycleLog.start_date.desc()).first()
    
    start_date = latest.start_date if latest else datetime.utcnow()
    cycle_len = latest.cycle_length_days if (latest and latest.cycle_length_days) else 28
    
    # Define phase shifts (offsets in days from start of cycle)
    # Menstrual: Days 1-5 (offset 0)
    # Follicular: Days 6-12 (offset 5)
    # Ovulatory: Days 13-16 (offset 12)
    # Luteal: Days 17-28 (offset 16)
    phases = [
        {"name": "Menstrual Phase (Restorative Yoga / Gentle Walk)", "start_offset": 0, "duration": 5, "desc": "Estrogen & Progesterone low. Focus on recovery and light movement."},
        {"name": "Follicular Phase (Progressive Overload / Pilates Core)", "start_offset": 5, "duration": 7, "desc": "Energy rising. Great time to push limits and build strength."},
        {"name": "Ovulatory Phase (Peak HIIT / Barbell Squats)", "start_offset": 12, "duration": 4, "desc": "Testosterone & Estrogen peak. Energy and confidence are highest!"},
        {"name": "Luteal Phase (Steady Jogging / Arm Sculpting)", "start_offset": 16, "duration": cycle_len - 16, "desc": "Progesterone peaks. Body temperature is higher, focus on steady cardio."}
    ]
    
    ical_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Smarty AI//FemmeCare Calendar Sync//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    # Generate calendar events for 3 future cycles
    for cycle_idx in range(3):
        cycle_start = start_date + timedelta(days=cycle_idx * cycle_len)
        for phase in phases:
            phase_start = cycle_start + timedelta(days=phase["start_offset"])
            phase_end = phase_start + timedelta(days=phase["duration"])
            
            event_id = f"smarty_cycle_{user_id}_{cycle_idx}_{phase['start_offset']}"
            dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            dtstart = phase_start.strftime("%Y%m%d")
            dtend = phase_end.strftime("%Y%m%d")
            
            ical_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{event_id}",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART;VALUE=DATE:{dtstart}",
                f"DTEND;VALUE=DATE:{dtend}",
                f"SUMMARY:🌸 {phase['name']}",
                f"DESCRIPTION:{phase['desc']}",
                "STATUS:CONFIRMED",
                "SEQUENCE:0",
                "END:VEVENT"
            ])
            
    ical_lines.append("END:VCALENDAR")
    ical_content = "\r\n".join(ical_lines)
    
    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=smarty_cycle_feed_{user_id}.ics",
            "Cache-Control": "no-cache"
        }
    )


