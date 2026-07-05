import os
import json

# Global categories mapping — now using wger's real categories
# Maps wger category name → fitness_goal used by the recommendation engine
WGER_CATEGORY_GOAL_MAP = {
    "Abs": "fat_loss",
    "Arms": "muscle_gain",
    "Back": "muscle_gain",
    "Calves": "maintenance",
    "Cardio": "fat_loss",
    "Chest": "muscle_gain",
    "Legs": "muscle_gain",
    "Shoulders": "muscle_gain",
}

# Legacy mapping kept for reference
LEGACY_CATEGORIES = {
    "Fat Loss Cardio": "fat_loss",
    "Muscle Building": "muscle_gain",
    "Athletic Performance": "athletic",
    "Maintenance & Mobility": "maintenance"
}


def generate_exercises_json():
    """
    Return path to the exercise seed JSON.

    Priority:
    1. wger-sourced data (backend/app/seed_data/exercises_wger.json)
       — the real dataset.
    2. Minimal hardcoded fallback (~20 exercises) — emergency only.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    seed_data_dir = os.path.join(base_dir, "seed_data")
    os.makedirs(seed_data_dir, exist_ok=True)

    # 1. Prefer wger-sourced data
    wger_file = os.path.join(seed_data_dir, "exercises_wger.json")
    if os.path.exists(wger_file) and os.path.getsize(wger_file) > 1000:
        return wger_file

    # 2. Fallback: check legacy file
    legacy_file = os.path.join(seed_data_dir, "exercises.json")
    if os.path.exists(legacy_file) and os.path.getsize(legacy_file) > 1000:
        return legacy_file

    # 3. Emergency fallback: generate a minimal set inline
    print(
        "[!] No wger seed data found. Run "
        "'python backend/scripts/fetch_wger_exercises.py' first."
    )
    print("[!] Generating minimal fallback exercise set.")
    exercises = _minimal_fallback_exercises()
    fallback_file = os.path.join(seed_data_dir, "exercises.json")
    with open(fallback_file, "w") as f:
        json.dump(exercises, f, indent=2)
    print(f"Generated {len(exercises)} fallback exercises at {fallback_file}")
    return fallback_file


def _minimal_fallback_exercises():
    """
    A small but real set of exercises for when wger data hasn't
    been fetched yet.
    """
    exercises = []

    def add(cat, name, muscle, equip, cpm, goal, desc):
        diff = "Beginner"
        if cpm >= 12.0:
            diff = "Advanced"
        elif cpm >= 7.0:
            diff = "Intermediate"
        exercises.append({
            "category_name": cat,
            "name": name,
            "targeted_muscle": muscle,
            "difficulty": diff,
            "equipment": equip,
            "calories_per_min": cpm,
            "fitness_goal": goal,
            "description": desc,
            "source": "fallback"
        })

    # Cardio / fat_loss
    add(
        "Cardio", "Burpees", "Full Body", "Bodyweight", 14.0, "fat_loss",
        "High-intensity burpee interval for total body conditioning."
    )
    add(
        "Cardio", "Jump Rope", "Calves", "Jump Rope", 12.0, "fat_loss",
        "Cardio skipping drill targeting coordination and calves."
    )
    add(
        "Cardio", "Treadmill Sprint", "Legs", "Treadmill", 16.0, "fat_loss",
        "High intensity interval sprint."
    )
    add(
        "Cardio", "Rowing Machine", "Back", "Rowing Machine", 13.0, "fat_loss",
        "Full body cardiovascular workout targeting back and legs."
    )
    add(
        "Cardio", "Mountain Climbers", "Core", "Bodyweight", 9.5, "fat_loss",
        "Core-intensive cardio drill."
    )

    # Chest / muscle_gain
    add(
        "Chest", "Bench Press", "Chest", "Barbell", 7.5, "muscle_gain",
        "Horizontal press for chest thickness and strength."
    )
    add(
        "Chest", "Push-up", "Chest", "Bodyweight", 6.0, "muscle_gain",
        "Standard bodyweight push-up."
    )
    add(
        "Chest", "Dumbbell Fly", "Chest", "Dumbbell", 5.0, "muscle_gain",
        "Chest isolation fly movement."
    )

    # Back / muscle_gain
    add(
        "Back", "Deadlift", "Full Body", "Barbell", 14.0, "muscle_gain",
        "Compound pull targeting posterior chain."
    )
    add(
        "Back", "Pull-up", "Lats", "Bodyweight", 8.5, "muscle_gain",
        "Vertical pull for back width."
    )
    add(
        "Back", "Barbell Row", "Back", "Barbell", 8.0, "muscle_gain",
        "Bent-over horizontal pull for back thickness."
    )

    # Legs / muscle_gain
    add(
        "Legs", "Barbell Squat", "Quadriceps", "Barbell", 10.0, "muscle_gain",
        "Primary compound leg builder."
    )
    add(
        "Legs", "Romanian Deadlift", "Hamstrings", "Barbell", 7.5,
        "muscle_gain", "Hip hinge for hamstrings and glutes."
    )
    add(
        "Legs", "Leg Press", "Quadriceps", "Machine", 6.5, "muscle_gain",
        "Sled leg press for quad hypertrophy."
    )

    # Arms / muscle_gain
    add(
        "Arms", "Barbell Bicep Curl", "Biceps", "Barbell", 4.0, "muscle_gain",
        "Standard bicep curl."
    )
    add(
        "Arms", "Tricep Pushdown", "Triceps", "Cable Machine", 4.0,
        "muscle_gain", "Tricep isolation pushdown."
    )

    # Shoulders / muscle_gain
    add(
        "Shoulders", "Overhead Press", "Shoulders", "Barbell", 7.0,
        "muscle_gain", "Vertical overhead press for deltoid strength."
    )
    add(
        "Shoulders", "Lateral Raise", "Shoulders", "Dumbbell", 4.0,
        "muscle_gain", "Isolation for lateral deltoids."
    )

    # Abs / fat_loss
    add(
        "Abs", "Plank", "Core", "Bodyweight", 3.5, "fat_loss",
        "Isometric core stabilization."
    )
    add(
        "Abs", "Crunches", "Abs", "Bodyweight", 4.0, "fat_loss",
        "Standard abdominal crunch."
    )

    # Calves / maintenance
    add(
        "Calves", "Standing Calf Raise", "Calves", "Machine", 3.5,
        "maintenance", "Calf extension for gastrocnemius."
    )

    return exercises


if __name__ == "__main__":
    path = generate_exercises_json()
    with open(path) as f:
        data = json.load(f)
    print(f"Seed file: {path}")
    print(f"Exercises: {len(data)}")

