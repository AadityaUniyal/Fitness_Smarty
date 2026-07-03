from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from app.database import get_db
from app import schemas, models
from app.auth import get_current_user

router = APIRouter(prefix="/api/activities", tags=["Activity Tracker"])


@router.get("/sessions", response_model=schemas.ActivityListResponse)
def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    query = db.query(models.ActivitySession).filter(
        models.ActivitySession.user_id == current_user.id
    )
    total = query.count()
    sessions = query.order_by(desc(models.ActivitySession.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return schemas.ActivityListResponse(
        sessions=[
            schemas.ActivitySessionResponse(
                id=s.id, activity_type=s.activity_type,
                duration_seconds=s.duration_seconds, distance_km=s.distance_km,
                calories=s.calories, avg_pace=s.avg_pace, avg_speed=s.avg_speed,
                label=s.label, started_at=s.started_at, created_at=s.created_at,
                route_points=[
                    schemas.RoutePointResponse(id=r.id, lat=r.lat, lng=r.lng, timestamp=r.timestamp)
                    for r in s.route_points
                ],
            )
            for s in sessions
        ],
        total_count=total, page=page, page_size=page_size,
    )


@router.post("/sessions", response_model=schemas.ActivitySessionResponse, status_code=201)
def create_session(
    data: schemas.ActivitySessionCreate,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    session = models.ActivitySession(
        user_id=current_user.id, activity_type=data.activity_type,
        duration_seconds=data.duration_seconds, distance_km=data.distance_km,
        calories=data.calories, avg_pace=data.avg_pace, avg_speed=data.avg_speed,
        label=data.label,
    )
    db.add(session)
    db.flush()
    for rp in data.route_points:
        db.add(models.ActivityRoutePoint(
            session_id=session.id, lat=rp.lat, lng=rp.lng,
            timestamp=rp.timestamp,
        ))
    db.commit()
    db.refresh(session)
    return schemas.ActivitySessionResponse(
        id=session.id, activity_type=session.activity_type,
        duration_seconds=session.duration_seconds, distance_km=session.distance_km,
        calories=session.calories, avg_pace=session.avg_pace, avg_speed=session.avg_speed,
        label=session.label, started_at=session.started_at, created_at=session.created_at,
        route_points=[
            schemas.RoutePointResponse(id=r.id, lat=r.lat, lng=r.lng, timestamp=r.timestamp)
            for r in session.route_points
        ],
    )


@router.get("/sessions/{session_id}", response_model=schemas.ActivitySessionResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    session = db.query(models.ActivitySession).filter(
        models.ActivitySession.id == session_id,
        models.ActivitySession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(404, "Session not found")
    return schemas.ActivitySessionResponse(
        id=session.id, activity_type=session.activity_type,
        duration_seconds=session.duration_seconds, distance_km=session.distance_km,
        calories=session.calories, avg_pace=session.avg_pace, avg_speed=session.avg_speed,
        label=session.label, started_at=session.started_at, created_at=session.created_at,
        route_points=[
            schemas.RoutePointResponse(id=r.id, lat=r.lat, lng=r.lng, timestamp=r.timestamp)
            for r in session.route_points
        ],
    )


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    session = db.query(models.ActivitySession).filter(
        models.ActivitySession.id == session_id,
        models.ActivitySession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(404, "Session not found")
    db.delete(session)
    db.commit()
