
import random
from datetime import datetime, timedelta

CHALLENGE_TEMPLATES = [
    {"title": "Metabolic Surge", "goal": "Burn 15,000 KCAL in 7 days", "reward": 2500},
    {"title": "Iron Resilience", "goal": "Complete 5 Strength Nodes this week", "reward": 1800},
    {"title": "Zen Sync", "goal": "Log 120 minutes of Neural Mobility", "reward": 1200},
    {"title": "Hydration Master", "goal": "Hit water targets for 5 consecutive days", "reward": 800}
]

def get_active_challenges():
    """Returns a set of randomly selected community challenges."""
    # In a real app, this would query a global DB. Here we simulate dynamic selection.
    selected = random.sample(CHALLENGE_TEMPLATES, 2)
    
    return [
        {
            **c,
            "expiry": (datetime.utcnow() + timedelta(days=3)).isoformat(),
            "participants": random.randint(100, 5000)
        } for c in selected
    ]
