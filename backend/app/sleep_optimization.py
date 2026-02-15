
from datetime import datetime, time
from . import models

def calculate_circadian_alignment(sleep_start: datetime, sleep_end: datetime):
    """
    Compares user sleep windows with optimal hormonal secretion windows.
    Optimal Deep Sleep Window: 22:00 - 02:00
    """
    # Normalized scores
    start_hour = sleep_start.hour
    end_hour = sleep_end.hour
    
    alignment_score = 100
    
    # Penalize late start (after midnight)
    if start_hour >= 0 and start_hour < 6:
        alignment_score -= (start_hour + 1) * 10
    elif start_hour > 22:
        alignment_score -= (start_hour - 22) * 5
        
    duration = (sleep_end - sleep_start).total_seconds() / 3600
    if duration < 7:
        alignment_score -= (7 - duration) * 15
        
    return max(0, min(100, alignment_score))

def get_recovery_protocol(strain_score: float, sleep_quality: float):
    """
    Suggests bio-hacking protocols based on systemic strain vs recovery quality.
    """
    if strain_score > 80 and sleep_quality < 60:
        return {
            "protocol": "Emergency Neural Reset",
            "actions": ["20min Cold Plunge (10°C)", "Magnesium Bisglycinate (400mg)", "No blue light for 120min before rest"],
            "intensity_cap": "30% (Zone 1 only)"
        }
    elif strain_score > 60:
        return {
            "protocol": "Active Synchronization",
            "actions": ["15min Infrared Sauna", "Contrast Showers", "Dynamic Mobility Loop"],
            "intensity_cap": "75% (Sub-maximal)"
        }
    
    return {
        "protocol": "Peak Performance Loop",
        "actions": ["Standard hydration", "Pre-workout caffeine (200mg)", "Explosive loading"],
        "intensity_cap": "100% (Elite Output)"
    }
