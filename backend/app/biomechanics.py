
# Procedural Biomechanics Engine - V2.0
# Expanded logic for high-fidelity form correction feedback.

def evaluate_form(joint_data: dict):
    """
    Evaluates joint angles and provides a detailed status report with corrective instructions.
    """
    results = []
    
    # Spine alignment analysis
    spine_angle = joint_data.get("spine_angle", 180)
    if spine_angle < 155:
        results.append({
            "part": "spine",
            "status": "critical",
            "msg": "SEVERE KYPHOSIS DETECTED. Immediately retract scapula and engage core to stabilize lumbar spine."
        })
    elif spine_angle < 170:
        results.append({
            "part": "spine",
            "status": "warning",
            "msg": "Minor spinal rounding. Think about pulling your chest through your arms."
        })
    else:
        results.append({
            "part": "spine",
            "status": "optimal",
            "msg": "Spinal stack is nominal. Force distribution is optimized."
        })
        
    # Knee tracking and depth analysis
    knee_val = joint_data.get("knee_depth", 0)
    knee_alignment = joint_data.get("knee_alignment", "neutral") # valgus/varus
    
    if knee_alignment == "valgus":
        results.append({
            "part": "knees",
            "status": "critical",
            "msg": "KNEE VALGUS DETECTED. Drive knees outward to align with second toe to prevent ACL stress."
        })
    elif knee_val > 100:
        results.append({
            "part": "knees",
            "status": "warning",
            "msg": "Deep range detected. Ensure heel pressure remains constant."
        })
    else:
        results.append({
            "part": "knees",
            "status": "optimal",
            "msg": "Patellar tracking within safe kinetic window."
        })

    return results

def calculate_injury_risk(stress_nodes: list):
    """Calculates a percentage risk based on status weights."""
    weights = {"optimal": 0, "warning": 10, "critical": 40}
    total_risk = sum(weights.get(node["status"], 0) for node in stress_nodes)
    return min(total_risk + 5, 99)
