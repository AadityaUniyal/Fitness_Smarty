from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from app.database import get_db
from app import schemas, models
from app.auth import get_current_user

router = APIRouter(prefix="/api/form-coach", tags=["Form Coach"])


@router.get("/sessions", response_model=List[schemas.FormCoachSessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    sessions = db.query(models.FormCoachSession).filter(
        models.FormCoachSession.user_id == current_user.id
    ).order_by(desc(models.FormCoachSession.created_at)).all()
    result = []
    for s in sessions:
        result.append(schemas.FormCoachSessionResponse(
            id=s.id, exercise=s.exercise, duration_seconds=s.duration_seconds,
            rep_count=s.rep_count, feedback_summary=s.feedback_summary,
            feedback_logs=[schemas.FormFeedbackLogResponse(
                id=f.id, message=f.message, feedback_type=f.feedback_type,
                timestamp=f.timestamp,
            ) for f in s.feedback_logs],
            created_at=s.created_at,
        ))
    return result


@router.post("/sessions", response_model=schemas.FormCoachSessionResponse, status_code=201)
def create_session(
    data: schemas.FormCoachSessionCreate,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    session = models.FormCoachSession(
        user_id=current_user.id, exercise=data.exercise,
        duration_seconds=data.duration_seconds, rep_count=data.rep_count,
        feedback_summary=data.feedback_summary,
    )
    db.add(session)
    db.flush()
    for f in data.feedback_logs:
        db.add(models.FormFeedbackLog(
            session_id=session.id, message=f.message, feedback_type=f.feedback_type,
        ))
    db.commit()
    db.refresh(session)
    return schemas.FormCoachSessionResponse(
        id=session.id, exercise=session.exercise,
        duration_seconds=session.duration_seconds, rep_count=session.rep_count,
        feedback_summary=session.feedback_summary,
        feedback_logs=[schemas.FormFeedbackLogResponse(
            id=f.id, message=f.message, feedback_type=f.feedback_type,
            timestamp=f.timestamp,
        ) for f in session.feedback_logs],
        created_at=session.created_at,
    )


@router.get("/sessions/{session_id}", response_model=schemas.FormCoachSessionResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    session = db.query(models.FormCoachSession).filter(
        models.FormCoachSession.id == session_id,
        models.FormCoachSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(404, "Session not found")
    return schemas.FormCoachSessionResponse(
        id=session.id, exercise=session.exercise,
        duration_seconds=session.duration_seconds, rep_count=session.rep_count,
        feedback_summary=session.feedback_summary,
        feedback_logs=[schemas.FormFeedbackLogResponse(
            id=f.id, message=f.message, feedback_type=f.feedback_type,
            timestamp=f.timestamp,
        ) for f in session.feedback_logs],
        created_at=session.created_at,
    )
