
# Vision HUD Processor - V2.0
# Maps anatomical parts to 2D coordinate space and attaches corrective feedback strings.

ANATOMY_MAP = {
    "spine": {"x": 0.45, "y": 0.3, "w": 0.1, "h": 0.4},
    "knees": {"x": 0.35, "y": 0.7, "w": 0.3, "h": 0.15},
    "shoulders": {"x": 0.3, "y": 0.2, "w": 0.4, "h": 0.1},
    "head": {"x": 0.42, "y": 0.05, "w": 0.16, "h": 0.16}
}

def get_overlay_coordinates(analysis_results: list):
    """
    Takes a list of analysis result objects and returns HUD visualization data.
    """
    overlays = []
    for res in analysis_results:
        part = res["part"]
        if part in ANATOMY_MAP:
            overlays.append({
                "name": part,
                "box": ANATOMY_MAP[part],
                "status": res["status"],
                "feedback": res["msg"]
            })
    return overlays
