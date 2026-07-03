from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import ActivityEvent, StreakState, FreezeLog

def log_activity(user_id: str, event_type: str, offset_minutes: int, db: Session):
    """
    Log a daily action event (e.g. meal_log, workout_completed) 
    and re-evaluate the user's logging streak.
    """
    event = ActivityEvent(
        user_id=user_id,
        event_type=event_type,
        local_timestamp=datetime.utcnow(),
        timezone_offset_minutes=offset_minutes
    )
    db.add(event)
    db.commit()
    
    # Recalculate streak
    recalculate_streak(user_id, db)

def recalculate_streak(user_id: str, db: Session) -> int:
    """
    Computes streak from timezone-adjusted activity logs.
    Saves streak length to StreakState and consumes freeze tokens if a day is missed.
    """
    events = db.query(ActivityEvent).filter(ActivityEvent.user_id == user_id).order_by(ActivityEvent.local_timestamp.asc()).all()
    
    # Calculate dates adjusted to local timezone
    local_dates = set()
    for e in events:
        local_time = e.local_timestamp + timedelta(minutes=e.timezone_offset_minutes)
        local_dates.add(local_time.date())
        
    if not local_dates:
        return 0
        
    sorted_dates = sorted(list(local_dates))
    
    # Fetch/create state
    state = db.query(StreakState).filter(StreakState.user_id == user_id).first()
    if not state:
        state = StreakState(user_id=user_id, current_streak=0, freezes_remaining=3)
        db.add(state)
        
    # Analyze day gaps
    current_streak = 0
    start_idx = 0
    
    # Event-sourced loop checking each consecutive day
    idx = 0
    freezes = state.freezes_remaining
    
    while idx < len(sorted_dates):
        if idx == 0:
            current_streak = 1
            idx += 1
            continue
            
        prev_date = sorted_dates[idx-1]
        curr_date = sorted_dates[idx]
        delta = (curr_date - prev_date).days
        
        if delta == 1:
            current_streak += 1
        elif delta > 1:
            # Check if we can spend freezes to patch the gap days
            gap_days = delta - 1
            if freezes >= gap_days:
                # Spend freezes
                for offset in range(1, gap_days + 1):
                    missed_day = prev_date + timedelta(days=offset)
                    # Log spent freeze
                    freeze_log = FreezeLog(
                        user_id=user_id,
                        date_missed=missed_day.isoformat()
                    )
                    db.add(freeze_log)
                freezes -= gap_days
                current_streak += delta
            else:
                # Break streak
                current_streak = 1
                
        idx += 1

    # Check if the streak has already expired today (i.e. last active day is older than yesterday)
    if sorted_dates:
        today_local = (datetime.utcnow() + timedelta(minutes=events[-1].timezone_offset_minutes)).date()
        days_since_last_activity = (today_local - sorted_dates[-1]).days
        if days_since_last_activity > 1:
            # We missed yesterday or older. Check freeze fallback.
            if freezes > 0:
                freeze_log = FreezeLog(
                    user_id=user_id,
                    date_missed=(sorted_dates[-1] + timedelta(days=1)).isoformat()
                )
                db.add(freeze_log)
                freezes -= 1
            else:
                current_streak = 0

    state.current_streak = current_streak
    state.freezes_remaining = freezes
    state.last_computed_at = datetime.utcnow()
    db.commit()
    return current_streak
