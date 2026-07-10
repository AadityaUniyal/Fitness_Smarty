from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.clerk_auth import get_current_user_id_from_clerk as get_current_user
from app.database import get_db
from app.unified_coach_service import UnifiedCoachService

router = APIRouter(prefix="/api/coach", tags=["Unified Personal Coach"])


@router.get("/daily", response_model=schemas.CoachDailyResponse)
def get_daily_coach(
    db: Session = Depends(get_db), user_id: str = Depends(get_current_user)
):
    """
    Get the unified daily coach advice, checklist, workout splits,
    next meal plans, and recovery guidance.
    """
    service = UnifiedCoachService(db=db)
    try:
        plan = service.get_daily_coach_plan(user_id=user_id)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Coach calculation error: {str(e)}"
        )
