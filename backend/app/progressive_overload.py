"""
Progressive Overload & Periodization Engine
Pure logic functions to track exercise volume, detect plateaus, and recommend
the next session's sets, reps, and weight.
"""

from typing import List, Dict, Any, Tuple, Optional


def calculate_session_volume(sets: List[Dict[str, Any]]) -> float:
    """
    Calculates the total volume of a session: sum(reps * weight)
    """
    return sum(float(s.get("reps", 0)) * float(s.get("weight", 0.0)) for s in sets)


def calculate_one_rep_max(weight: float, reps: int) -> float:
    """
    Estimate 1-Rep Max using the Epley formula: 1RM = w * (1 + r/30)
    """
    if reps <= 0:
        return 0.0
    if reps == 1:
        return weight
    return weight * (1.0 + reps / 30.0)


def detect_plateau(volumes: List[float], sessions_to_check: int = 3) -> bool:
    """
    Detects a plateau if the volume has not increased for `sessions_to_check` consecutive sessions.
    volumes is in chronological order (oldest to newest).
    """
    if len(volumes) < sessions_to_check + 1:
        return False
    
    # Take the last `sessions_to_check` + 1 volumes
    relevant_volumes = volumes[-(sessions_to_check + 1):]
    
    # A plateau exists if each subsequent volume is less than or equal to the prior volume,
    # or if there is no significant increase (e.g. within 1% margin)
    for i in range(1, len(relevant_volumes)):
        if relevant_volumes[i] > relevant_volumes[i - 1] * 1.01:
            return False  # There was an increase of >1%
            
    return True


def prescribe_next_session(
    history: List[Dict[str, Any]],
    exercise_name: str,
    progression_type: str = "double_progression", # 'double_progression' or 'one_rep_max'
    min_reps: int = 8,
    max_reps: int = 12,
    weight_increment: float = 2.5
) -> Dict[str, Any]:
    """
    Prescribes the next session's weight and rep targets for an exercise.
    
    history: List of past sessions, in chronological order.
             Each session is: {"date": str, "sets": [{"reps": int, "weight": float}]}
             
    Returns:
        Dict detailing:
            - next_sets: List of {"reps": int, "weight": float}
            - plateau_detected: bool
            - progression_applied: str
            - reasoning: str
    """
    if not history:
        # Default starting prescription
        default_weight = 20.0  # default bar weight
        return {
            "sets": [{"reps": min_reps, "weight": default_weight}] * 3,
            "plateau_detected": False,
            "progression_applied": "initial",
            "reasoning": f"No history found. Prescribing baseline of 3 sets of {min_reps} reps at {default_weight}kg."
        }

    # Extract sets and volumes
    volumes = []
    parsed_sessions = []
    for h in history:
        sets = h.get("sets", [])
        vol = calculate_session_volume(sets)
        volumes.append(vol)
        parsed_sessions.append(sets)

    last_sets = parsed_sessions[-1]
    plateau = detect_plateau(volumes, sessions_to_check=3)

    if plateau:
        # If plateau is detected, we prescribe a de-load (reduce weight by 10%, keep reps/sets same)
        # or reduce volume to break through the plateau.
        new_sets = []
        for s in last_sets:
            new_weight = max(1.0, round((s.get("weight", 0.0) * 0.9) / 0.5) * 0.5)  # Round to nearest 0.5kg
            new_sets.append({"reps": s.get("reps", min_reps), "weight": new_weight})
        
        return {
            "sets": new_sets,
            "plateau_detected": True,
            "progression_applied": "deload",
            "reasoning": "Plateau detected (no volume increase in last 3 sessions). Prescribing a 10% de-load to facilitate recovery."
        }

    # Progression logic
    if progression_type == "double_progression":
        # Rule: Focus on increasing reps first.
        # If all sets hit max_reps at the current weight, increase the weight and reset reps to min_reps.
        # Otherwise, attempt to increase reps on the first set, or match the last session.
        all_hit_max = all(s.get("reps", 0) >= max_reps for s in last_sets)
        
        if all_hit_max:
            # Increase weight, reset reps to min_reps
            new_sets = []
            for s in last_sets:
                new_weight = s.get("weight", 0.0) + weight_increment
                new_sets.append({"reps": min_reps, "weight": new_weight})
            reasoning = f"All sets met/exceeded max rep limit ({max_reps}). Increasing weight by +{weight_increment}kg and resetting target reps to {min_reps}."
            applied = "weight_increase"
        else:
            # Try to add reps to the sets that haven't hit max_reps yet
            new_sets = []
            incremented = False
            for s in last_sets:
                curr_reps = s.get("reps", 0)
                curr_weight = s.get("weight", 0.0)
                if curr_reps < max_reps and not incremented:
                    new_sets.append({"reps": curr_reps + 1, "weight": curr_weight})
                    incremented = True
                else:
                    new_sets.append({"reps": curr_reps, "weight": curr_weight})
            
            reasoning = "Target reps incremented on incomplete set to drive progressive overload." if incremented else "Match previous performance to stabilize volume."
            applied = "rep_increase" if incremented else "maintain"
            
        return {
            "sets": new_sets,
            "plateau_detected": False,
            "progression_applied": applied,
            "reasoning": reasoning
        }
        
    elif progression_type == "one_rep_max":
        # Rule: Calculate average 1RM of last session. Target next session at a percentage of 1RM or step up.
        # If last session was successfully completed, increase target 1RM by a fraction and prescribe targets.
        avg_1rm = sum(calculate_one_rep_max(s.get("weight", 0.0), s.get("reps", 0)) for s in last_sets) / len(last_sets)
        
        # Target 1RM step-up: +2.5%
        target_1rm = avg_1rm * 1.025
        
        # Prescribe reps & weights based on target 1RM: Weight = 1RM / (1 + reps/30)
        # We'll target a solid middle ground rep count, e.g. 10 reps
        target_reps = (min_reps + max_reps) // 2
        prescribed_weight = round((target_1rm / (1.0 + target_reps / 30.0)) / 0.5) * 0.5
        
        new_sets = [{"reps": target_reps, "weight": prescribed_weight}] * len(last_sets)
        
        return {
            "sets": new_sets,
            "plateau_detected": False,
            "progression_applied": "1rm_stepping",
            "reasoning": f"Based on estimated 1RM ({avg_1rm:.1f}kg), stepping up target 1RM to {target_1rm:.1f}kg and prescribing {target_reps} reps at {prescribed_weight}kg."
        }
        
    else:
        # Fallback to copy last
        return {
            "sets": last_sets,
            "plateau_detected": False,
            "progression_applied": "maintain",
            "reasoning": "Unknown progression rule; maintaining previous session layout."
        }
