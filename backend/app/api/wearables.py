from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from datetime import datetime, timezone
from app.database import get_db
from app import schemas, models
from app.auth import get_current_user

router = APIRouter(prefix="/api/wearables", tags=["Wearable Integrations"])


@router.get("/connections", response_model=List[schemas.WearableConnectionResponse])
def list_connections(
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    conns = db.query(models.WearableConnection).filter(
        models.WearableConnection.user_id == current_user.id
    ).all()
    result = []
    for c in conns:
        result.append(schemas.WearableConnectionResponse(
            id=c.id, device_id=c.device_id, device_name=c.device_name,
            connected=c.connected, last_sync=c.last_sync, created_at=c.created_at,
            metrics=[schemas.WearableMetricResponse(
                id=m.id, metric_type=m.metric_type, value=m.value,
                unit=m.unit, recorded_at=m.recorded_at,
            ) for m in c.metrics],
        ))
    return result


@router.post("/connections", response_model=schemas.WearableConnectionResponse, status_code=201)
def connect_device(
    data: schemas.WearableConnectRequest,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    existing = db.query(models.WearableConnection).filter(
        models.WearableConnection.user_id == current_user.id,
        models.WearableConnection.device_id == data.device_id,
    ).first()
    if existing:
        existing.connected = True
        db.commit()
        db.refresh(existing)
        conn = existing
    else:
        conn = models.WearableConnection(
            user_id=current_user.id, device_id=data.device_id,
            device_name=data.device_name, access_token=data.access_token,
        )
        db.add(conn)
        db.commit()
        db.refresh(conn)
    return schemas.WearableConnectionResponse(
        id=conn.id, device_id=conn.device_id, device_name=conn.device_name,
        connected=conn.connected, last_sync=conn.last_sync, created_at=conn.created_at,
        metrics=[],
    )


@router.delete("/connections/{connection_id}", status_code=204)
def disconnect_device(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    conn = db.query(models.WearableConnection).filter(
        models.WearableConnection.id == connection_id,
        models.WearableConnection.user_id == current_user.id,
    ).first()
    if not conn:
        raise HTTPException(404, "Connection not found")
    db.delete(conn)
    db.commit()


@router.post("/connections/{connection_id}/sync")
def sync_device(
    connection_id: int,
    metrics: List[schemas.WearableMetricCreate],
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    conn = db.query(models.WearableConnection).filter(
        models.WearableConnection.id == connection_id,
        models.WearableConnection.user_id == current_user.id,
    ).first()
    if not conn:
        raise HTTPException(404, "Connection not found")
    for m in metrics:
        db.add(models.WearableMetric(
            connection_id=conn.id, metric_type=m.metric_type,
            value=m.value, unit=m.unit, recorded_at=m.recorded_at or datetime.now(timezone.utc),
        ))
    conn.last_sync = datetime.now(timezone.utc)
    db.commit()
    return {"synced": len(metrics), "message": f"Synced {len(metrics)} metrics"}


@router.get("/metrics/aggregated")
def get_aggregated_metrics(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: models.EnhancedUser = Depends(get_current_user),
):
    from datetime import timedelta
    since = datetime.now(timezone.utc) - timedelta(days=days)
    conns = db.query(models.WearableConnection).filter(
        models.WearableConnection.user_id == current_user.id,
        models.WearableConnection.connected == True,
    ).all()
    conn_ids = [c.id for c in conns]
    if not conn_ids:
        return {"metrics": {}, "days": days}
    metrics = db.query(models.WearableMetric).filter(
        models.WearableMetric.connection_id.in_(conn_ids),
        models.WearableMetric.recorded_at >= since,
    ).all()
    aggregated = {}
    for m in metrics:
        if m.metric_type not in aggregated:
            aggregated[m.metric_type] = []
        aggregated[m.metric_type].append({
            "value": m.value, "unit": m.unit, "recorded_at": m.recorded_at.isoformat(),
        })
    return {"metrics": aggregated, "days": days}
