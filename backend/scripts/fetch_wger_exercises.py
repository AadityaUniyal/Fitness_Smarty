"""
fetch_wger_exercises.py — Pull real exercise data from the wger public API.

Fetches all English-language exercises from https://wger.de/api/v2/,
resolves muscle/equipment IDs to human-readable names, derives difficulty
and calories_per_min via MET-based heuristics, and writes a deduplicated
JSON seed file to backend/app/seed_data/exercises_wger.json.

Run once (or whenever you want to refresh):
    python backend/scripts/fetch_wger_exercises.py

License: wger exercise text/metadata is CC-BY-SA 4.0.
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

BASE_URL = "https://wger.de/api/v2"
LANGUAGE_EN = 2
PAGE_SIZE = 100
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "app" / "seed_data"
OUTPUT_FILE = OUTPUT_DIR / "exercises_wger.json"

# ── Lookup tables (fetched once) ──────────────────────────────────────────────

def _get_json(url: str, retries: int = 3) -> dict:
    """Fetch JSON from a URL with simple retry/backoff."""
    for attempt in range(retries):
        try:
            req = Request(url, headers={"Accept": "application/json", "User-Agent": "SmartyReco/1.0"})
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except (URLError, HTTPError, TimeoutError) as exc:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"  [retry {attempt+1}] {exc} — waiting {wait}s …")
                time.sleep(wait)
            else:
                raise


def fetch_lookup(endpoint: str) -> dict:
    """Fetch a simple id→name lookup from a wger list endpoint."""
    data = _get_json(f"{BASE_URL}/{endpoint}/?format=json&limit=200")
    return {item["id"]: item.get("name_en") or item["name"] for item in data["results"]}


# ── MET-based calorie heuristics ──────────────────────────────────────────────

# Approximate MET values by wger category name.
# Source: Compendium of Physical Activities (Ainsworth 2011), simplified.
_CATEGORY_MET = {
    "Abs":       3.8,
    "Arms":      3.5,
    "Back":      5.0,
    "Calves":    3.5,
    "Cardio":    8.0,
    "Chest":     5.0,
    "Legs":      6.0,
    "Shoulders": 4.0,
}

# Equipment modifiers — compound/heavy equipment bumps MET up.
_EQUIP_MOD = {
    "Barbell":               1.20,
    "Dumbbell":              1.10,
    "Kettlebell":            1.15,
    "SZ-Bar":                1.10,
    "Bench":                 1.05,
    "Incline bench":         1.05,
    "Pull-up bar":           1.15,
    "Swiss Ball":            1.05,
    "Gym mat":               0.95,
    "Resistance band":       0.95,
    "none (bodyweight exercise)": 1.00,
}


def _estimate_calories_per_min(category_name: str, equipment_names: list[str]) -> float:
    """Return estimated kcal/min for a 70 kg person (MET × 3.5 × 70 / 200)."""
    met = _CATEGORY_MET.get(category_name, 4.0)
    if equipment_names:
        # take the max equipment modifier (strongest piece of equipment)
        mod = max(_EQUIP_MOD.get(e, 1.0) for e in equipment_names)
        met *= mod
    cpm = met * 3.5 * 70 / 200  # standard MET→kcal/min formula
    return round(cpm, 1)


def _estimate_difficulty(muscle_count: int, equipment_names: list[str]) -> str:
    """Heuristic difficulty from muscle count + equipment complexity."""
    heavy = {"Barbell", "Kettlebell", "Pull-up bar"}
    has_heavy = bool(set(equipment_names) & heavy)
    if muscle_count >= 3 or (muscle_count >= 2 and has_heavy):
        return "Advanced"
    elif muscle_count >= 2 or has_heavy:
        return "Intermediate"
    return "Beginner"


# ── Fitness goal mapping ──────────────────────────────────────────────────────

_CATEGORY_TO_GOAL = {
    "Cardio":    "fat_loss",
    "Abs":       "fat_loss",
    "Chest":     "muscle_gain",
    "Back":      "muscle_gain",
    "Arms":      "muscle_gain",
    "Shoulders": "muscle_gain",
    "Legs":      "muscle_gain",
    "Calves":    "maintenance",
}


# ── Main fetch logic ─────────────────────────────────────────────────────────

def fetch_all_exercises() -> list[dict]:
    print("Fetching wger lookup tables …")
    muscles = fetch_lookup("muscle")
    equipment = fetch_lookup("equipment")
    categories = fetch_lookup("exercisecategory")
    print(f"  {len(muscles)} muscles, {len(equipment)} equipment types, {len(categories)} categories")

    exercises = []
    seen = set()  # (lower_name, equip_str) for dedup

    url = f"{BASE_URL}/exerciseinfo/?format=json&language={LANGUAGE_EN}&limit={PAGE_SIZE}"
    page = 0

    while url:
        page += 1
        print(f"Fetching page {page} … ({url[:80]}…)")
        data = _get_json(url)

        for ex in data["results"]:
            # Extract English translation
            translations = ex.get("translations", [])
            en_trans = [t for t in translations if t.get("language") == LANGUAGE_EN]
            if not en_trans:
                continue  # skip exercises without English name
            name = en_trans[0].get("name", "").strip()
            if not name or len(name) < 3:
                continue

            description = en_trans[0].get("description", "").strip()
            # Strip HTML tags from description (wger uses HTML)
            import re
            description = re.sub(r"<[^>]+>", "", description).strip()
            if len(description) > 500:
                description = description[:497] + "…"

            cat_info = ex.get("category", {})
            cat_name = cat_info.get("name", "General") if isinstance(cat_info, dict) else categories.get(cat_info, "General")

            primary_muscles = [muscles.get(m["id"] if isinstance(m, dict) else m, "Unknown")
                               for m in ex.get("muscles", [])]
            secondary_muscles = [muscles.get(m["id"] if isinstance(m, dict) else m, "Unknown")
                                 for m in ex.get("muscles_secondary", [])]
            equip_list = [equipment.get(e["id"] if isinstance(e, dict) else e, "Bodyweight")
                          for e in ex.get("equipment", [])]

            # Deduplicate on (lower name, sorted equipment)
            equip_str = ",".join(sorted(equip_list)) or "Bodyweight"
            dedup_key = (name.lower(), equip_str.lower())
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            all_muscles = primary_muscles + secondary_muscles
            targeted_muscle = primary_muscles[0] if primary_muscles else cat_name

            exercises.append({
                "name": name,
                "category_name": cat_name,
                "targeted_muscle": targeted_muscle,
                "primary_muscles": primary_muscles,
                "secondary_muscles": secondary_muscles,
                "equipment": equip_str if equip_list else "Bodyweight",
                "difficulty": _estimate_difficulty(len(all_muscles), equip_list),
                "calories_per_min": _estimate_calories_per_min(cat_name, equip_list),
                "fitness_goal": _CATEGORY_TO_GOAL.get(cat_name, "maintenance"),
                "description": description or f"{cat_name} exercise targeting {targeted_muscle}.",
                "source": "wger.de (CC-BY-SA 4.0)",
                "wger_id": ex.get("id"),
            })

        url = data.get("next")
        if url:
            time.sleep(0.5)  # be polite to the public API

    return exercises


def main():
    exercises = fetch_all_exercises()
    print(f"\nTotal exercises after dedup: {len(exercises)}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(exercises, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT_FILE}")

    # Summary stats
    from collections import Counter
    cats = Counter(e["category_name"] for e in exercises)
    goals = Counter(e["fitness_goal"] for e in exercises)
    diffs = Counter(e["difficulty"] for e in exercises)
    print(f"\nBy category: {dict(cats)}")
    print(f"By goal:     {dict(goals)}")
    print(f"By difficulty: {dict(diffs)}")


if __name__ == "__main__":
    main()
