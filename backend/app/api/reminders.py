from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from app.database import get_db
from app import schemas, models
from app.auth import get_current_user

router = APIRouter(prefix="/api/reminders", tags=["Reminders & Notifications"])


@router.get("/reminders", response_model=List[schemas.ReminderResponse])
def list_reminders(
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    reminders = db.query(models.Reminder).filter(
        models.Reminder.user_id == current_user.id
    ).order_by(models.Reminder.time).all()
    return [schemas.ReminderResponse(
        id=r.id, label=r.label, description=r.description,
        time=r.time, days=r.days, enabled=r.enabled, icon=r.icon,
        created_at=r.created_at, updated_at=r.updated_at,
    ) for r in reminders]


@router.post("/reminders", response_model=schemas.ReminderResponse, status_code=201)
def create_reminder(
    data: schemas.ReminderCreate,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    reminder = models.Reminder(
        user_id=current_user.id, label=data.label, description=data.description,
        time=data.time, days=data.days, enabled=data.enabled, icon=data.icon,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return schemas.ReminderResponse(
        id=reminder.id, label=reminder.label, description=reminder.description,
        time=reminder.time, days=reminder.days, enabled=reminder.enabled,
        icon=reminder.icon, created_at=reminder.created_at, updated_at=reminder.updated_at,
    )


@router.put("/reminders/{reminder_id}", response_model=schemas.ReminderResponse)
def update_reminder(
    reminder_id: int,
    data: schemas.ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    reminder = db.query(models.Reminder).filter(
        models.Reminder.id == reminder_id,
        models.Reminder.user_id == current_user.id,
    ).first()
    if not reminder:
        raise HTTPException(404, "Reminder not found")
    if data.label is not None: reminder.label = data.label
    if data.description is not None: reminder.description = data.description
    if data.time is not None: reminder.time = data.time
    if data.days is not None: reminder.days = data.days
    if data.enabled is not None: reminder.enabled = data.enabled
    if data.icon is not None: reminder.icon = data.icon
    db.commit()
    db.refresh(reminder)
    return schemas.ReminderResponse(
        id=reminder.id, label=reminder.label, description=reminder.description,
        time=reminder.time, days=reminder.days, enabled=reminder.enabled,
        icon=reminder.icon, created_at=reminder.created_at, updated_at=reminder.updated_at,
    )


@router.delete("/reminders/{reminder_id}", status_code=204)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    reminder = db.query(models.Reminder).filter(
        models.Reminder.id == reminder_id,
        models.Reminder.user_id == current_user.id,
    ).first()
    if not reminder:
        raise HTTPException(404, "Reminder not found")
    db.delete(reminder)
    db.commit()


@router.get("/notifications", response_model=List[schemas.NotificationLogResponse])
def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    query = db.query(models.NotificationLog).filter(
        models.NotificationLog.user_id == current_user.id,
    )
    if unread_only:
        query = query.filter(models.NotificationLog.read == False)
    notifications = query.order_by(desc(models.NotificationLog.created_at)).limit(limit).all()
    return [schemas.NotificationLogResponse(
        id=n.id, title=n.title, body=n.body, icon=n.icon,
        source=n.source, read=n.read, created_at=n.created_at,
    ) for n in notifications]


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    notif = db.query(models.NotificationLog).filter(
        models.NotificationLog.id == notification_id,
        models.NotificationLog.user_id == current_user.id,
    ).first()
    if not notif:
        raise HTTPException(404, "Notification not found")
    notif.read = True
    db.commit()
    return {"read": True}


@router.post("/notifications/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    db.query(models.NotificationLog).filter(
        models.NotificationLog.user_id == current_user.id,
        models.NotificationLog.read == False,
    ).update({"read": True})
    db.commit()
    return {"read_all": True}
