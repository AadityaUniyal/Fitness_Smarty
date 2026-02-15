
from . import models

def get_hydration_requirement(user: models.EnhancedUser, activity_minutes: int = 0):
    """
    Calculates target water intake in milliliters.
    Base: 35ml per kg of body weight + 500ml per hour of high-intensity activity.
    """
    base_ml = (user.weight_kg or 70) * 35
    activity_bonus = (activity_minutes / 60) * 500
    target = base_ml + activity_bonus
    return {
        "target_ml": round(target),
        "status": "hydrated" if target < 3000 else "high_demand",
        "recommendation": f"Drink {round(target / 250)} glasses of water today."
    }
