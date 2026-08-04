"""
Gender-Specific Health API Endpoints

Gender-specific calculations and FemmeCare features
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.gender_specific_service import GenderSpecificService
from app.clerk_auth import get_current_user_id_from_clerk as get_current_user_id


router = APIRouter(
    prefix="/api/gender-health",
    tags=["Gender-Specific Health"]
)


class FemmeCarerToggleRequest(BaseModel):
    """Request to enable/disable FemmeCare features"""
    user_id: int
    enabled: bool


@router.get("/bmr/{user_id}")
def calculate_bmr(
    user_id: int,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Calculate Basal Metabolic Rate with gender-specific formula.
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        from app.models import EnhancedUser, UserProfile
        
        user = db.query(EnhancedUser).filter(EnhancedUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = db.query(UserProfile).filter(UserProfile.user_id == str(user_id)).first()
        
        weight_kg = user.weight_kg or (profile.weight_kg if profile else None) or 70.0
        height_cm = user.height_cm or (profile.height_cm if profile else None) or 170.0
        age = user.age or (profile.age if profile else None) or 30
        gender = user.gender or (profile.gender if profile else None) or "male"
        
        service = GenderSpecificService(db)
        bmr = service.calculate_bmr_gender_specific(
            weight_kg=weight_kg,
            height_cm=height_cm,
            age=age,
            gender=gender
        )
        
        return {
            "user_id": user_id,
            "gender": gender,
            "bmr": bmr,
            "explanation": f"Your body burns {bmr} calories per day at rest (gender-specific calculation)",
            "formula_used": "Mifflin-St Jeor equation"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate BMR: {str(e)}")


@router.get("/tdee/{user_id}")
def calculate_tdee(
    user_id: int,
    include_femmecare: bool = Query(True, description="Include cycle-based adjustments for females"),
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Calculate Total Daily Energy Expenditure with gender-specific adjustments.
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        service = GenderSpecificService(db)
        result = service.calculate_tdee_gender_specific(
            user_id=user_id,
            include_femmecare_adjustments=include_femmecare
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate TDEE: {str(e)}")


@router.get("/macro-targets/{user_id}")
def get_macro_targets(
    user_id: int,
    goal: str = Query("maintenance", description="weight_loss, muscle_gain, maintenance, or athletic"),
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Calculate macro targets with gender-specific adjustments.
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        service = GenderSpecificService(db)
        result = service.get_gender_specific_macro_targets(
            user_id=user_id,
            goal=goal
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate macros: {str(e)}")


@router.post("/femmecare/toggle")
def toggle_femmecare(
    request: FemmeCarerToggleRequest,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Enable or disable FemmeCare features for female users.
    """
    if str(request.user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        service = GenderSpecificService(db)
        result = service.toggle_femmecare(
            user_id=request.user_id,
            enabled=request.enabled
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle FemmeCare: {str(e)}")


@router.get("/femmecare/dashboard/{user_id}")
def get_femmecare_dashboard(
    user_id: int,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Get comprehensive FemmeCare dashboard.
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        service = GenderSpecificService(db)
        result = service.get_femmecare_dashboard(user_id=user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


@router.get("/femmecare/current-phase/{user_id}")
def get_current_cycle_phase(
    user_id: int,
    db: Session = Depends(get_db),
    current_auth_id: str = Depends(get_current_user_id)
):
    """
    Get current menstrual cycle phase and recommendations.
    """
    if str(user_id) != str(current_auth_id):
        raise HTTPException(status_code=403, detail="Operation forbidden.")
    try:
        service = GenderSpecificService(db)
        cycle_data = service._get_current_cycle_phase(user_id)
        
        if not cycle_data:
            return {
                "message": "No cycle data logged yet. Start tracking your period to get personalized insights.",
                "has_data": False
            }
        
        phase_info = {
            "menstrual": {
                "name": "Menstrual Phase",
                "emoji": "🩸",
                "description": "Period days. Rest and recovery time.",
                "energy_level": "Low"
            },
            "follicular": {
                "name": "Follicular Phase",
                "emoji": "🌱",
                "description": "Energy rising. Great for new challenges.",
                "energy_level": "Increasing"
            },
            "ovulation": {
                "name": "Ovulation",
                "emoji": "⚡",
                "description": "Peak energy and strength. Push hard!",
                "energy_level": "Peak"
            },
            "luteal": {
                "name": "Luteal Phase",
                "emoji": "🌙",
                "description": "Energy declining. Focus on moderate activity.",
                "energy_level": "Moderate to Low"
            }
        }
        
        phase = cycle_data['phase']
        info = phase_info.get(phase, {})
        
        return {
            "has_data": True,
            "phase": phase,
            "phase_name": info.get("name", phase.title()),
            "emoji": info.get("emoji", "📅"),
            "description": info.get("description", ""),
            "energy_level": info.get("energy_level", "Unknown"),
            "days_since_period": cycle_data['days_since_period'],
            "last_period_date": cycle_data['last_period_date']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get phase: {str(e)}")


@router.get("/comparison/male-female")
def get_gender_comparison(
    db: Session = Depends(get_db)
):
    """
    Educational endpoint showing physiological differences between male and female.
    
    Helps users understand why gender-specific calculations matter.
    """
    return {
        "bmr_difference": {
            "explanation": "Women typically have 10-15% lower BMR than men of same weight/height",
            "reason": "Lower muscle mass percentage and different hormonal profile",
            "formula_difference": {
                "male_adjustment": "+5 calories",
                "female_adjustment": "-161 calories"
            }
        },
        "nutritional_needs": {
            "iron": {
                "male": "8 mg/day",
                "female": "18 mg/day (menstruating), 8 mg/day (post-menopause)",
                "reason": "Blood loss during menstruation"
            },
            "calcium": {
                "both": "1000-1200 mg/day",
                "female_note": "Extra important for bone health, especially post-menopause"
            },
            "protein": {
                "both": "1.6-2.2 g/kg body weight for athletes",
                "note": "Same relative needs, but absolute amounts differ due to body composition"
            },
            "healthy_fats": {
                "male": "20-30% of calories",
                "female": "25-35% of calories",
                "reason": "Essential for hormone production and menstrual health"
            }
        },
        "training_considerations": {
            "female_advantages": [
                "Better endurance capacity",
                "Faster recovery between sets",
                "Better fat oxidation during exercise"
            ],
            "male_advantages": [
                "Higher baseline strength due to muscle mass",
                "More testosterone for muscle growth"
            ],
            "cycle_considerations": [
                "Follicular phase: Best time for strength training and PR attempts",
                "Luteal phase: Better for endurance, may need slightly more calories",
                "Menstrual phase: Listen to body, lighter training acceptable"
            ]
        },
        "femmecare_benefits": {
            "enabled": [
                "Cycle-synced workout recommendations",
                "Phase-specific nutrition advice",
                "Calorie adjustments for luteal phase (~7.5% increase)",
                "Period tracking and predictions",
                "Pregnancy and menopause support modes"
            ],
            "privacy": "All cycle data is encrypted and stored securely"
        }
    }
