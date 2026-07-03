"""
Anomaly / Logging-Error Detection Engine
Uses simple, robust rolling statistics (Z-score and IQR) to identify potential fat-fingered logs.
"""

from typing import List, Dict, Any, Tuple
import math


def calculate_mean_and_std(values: List[float]) -> Tuple[float, float]:
    """
    Helper to calculate mean and standard deviation of a list of floats.
    """
    if not values:
        return 0.0, 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std = math.sqrt(variance)
    return mean, std


def calculate_percentile(values: List[float], percentile: float) -> float:
    """
    Helper to calculate the percentile of a list of floats.
    """
    if not values:
        return 0.0
    sorted_val = sorted(values)
    k = (len(sorted_val) - 1) * percentile
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_val[int(k)]
    d0 = sorted_val[int(f)] * (c - k)
    d1 = sorted_val[int(c)] * (k - f)
    return d0 + d1


def detect_outliers_zscore(values: List[float], threshold: float = 3.0) -> List[bool]:
    """
    Detect outliers using standard Z-score.
    Returns a list of booleans indicating whether each element is an outlier.
    """
    if len(values) < 3:
        return [False] * len(values)
    
    mean, std = calculate_mean_and_std(values)
    if std == 0:
        return [False] * len(values)
        
    return [abs(x - mean) / std > threshold for x in values]


def detect_outliers_iqr(values: List[float], factor: float = 1.5) -> List[bool]:
    """
    Detect outliers using Interquartile Range (IQR).
    Returns a list of booleans indicating whether each element is an outlier.
    """
    if len(values) < 4:
        return [False] * len(values)
        
    q25 = calculate_percentile(values, 0.25)
    q75 = calculate_percentile(values, 0.75)
    iqr = q75 - q25
    
    lower_bound = q25 - (factor * iqr)
    upper_bound = q75 + (factor * iqr)
    
    return [x < lower_bound or x > upper_bound for x in values]


def check_single_log_anomaly(
    history: List[float],
    new_value: float,
    metric_type: str = "calories",
    z_threshold: float = 2.5
) -> Dict[str, Any]:
    """
    Checks if a newly logged value is highly anomalous compared to historical entries.
    
    metric_type: 'calories' or 'weight'
    """
    if not history:
        # Check absolute bounds as a fallback
        if metric_type == "calories" and (new_value < 50 or new_value > 8000):
            return {
                "is_anomaly": True,
                "reason": f"Value {new_value} kcal is outside typical physiological limits (50-8000 kcal)."
            }
        if metric_type == "weight" and (new_value < 30 or new_value > 250):
            return {
                "is_anomaly": True,
                "reason": f"Value {new_value} kg is outside plausible human limits (30-250 kg)."
            }
        return {"is_anomaly": False, "reason": "No history available to flag anomaly."}

    # Add the new value to history to calculate outlier statistics
    combined = history + [new_value]
    
    # We use IQR for calories (often right-skewed) and Z-score/IQR for weight (normally distributed)
    is_anomaly = False
    reason = ""
    
    if metric_type == "weight":
        # Check 1: Sudden day-to-day percentage jump
        last_weight = history[-1]
        pct_change = abs(new_value - last_weight) / last_weight
        if pct_change > 0.05:  # Change of > 5% in one log
            return {
                "is_anomaly": True,
                "reason": f"Weight change of {pct_change*100:.1f}% is physically implausible for a single log interval."
            }
            
        # Check 2: Z-score outlier
        mean, std = calculate_mean_and_std(history)
        if std > 0.1:  # Only if there's enough variation
            z_score = abs(new_value - mean) / std
            if z_score > z_threshold:
                is_anomaly = True
                reason = f"Weight {new_value}kg is a Z-score outlier (Z={z_score:.2f}, mean={mean:.1f}kg, std={std:.2f}kg)."
                
    else:  # calories
        # IQR outlier detection
        q25 = calculate_percentile(history, 0.25)
        q75 = calculate_percentile(history, 0.75)
        iqr = q75 - q25
        if iqr > 100:  # Avoid flagging standard variances
            upper_limit = q75 + 2.0 * iqr
            lower_limit = max(0.0, q25 - 2.0 * iqr)
            if new_value > upper_limit:
                is_anomaly = True
                reason = f"Calorie log of {new_value} kcal exceeds the statistical upper threshold of {upper_limit:.0f} kcal (IQR range: {q25:.0f}-{q75:.0f} kcal)."
            elif new_value < lower_limit:
                is_anomaly = True
                reason = f"Calorie log of {new_value} kcal is below the statistical lower threshold of {lower_limit:.0f} kcal."
        else:
            # Simple bounds check if historical variance is tiny
            mean = sum(history) / len(history)
            if new_value > mean * 2.5:
                is_anomaly = True
                reason = f"Calorie log of {new_value} kcal is over 2.5x your typical mean intake ({mean:.0f} kcal)."

    return {
        "is_anomaly": is_anomaly,
        "reason": reason if is_anomaly else "Log is within standard statistical bounds."
    }
