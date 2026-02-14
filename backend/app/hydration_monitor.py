
from . import db_models

def get_hydration_requirement(user: db_models.EnhancedUser, activity_minutes: int = 0):
    """
    Calculates target water intake in milliliters.
    Base: 35ml per kg of body weight + 500ml per hour of high-intensity activity.
    """
    base_ml = user.weight * 35
    activity_ml = (activity_minutes / 60) * 750 # Higher loss during training
    
    total_target = base_ml + activity_ml
    
    return {
        "target_ml": round(total_target, 0),
        "target_oz": round(total_target / 29.5735, 1),
        "intervals": 8,
        "advice": "Neural cooling protocol: Sip 250ml every 90 minutes."
    }
