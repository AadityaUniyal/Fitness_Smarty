"""
Comprehensive Production Seeding Script for Neon PostgreSQL

Database Connection:
postgresql://neondb_owner:npg_VscPlK6OM9vm@ep-morning-term-aymxxv10-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require

Seeds:
1. Exercise Categories & Detailed Exercise Items (Calorie burn per min/rep, duration, sets, reps, goal mappings, muscle groups, equipment, difficulty, MET values)
2. Female-Specific Exercises (Menstrual, Follicular, Ovulatory, Luteal phase support)
3. Food Categories & Detailed Food Items (Macros per 100g, elite rating, goal alignment, prep times)
4. Achievements & Badges (Gamification system templates)
5. Subscription Plans (Free, Pro Athletic, Elite AI Neural)

Usage:
python seed_neon_database.py
"""

import sys
import os
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app import models

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

NEON_DATABASE_URL = os.getenv("DATABASE_URL")
if not NEON_DATABASE_URL:
    try:
        from app.config import settings
        NEON_DATABASE_URL = settings.DATABASE_URL
    except Exception:
        raise ValueError("DATABASE_URL environment variable is not set. Please set DATABASE_URL in backend/.env")

# Clean SSL mode query params if needed for SQLAlchemy compatibility
if "channel_binding" in NEON_DATABASE_URL:
    NEON_DATABASE_URL = NEON_DATABASE_URL.replace("&channel_binding=require", "").replace("channel_binding=require&", "")


engine = create_engine(NEON_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# =====================================================================
# 1. COMPREHENSIVE EXERCISE CATALOG
# =====================================================================
EXERCISE_CATALOG = {
    "Chest & Push": [
        # Beginner
        {
            "name": "Push-ups", "muscle": "Chest", "group": "Push", "sec_muscles": ["Triceps", "Front Delts", "Core"],
            "difficulty": "Beginner", "equipment": "Bodyweight", "pattern": "Push", "goal": "muscle_gain",
            "sets": 3, "reps": "10-15", "set_duration": 45, "rest": 60, "cal_min": 7.5, "cal_rep": 0.5, "cal_set": 12.0, "met": 6.0,
            "desc": "Classic bodyweight upper-body press. Keep core tight and lower chest to floor level."
        },
        {
            "name": "Incline Push-ups", "muscle": "Upper Chest", "group": "Push", "sec_muscles": ["Triceps", "Front Delts"],
            "difficulty": "Beginner", "equipment": "Bench", "pattern": "Push", "goal": "fat_loss",
            "sets": 3, "reps": "12-15", "set_duration": 40, "rest": 60, "cal_min": 6.0, "cal_rep": 0.4, "cal_set": 9.5, "met": 5.0,
            "desc": "Hands elevated on a bench or bar. Excellent progression for building pressing endurance."
        },
        {
            "name": "Dumbbell Floor Press", "muscle": "Chest", "group": "Push", "sec_muscles": ["Triceps"],
            "difficulty": "Beginner", "equipment": "Dumbbell", "pattern": "Push", "goal": "muscle_gain",
            "sets": 3, "reps": "10-12", "set_duration": 45, "rest": 60, "cal_min": 6.5, "cal_rep": 0.6, "cal_set": 11.0, "met": 5.5,
            "desc": "Safe chest pressing on the floor preventing shoulder hyperextension."
        },
        # Intermediate
        {
            "name": "Barbell Bench Press", "muscle": "Chest", "group": "Push", "sec_muscles": ["Triceps", "Front Delts"],
            "difficulty": "Intermediate", "equipment": "Barbell", "pattern": "Push", "goal": "strength",
            "sets": 4, "reps": "8-10", "set_duration": 45, "rest": 90, "cal_min": 9.0, "cal_rep": 1.2, "cal_set": 16.0, "met": 7.5,
            "desc": "The primary upper-body strength movement. Retract scapula and drive bar up dynamically."
        },
        {
            "name": "Incline Dumbbell Bench Press", "muscle": "Upper Chest", "group": "Push", "sec_muscles": ["Front Delts", "Triceps"],
            "difficulty": "Intermediate", "equipment": "Dumbbell", "pattern": "Push", "goal": "muscle_gain",
            "sets": 4, "reps": "8-12", "set_duration": 50, "rest": 90, "cal_min": 8.5, "cal_rep": 1.1, "cal_set": 15.0, "met": 7.0,
            "desc": "Targets upper clavicular chest head. Maintain a 30-degree incline for optimal angle."
        },
        {
            "name": "Cable Chest Flyes", "muscle": "Chest", "group": "Push", "sec_muscles": ["Front Delts"],
            "difficulty": "Intermediate", "equipment": "Cable", "pattern": "Isolation", "goal": "muscle_gain",
            "sets": 3, "reps": "12-15", "set_duration": 45, "rest": 60, "cal_min": 7.0, "cal_rep": 0.8, "cal_set": 11.5, "met": 6.0,
            "desc": "Continuous cable tension stretching and contracting chest muscle fibers."
        },
        # Advanced
        {
            "name": "Weighted Dips", "muscle": "Lower Chest", "group": "Push", "sec_muscles": ["Triceps", "Front Delts"],
            "difficulty": "Advanced", "equipment": "Bodyweight", "pattern": "Push", "goal": "strength",
            "sets": 4, "reps": "6-8", "set_duration": 40, "rest": 120, "cal_min": 11.0, "cal_rep": 1.8, "cal_set": 18.0, "met": 8.5,
            "desc": "High-intensity compound chest movement. Lean torso forward to emphasize chest over triceps."
        },
        {
            "name": "Plyometric Clapping Push-ups", "muscle": "Chest", "group": "Push", "sec_muscles": ["Triceps", "Core"],
            "difficulty": "Advanced", "equipment": "Bodyweight", "pattern": "Push", "goal": "athletic",
            "sets": 3, "reps": "8-10", "set_duration": 30, "rest": 90, "cal_min": 12.0, "cal_rep": 1.5, "cal_set": 16.0, "met": 9.0,
            "desc": "Explosive power exercise building fast-twitch muscle fiber recruitment."
        }
    ],

    "Back & Pull": [
        # Beginner
        {
            "name": "Lat Pulldown", "muscle": "Lats", "group": "Pull", "sec_muscles": ["Biceps", "Rear Delts"],
            "difficulty": "Beginner", "equipment": "Cable", "pattern": "Pull", "goal": "muscle_gain",
            "sets": 3, "reps": "10-12", "set_duration": 45, "rest": 60, "cal_min": 6.5, "cal_rep": 0.6, "cal_set": 10.5, "met": 5.5,
            "desc": "Essential vertical pulling movement for upper back breadth."
        },
        {
            "name": "Seated Cable Row", "muscle": "Mid Back", "group": "Pull", "sec_muscles": ["Rhomboids", "Biceps"],
            "difficulty": "Beginner", "equipment": "Cable", "pattern": "Pull", "goal": "muscle_gain",
            "sets": 3, "reps": "10-12", "set_duration": 45, "rest": 60, "cal_min": 6.5, "cal_rep": 0.6, "cal_set": 10.5, "met": 5.5,
            "desc": "Builds back thickness. Drive elbows back while keeping chest proud."
        },
        # Intermediate
        {
            "name": "Single-Arm Dumbbell Row", "muscle": "Lats", "group": "Pull", "sec_muscles": ["Rhomboids", "Biceps"],
            "difficulty": "Intermediate", "equipment": "Dumbbell", "pattern": "Pull", "goal": "muscle_gain",
            "sets": 4, "reps": "8-12", "set_duration": 50, "rest": 75, "cal_min": 8.0, "cal_rep": 1.0, "cal_set": 14.0, "met": 6.8,
            "desc": "Unilateral rowing movement allowing full lat stretch and contraction range."
        },
        {
            "name": "Pull-ups", "muscle": "Lats", "group": "Pull", "sec_muscles": ["Biceps", "Rear Delts", "Core"],
            "difficulty": "Intermediate", "equipment": "Bodyweight", "pattern": "Pull", "goal": "athletic",
            "sets": 4, "reps": "6-10", "set_duration": 40, "rest": 90, "cal_min": 9.5, "cal_rep": 1.5, "cal_set": 15.5, "met": 8.0,
            "desc": "King of upper body bodyweight pulling movements."
        },
        {
            "name": "Barbell Bent-Over Row", "muscle": "Mid Back", "group": "Pull", "sec_muscles": ["Lats", "Erectors", "Biceps"],
            "difficulty": "Intermediate", "equipment": "Barbell", "pattern": "Pull", "goal": "strength",
            "sets": 4, "reps": "8-10", "set_duration": 45, "rest": 90, "cal_min": 9.0, "cal_rep": 1.4, "cal_set": 15.0, "met": 7.5,
            "desc": "Heavy compound row building dense back muscle mass and spinal stability."
        },
        # Advanced
        {
            "name": "Conventional Barbell Deadlift", "muscle": "Hamstrings", "group": "Pull", "sec_muscles": ["Glutes", "Erectors", "Lats", "Traps"],
            "difficulty": "Advanced", "equipment": "Barbell", "pattern": "Hinge", "goal": "strength",
            "sets": 4, "reps": "5", "set_duration": 40, "rest": 120, "cal_min": 12.0, "cal_rep": 2.5, "cal_set": 22.0, "met": 9.5,
            "desc": "Ultimate full-body posterior chain exercise. Pull weight off floor with neutral spine."
        },
        {
            "name": "Weighted Chin-ups", "muscle": "Lats", "group": "Pull", "sec_muscles": ["Biceps"],
            "difficulty": "Advanced", "equipment": "Bodyweight", "pattern": "Pull", "goal": "strength",
            "sets": 4, "reps": "5-8", "set_duration": 40, "rest": 120, "cal_min": 11.0, "cal_rep": 2.0, "cal_set": 18.0, "met": 8.5,
            "desc": "Supinated grip pull-up with added belt weight targeting lats and arm strength."
        }
    ],

    "Legs & Lower Body": [
        # Beginner
        {
            "name": "Bodyweight Squats", "muscle": "Quads", "group": "Legs", "sec_muscles": ["Glutes", "Hamstrings"],
            "difficulty": "Beginner", "equipment": "Bodyweight", "pattern": "Squat", "goal": "fat_loss",
            "sets": 3, "reps": "15-20", "set_duration": 45, "rest": 60, "cal_min": 7.0, "cal_rep": 0.5, "cal_set": 11.0, "met": 5.5,
            "desc": "Fundamental knee-dominant movement pattern. Squat deep keeping knees aligned over toes."
        },
        {
            "name": "Glute Bridges", "muscle": "Glutes", "group": "Legs", "sec_muscles": ["Hamstrings", "Core"],
            "difficulty": "Beginner", "equipment": "Bodyweight", "pattern": "Hinge", "goal": "muscle_gain",
            "sets": 3, "reps": "15-20", "set_duration": 45, "rest": 60, "cal_min": 5.5, "cal_rep": 0.4, "cal_set": 9.0, "met": 4.5,
            "desc": "Isolation movement targeting glute activation and hip extension."
        },
        {
            "name": "Walking Lunges", "muscle": "Quads", "group": "Legs", "sec_muscles": ["Glutes", "Calves"],
            "difficulty": "Beginner", "equipment": "Bodyweight", "pattern": "Lunge", "goal": "fat_loss",
            "sets": 3, "reps": "12 per leg", "set_duration": 50, "rest": 60, "cal_min": 8.0, "cal_rep": 0.6, "cal_set": 13.0, "met": 6.5,
            "desc": "Unilateral leg exercise improving hip flexibility, stability, and quad conditioning."
        },
        # Intermediate
        {
            "name": "Dumbbell Goblet Squat", "muscle": "Quads", "group": "Legs", "sec_muscles": ["Glutes", "Core"],
            "difficulty": "Intermediate", "equipment": "Dumbbell", "pattern": "Squat", "goal": "muscle_gain",
            "sets": 4, "reps": "10-12", "set_duration": 50, "rest": 75, "cal_min": 8.5, "cal_rep": 1.0, "cal_set": 14.5, "met": 7.0,
            "desc": "Hold weight at chest. Excellent front-loaded squat teaching upright torso mechanics."
        },
        {
            "name": "Romanian Deadlift (RDL)", "muscle": "Hamstrings", "group": "Legs", "sec_muscles": ["Glutes", "Erectors"],
            "difficulty": "Intermediate", "equipment": "Barbell", "pattern": "Hinge", "goal": "muscle_gain",
            "sets": 4, "reps": "8-10", "set_duration": 45, "rest": 90, "cal_min": 8.5, "cal_rep": 1.2, "cal_set": 15.0, "met": 7.0,
            "desc": "Hip hinge exercise stretching and building hamstrings and glute max strength."
        },
        {
            "name": "Bulgarian Split Squat", "muscle": "Quads", "group": "Legs", "sec_muscles": ["Glutes", "Hamstrings"],
            "difficulty": "Intermediate", "equipment": "Dumbbell", "pattern": "Lunge", "goal": "muscle_gain",
            "sets": 3, "reps": "10 per leg", "set_duration": 60, "rest": 90, "cal_min": 9.0, "cal_rep": 1.2, "cal_set": 16.0, "met": 7.5,
            "desc": "Rear foot elevated on bench. High-demand unilateral leg builder."
        },
        # Advanced
        {
            "name": "Barbell Back Squat", "muscle": "Quads", "group": "Legs", "sec_muscles": ["Glutes", "Hamstrings", "Core"],
            "difficulty": "Advanced", "equipment": "Barbell", "pattern": "Squat", "goal": "strength",
            "sets": 4, "reps": "6-8", "set_duration": 50, "rest": 120, "cal_min": 10.5, "cal_rep": 2.0, "cal_set": 20.0, "met": 8.8,
            "desc": "The cornerstone leg building exercise. Load bar across traps and squat below parallel."
        },
        {
            "name": "Barbell Front Squat", "muscle": "Quads", "group": "Legs", "sec_muscles": ["Upper Back", "Abs"],
            "difficulty": "Advanced", "equipment": "Barbell", "pattern": "Squat", "goal": "athletic",
            "sets": 4, "reps": "6-8", "set_duration": 45, "rest": 120, "cal_min": 11.0, "cal_rep": 2.1, "cal_set": 21.0, "met": 9.0,
            "desc": "Bar resting on front delts. Demands high thoracic extension and heavy quad drive."
        }
    ],

    "Shoulders & Delts": [
        # Beginner
        {
            "name": "Dumbbell Lateral Raises", "muscle": "Side Delts", "group": "Push", "sec_muscles": ["Traps"],
            "difficulty": "Beginner", "equipment": "Dumbbell", "pattern": "Isolation", "goal": "muscle_gain",
            "sets": 3, "reps": "12-15", "set_duration": 45, "rest": 60, "cal_min": 5.0, "cal_rep": 0.4, "cal_set": 8.5, "met": 4.5,
            "desc": "Isolates the side deltoid head for shoulder width."
        },
        {
            "name": "Dumbbell Front Raises", "muscle": "Front Delts", "group": "Push", "sec_muscles": ["Upper Chest"],
            "difficulty": "Beginner", "equipment": "Dumbbell", "pattern": "Isolation", "goal": "muscle_gain",
            "sets": 3, "reps": "12-15", "set_duration": 45, "rest": 60, "cal_min": 5.0, "cal_rep": 0.4, "cal_set": 8.5, "met": 4.5,
            "desc": "Front deltoid raise building anterior shoulder mass."
        },
        # Intermediate
        {
            "name": "Seated Dumbbell Shoulder Press", "muscle": "Deltoids", "group": "Push", "sec_muscles": ["Triceps", "Traps"],
            "difficulty": "Intermediate", "equipment": "Dumbbell", "pattern": "Push", "goal": "muscle_gain",
            "sets": 4, "reps": "8-12", "set_duration": 45, "rest": 75, "cal_min": 7.5, "cal_rep": 0.9, "cal_set": 13.0, "met": 6.5,
            "desc": "Heavy overhead press developing shoulder strength and upper body stability."
        },
        {
            "name": "Face Pulls", "muscle": "Rear Delts", "group": "Pull", "sec_muscles": ["Rhomboids", "Rotator Cuff"],
            "difficulty": "Intermediate", "equipment": "Cable", "pattern": "Isolation", "goal": "maintenance",
            "sets": 3, "reps": "15-20", "set_duration": 45, "rest": 60, "cal_min": 6.0, "cal_rep": 0.5, "cal_set": 9.5, "met": 5.0,
            "desc": "Essential posture and shoulder health exercise pulling rope to eye level."
        },
        # Advanced
        {
            "name": "Standing Barbell Overhead Press (OHP)", "muscle": "Deltoids", "group": "Push", "sec_muscles": ["Triceps", "Core"],
            "difficulty": "Advanced", "equipment": "Barbell", "pattern": "Push", "goal": "strength",
            "sets": 4, "reps": "5-8", "set_duration": 40, "rest": 120, "cal_min": 9.5, "cal_rep": 1.6, "cal_set": 17.0, "met": 8.0,
            "desc": "Strict overhead press pushing barbell from collarbone overhead."
        }
    ],

    "Arms (Biceps & Triceps)": [
        # Beginner
        {
            "name": "Dumbbell Bicep Curls", "muscle": "Biceps", "group": "Pull", "sec_muscles": ["Forearms"],
            "difficulty": "Beginner", "equipment": "Dumbbell", "pattern": "Isolation", "goal": "muscle_gain",
            "sets": 3, "reps": "12-15", "set_duration": 45, "rest": 60, "cal_min": 4.5, "cal_rep": 0.35, "cal_set": 7.5, "met": 4.0,
            "desc": "Classic bicep flexion isolating arm flexor muscles."
        },
        {
            "name": "Bench Tricep Dips", "muscle": "Triceps", "group": "Push", "sec_muscles": ["Front Delts"],
            "difficulty": "Beginner", "equipment": "Bench", "pattern": "Push", "goal": "fat_loss",
            "sets": 3, "reps": "12-15", "set_duration": 40, "rest": 60, "cal_min": 5.5, "cal_rep": 0.4, "cal_set": 9.0, "met": 4.8,
            "desc": "Bodyweight tricep dip off bench edge."
        },
        # Intermediate
        {
            "name": "EZ-Bar Preacher Curls", "muscle": "Biceps", "group": "Pull", "sec_muscles": ["Brachialis"],
            "difficulty": "Intermediate", "equipment": "Barbell", "pattern": "Isolation", "goal": "muscle_gain",
            "sets": 3, "reps": "10-12", "set_duration": 45, "rest": 60, "cal_min": 5.5, "cal_rep": 0.5, "cal_set": 9.0, "met": 4.8,
            "desc": "Strict bicep isolation preventing momentum using preacher bench pad."
        },
        {
            "name": "Cable Tricep Pushdowns", "muscle": "Triceps", "group": "Push", "sec_muscles": ["Forearms"],
            "difficulty": "Intermediate", "equipment": "Cable", "pattern": "Isolation", "goal": "muscle_gain",
            "sets": 3, "reps": "12-15", "set_duration": 45, "rest": 60, "cal_min": 5.5, "cal_rep": 0.5, "cal_set": 9.0, "met": 4.8,
            "desc": "Lock elbows to torso and extend arms straight down to contract triceps."
        },
        # Advanced
        {
            "name": "Skull Crushers (Lying Tricep Extension)", "muscle": "Triceps", "group": "Push", "sec_muscles": ["Forearms"],
            "difficulty": "Advanced", "equipment": "Barbell", "pattern": "Isolation", "goal": "muscle_gain",
            "sets": 4, "reps": "8-10", "set_duration": 45, "rest": 75, "cal_min": 6.5, "cal_rep": 0.7, "cal_set": 11.0, "met": 5.5,
            "desc": "Heavy tricep builder lowering EZ-bar to forehead on bench."
        }
    ],

    "Abs & Core": [
        # Beginner
        {
            "name": "Plank", "muscle": "Abs/Core", "group": "Core", "sec_muscles": ["Glutes", "Shoulders"],
            "difficulty": "Beginner", "equipment": "Bodyweight", "pattern": "Isometric", "goal": "fat_loss",
            "sets": 3, "reps": "45 sec", "set_duration": 45, "rest": 45, "cal_min": 6.0, "cal_rep": 0.4, "cal_set": 9.0, "met": 5.0,
            "desc": "Isometric core pillar stability hold."
        },
        {
            "name": "Crunches", "muscle": "Abs/Core", "group": "Core", "sec_muscles": [],
            "difficulty": "Beginner", "equipment": "Bodyweight", "pattern": "Flexion", "goal": "fat_loss",
            "sets": 3, "reps": "15-20", "set_duration": 45, "rest": 45, "cal_min": 5.0, "cal_rep": 0.3, "cal_set": 7.5, "met": 4.0,
            "desc": "Flexion crunch isolating rectus abdominis."
        },
        # Intermediate
        {
            "name": "Hanging Knee Raises", "muscle": "Lower Abs", "group": "Core", "sec_muscles": ["Hip Flexors"],
            "difficulty": "Intermediate", "equipment": "Bodyweight", "pattern": "Flexion", "goal": "muscle_gain",
            "sets": 3, "reps": "12-15", "set_duration": 45, "rest": 60, "cal_min": 7.0, "cal_rep": 0.6, "cal_set": 11.0, "met": 6.0,
            "desc": "Hang from pull-up bar and raise knees up to chest level."
        },
        {
            "name": "Russian Twists", "muscle": "Obliques", "group": "Core", "sec_muscles": ["Abs/Core"],
            "difficulty": "Intermediate", "equipment": "Dumbbell", "pattern": "Rotation", "goal": "fat_loss",
            "sets": 3, "reps": "20 total", "set_duration": 45, "rest": 45, "cal_min": 7.0, "cal_rep": 0.4, "cal_set": 10.5, "met": 6.0,
            "desc": "Seated rotational exercise targeting oblique muscles."
        },
        # Advanced
        {
            "name": "Ab Wheel Rollouts", "muscle": "Abs/Core", "group": "Core", "sec_muscles": ["Lats", "Shoulders"],
            "difficulty": "Advanced", "equipment": "Ab Wheel", "pattern": "Anti-Extension", "goal": "strength",
            "sets": 4, "reps": "10-12", "set_duration": 45, "rest": 75, "cal_min": 9.0, "cal_rep": 1.2, "cal_set": 14.5, "met": 7.5,
            "desc": "High-intensity anti-extension core exercise rolling out to full extension."
        }
    ],

    "Cardio & Conditioning": [
        # Beginner
        {
            "name": "Brisk Walking", "muscle": "Full Body", "group": "Cardio", "sec_muscles": ["Calves"],
            "difficulty": "Beginner", "equipment": "None", "pattern": "Cardio", "goal": "fat_loss",
            "sets": 1, "reps": "20 mins", "set_duration": 1200, "rest": 0, "cal_min": 4.5, "cal_rep": 0.0, "cal_set": 90.0, "met": 3.8,
            "desc": "Low-impact steady-state cardio for metabolic conditioning."
        },
        {
            "name": "Jump Rope", "muscle": "Calves", "group": "Cardio", "sec_muscles": ["Shoulders", "Core"],
            "difficulty": "Beginner", "equipment": "Jump Rope", "pattern": "Cardio", "goal": "fat_loss",
            "sets": 3, "reps": "2 mins", "set_duration": 120, "rest": 60, "cal_min": 12.0, "cal_rep": 0.1, "cal_set": 24.0, "met": 10.0,
            "desc": "Fast cadence agility and cardiovascular conditioning."
        },
        # Intermediate
        {
            "name": "Rowing Machine Sprints", "muscle": "Full Body", "group": "Cardio", "sec_muscles": ["Lats", "Quads"],
            "difficulty": "Intermediate", "equipment": "Machine", "pattern": "Cardio", "goal": "athletic",
            "sets": 4, "reps": "500m", "set_duration": 120, "rest": 90, "cal_min": 13.0, "cal_rep": 0.0, "cal_set": 26.0, "met": 10.5,
            "desc": "Full-body anaerobic rowing intervals."
        },
        # Advanced
        {
            "name": "HIIT Sprints", "muscle": "Full Body", "group": "Cardio", "sec_muscles": ["Quads", "Hamstrings"],
            "difficulty": "Advanced", "equipment": "None", "pattern": "Cardio", "goal": "fat_loss",
            "sets": 6, "reps": "30 sec sprint", "set_duration": 30, "rest": 60, "cal_min": 15.0, "cal_rep": 0.0, "cal_set": 18.0, "met": 12.5,
            "desc": "Maximum output sprint intervals maximizing post-exercise oxygen consumption (EPOC)."
        },
        {
            "name": "Burpees", "muscle": "Full Body", "group": "Cardio", "sec_muscles": ["Chest", "Quads", "Core"],
            "difficulty": "Advanced", "equipment": "Bodyweight", "pattern": "Cardio", "goal": "fat_loss",
            "sets": 4, "reps": "15-20", "set_duration": 60, "rest": 60, "cal_min": 14.0, "cal_rep": 1.5, "cal_set": 22.0, "met": 11.0,
            "desc": "Full-body explosive pushup to jump conditioning movement."
        }
    ]
}

# =====================================================================
# 2. FEMALE-SPECIFIC EXERCISES
# =====================================================================
FEMALE_EXERCISES_DATA = [
    {
        "name": "Pelvic Floor Kegel Holds", "muscle": "Pelvic Floor", "difficulty": "Beginner",
        "equipment": "Bodyweight", "cal_min": 3.0, "cal_rep": 0.1, "phase": "all",
        "desc": "Gentle pelvic floor strengthening and core alignment."
    },
    {
        "name": "Menstrual Phase Soothing Flow", "muscle": "Full Body", "difficulty": "Beginner",
        "equipment": "Yoga Mat", "cal_min": 3.5, "cal_rep": 0.0, "phase": "Menstrual",
        "desc": "Low-intensity stretches reducing menstrual cramps and lower back tension."
    },
    {
        "name": "Follicular Dynamic Strength Flow", "muscle": "Full Body", "difficulty": "Intermediate",
        "equipment": "Dumbbells", "cal_min": 9.0, "cal_rep": 0.8, "phase": "Follicular",
        "desc": "Capitalizes on rising estrogen levels for strength building and energy boost."
    },
    {
        "name": "Ovulatory Peak Power Intervals", "muscle": "Full Body", "difficulty": "Advanced",
        "equipment": "Kettlebell", "cal_min": 13.0, "cal_rep": 1.2, "phase": "Ovulatory",
        "desc": "Maximal performance training during peak strength and energy window."
    },
    {
        "name": "Luteal Phase Pilates Core", "muscle": "Abs/Core", "difficulty": "Intermediate",
        "equipment": "Mat", "cal_min": 6.5, "cal_rep": 0.4, "phase": "Luteal",
        "desc": "Controlled core stabilization avoiding excessive fatigue during high progesterone window."
    }
]

# =====================================================================
# 3. FOOD NUTRITION CATALOG (per 100g)
# =====================================================================
FOOD_CATALOG = {
    "High-Protein Meats & Seafood": [
        {"name": "Chicken Breast (Cooked)", "cal": 165, "p": 31.0, "c": 0.0, "f": 3.6, "elite": True, "goal": "muscle_gain", "prep": 15},
        {"name": "Wild Salmon Fillet", "cal": 206, "p": 22.0, "c": 0.0, "f": 12.0, "elite": True, "goal": "muscle_gain", "prep": 12},
        {"name": "Tuna Steak (Yellowfin)", "cal": 130, "p": 28.0, "c": 0.0, "f": 1.0, "elite": True, "goal": "fat_loss", "prep": 10},
        {"name": "Lean Ground Turkey (93/7)", "cal": 170, "p": 21.0, "c": 0.0, "f": 9.0, "elite": True, "goal": "fat_loss", "prep": 12},
        {"name": "Egg Whites", "cal": 52, "p": 11.0, "c": 0.7, "f": 0.2, "elite": True, "goal": "fat_loss", "prep": 5},
    ],
    "Plant-Based Proteins": [
        {"name": "Fresh Cottage Cheese / Paneer", "cal": 296, "p": 18.0, "c": 1.5, "f": 24.0, "elite": True, "goal": "muscle_gain", "prep": 5},
        {"name": "Organic Tofu (Firm)", "cal": 83, "p": 10.0, "c": 2.0, "f": 5.0, "elite": True, "goal": "maintenance", "prep": 10},
        {"name": "Yellow Lentils / Dal (Cooked)", "cal": 116, "p": 9.0, "c": 20.0, "f": 0.4, "elite": True, "goal": "fat_loss", "prep": 20},
        {"name": "Boiled Chickpeas (Kabuli Chana)", "cal": 164, "p": 8.9, "c": 27.0, "f": 2.6, "elite": True, "goal": "athletic", "prep": 15},
    ],
    "Complex Carbs & Whole Grains": [
        {"name": "Rolled Oats", "cal": 389, "p": 16.9, "c": 66.0, "f": 6.9, "elite": True, "goal": "muscle_gain", "prep": 5},
        {"name": "Brown Basmati Rice (Cooked)", "cal": 123, "p": 2.7, "c": 26.0, "f": 1.0, "elite": True, "goal": "fat_loss", "prep": 20},
        {"name": "Baked Sweet Potato", "cal": 90, "p": 2.0, "c": 21.0, "f": 0.1, "elite": True, "goal": "fat_loss", "prep": 30},
        {"name": "Organic Quinoa (Cooked)", "cal": 120, "p": 4.4, "c": 21.0, "f": 1.9, "elite": True, "goal": "athletic", "prep": 15},
    ],
    "Healthy Fats & Seeds": [
        {"name": "Raw Almonds", "cal": 579, "p": 21.0, "c": 22.0, "f": 50.0, "elite": True, "goal": "maintenance", "prep": 0},
        {"name": "Avocado", "cal": 160, "p": 2.0, "c": 8.5, "f": 14.7, "elite": True, "goal": "maintenance", "prep": 2},
        {"name": "Extra Virgin Olive Oil", "cal": 884, "p": 0.0, "c": 0.0, "f": 100.0, "elite": True, "goal": "maintenance", "prep": 0},
        {"name": "Chia Seeds", "cal": 486, "p": 16.5, "c": 42.0, "f": 30.7, "elite": True, "goal": "athletic", "prep": 0},
    ],
    "Dairy & Fermented Foods": [
        {"name": "Greek Yogurt (Non-Fat)", "cal": 59, "p": 10.0, "c": 3.6, "f": 0.4, "elite": True, "goal": "fat_loss", "prep": 1},
        {"name": "Skimmed Milk", "cal": 35, "p": 3.4, "c": 5.0, "f": 0.1, "elite": False, "goal": "fat_loss", "prep": 0},
    ],
    "Performance Supplements": [
        {"name": "Whey Protein Isolate Powder", "cal": 380, "p": 85.0, "c": 2.5, "f": 1.0, "elite": True, "goal": "muscle_gain", "prep": 1},
        {"name": "Creatine Monohydrate", "cal": 0, "p": 0.0, "c": 0.0, "f": 0.0, "elite": True, "goal": "strength", "prep": 1},
    ]
}

# =====================================================================
# 4. GAMIFICATION TEMPLATES (Achievements & Badges)
# =====================================================================
ACHIEVEMENT_TEMPLATES = [
    {"name": "First Step Champion", "desc": "Logged your first workout session in SMARTY AI.", "cat": "workout", "type": "count", "icon": "🏋️", "rarity": "common", "points": 25, "criteria": {"type": "workout_count", "target": 1}},
    {"name": "Iron Discipline", "desc": "Completed 10 workouts.", "cat": "workout", "type": "count", "icon": "💪", "rarity": "rare", "points": 100, "criteria": {"type": "workout_count", "target": 10}},
    {"name": "Century Club", "desc": "Completed 100 workouts total.", "cat": "workout", "type": "count", "icon": "👑", "rarity": "legendary", "points": 500, "criteria": {"type": "workout_count", "target": 100}},
    {"name": "7-Day Streak Warrior", "desc": "Maintained a 7-day daily activity streak.", "cat": "streak", "type": "streak", "icon": "🔥", "rarity": "rare", "points": 150, "criteria": {"type": "streak_days", "target": 7}},
    {"name": "Hydration Master", "desc": "Hit 3,000ml water goal in a single day.", "cat": "nutrition", "type": "goal", "icon": "💧", "rarity": "common", "points": 50, "criteria": {"type": "hydration_target", "target": 3000}},
    {"name": "Macro Perfectionist", "desc": "Hit daily protein target within 5% precision.", "cat": "nutrition", "type": "goal", "icon": "🎯", "rarity": "epic", "points": 200, "criteria": {"type": "macro_precision", "target": 95}}
]

BADGE_TEMPLATES = [
    {"name": "Bronze Lifter", "desc": "Completed 5 resistance workouts.", "icon": "🥉", "tier": "bronze", "cat": "strength", "points": 50, "reqs": {"workouts": 5}},
    {"name": "Silver Shredder", "desc": "Burned 5,000 total active calories.", "icon": "🥈", "tier": "silver", "cat": "cardio", "points": 150, "reqs": {"calories_burned": 5000}},
    {"name": "Gold Titan", "desc": "Logged 50 high-protein meal logs.", "icon": "🥇", "tier": "gold", "cat": "nutrition", "points": 300, "reqs": {"meal_logs": 50}},
    {"name": "Diamond Beast", "desc": "Achieved level 10 neural status.", "icon": "💎", "tier": "diamond", "cat": "consistency", "points": 1000, "reqs": {"level": 10}}
]

SUBSCRIPTION_PLANS = [
    {"name": "Free Tier", "price_cents": 0, "interval": "month", "desc": "Standard AI workout and nutrition tracking features."},
    {"name": "Pro Athletic", "price_cents": 1499, "interval": "month", "desc": "Advanced Gemini AI coach, YOLO vision scanning, & FemmeCare cycle sync."},
    {"name": "Elite AI Neural", "price_cents": 11999, "interval": "year", "desc": "Unlimited SHAP explainable coaching, LSTM weight forecasting, & priority support."}
]


def seed_database():
    logger.info("=====================================================")
    logger.info("🚀 STARTING NEON POSTGRESQL PRODUCTION SEEDING")
    logger.info("=====================================================")

    # Ensure tables exist
    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 1. Seed Exercise Categories & Items
        logger.info("\n🏋️ Seeding Exercise Categories & Professional Items...")
        for cat_name, items in EXERCISE_CATALOG.items():
            category = db.query(models.ExerciseCategory).filter(models.ExerciseCategory.name == cat_name).first()
            if not category:
                category = models.ExerciseCategory(
                    name=cat_name,
                    description=f"Professional exercise library for {cat_name}"
                )
                db.add(category)
                db.commit()
                db.refresh(category)

            for ex in items:
                existing = db.query(models.ExerciseItem).filter(
                    models.ExerciseItem.name == ex["name"]
                ).first()

                if not existing:
                    exercise = models.ExerciseItem(
                        category_id=category.id,
                        name=ex["name"],
                        targeted_muscle=ex["muscle"],
                        muscle_group=ex["group"],
                        secondary_muscles=ex["sec_muscles"],
                        difficulty=ex["difficulty"],
                        equipment=ex["equipment"],
                        movement_pattern=ex["pattern"],
                        avg_set_duration_sec=ex["set_duration"],
                        avg_rest_sec=ex["rest"],
                        default_sets=ex["sets"],
                        default_reps=ex["reps"],
                        est_calories_per_set=ex["cal_set"],
                        calories_per_min=ex["cal_min"],
                        calories_per_rep=ex["cal_rep"],
                        met_value=ex["met"],
                        follicular_suitability=1.0,
                        luteal_suitability=0.8,
                        fitness_goal=ex["goal"],
                        description=ex["desc"]
                    )
                    db.add(exercise)
        db.commit()
        logger.info("  ✅ Exercises catalog seeded successfully.")

        # 2. Seed Female-Specific Exercises
        logger.info("\n👩 Seeding Female-Specific Exercises...")
        female_category = db.query(models.ExerciseCategory).filter(models.ExerciseCategory.name == "Female Health & Cycle Support").first()
        if not female_category:
            female_category = models.ExerciseCategory(
                name="Female Health & Cycle Support",
                description="Hormonal cycle phase-aware exercises for women"
            )
            db.add(female_category)
            db.commit()
            db.refresh(female_category)

        for ex in FEMALE_EXERCISES_DATA:
            existing = db.query(models.FemaleExerciseItem).filter(
                models.FemaleExerciseItem.name == ex["name"]
            ).first()

            if not existing:
                female_ex = models.FemaleExerciseItem(
                    category_id=female_category.id,
                    name=ex["name"],
                    targeted_muscle=ex["muscle"],
                    difficulty=ex["difficulty"],
                    equipment=ex["equipment"],
                    calories_per_min=ex["cal_min"],
                    calories_per_rep=ex["cal_rep"],
                    suitable_cycle_phase=ex["phase"],
                    description=ex["desc"]
                )
                db.add(female_ex)

            # Also ensure it exists in general ExerciseItem for unified lookup
            gen_existing = db.query(models.ExerciseItem).filter(models.ExerciseItem.name == ex["name"]).first()
            if not gen_existing:
                db.add(models.ExerciseItem(
                    category_id=female_category.id,
                    name=ex["name"],
                    targeted_muscle=ex["muscle"],
                    muscle_group="Core",
                    difficulty=ex["difficulty"],
                    equipment=ex["equipment"],
                    calories_per_min=ex["cal_min"],
                    calories_per_rep=ex["cal_rep"],
                    fitness_goal="maintenance",
                    description=ex["desc"]
                ))
        db.commit()
        logger.info("  ✅ Female exercises seeded successfully.")

        # 3. Seed Food Categories & Items
        logger.info("\n🍎 Seeding Food Categories & Nutrition Database...")
        for cat_name, foods in FOOD_CATALOG.items():
            food_cat = db.query(models.FoodCategory).filter(models.FoodCategory.name == cat_name).first()
            if not food_cat:
                food_cat = models.FoodCategory(
                    name=cat_name,
                    description=f"Nutrient database for {cat_name}"
                )
                db.add(food_cat)
                db.commit()
                db.refresh(food_cat)

            for food_data in foods:
                existing = db.query(models.FoodItem).filter(models.FoodItem.name == food_data["name"]).first()
                if not existing:
                    db.add(models.FoodItem(
                        category_id=food_cat.id,
                        name=food_data["name"],
                        calories=food_data["cal"],
                        protein=food_data["p"],
                        carbs=food_data["c"],
                        fats=food_data["f"],
                        is_elite=food_data["elite"],
                        recommended_for_goal=food_data["goal"],
                        prep_time_minutes=food_data["prep"]
                    ))
        db.commit()
        logger.info("  ✅ Food catalog seeded successfully.")

        # 4. Seed Achievements & Badges
        logger.info("\n🏆 Seeding Gamification Achievements & Badges...")
        for ach in ACHIEVEMENT_TEMPLATES:
            existing = db.query(models.Achievement).filter(models.Achievement.name == ach["name"]).first()
            if not existing:
                db.add(models.Achievement(
                    name=ach["name"],
                    description=ach["desc"],
                    category=ach["cat"],
                    achievement_type=ach["type"],
                    icon=ach["icon"],
                    rarity=ach["rarity"],
                    points=ach["points"],
                    criteria=ach["criteria"]
                ))

        for badge in BADGE_TEMPLATES:
            existing = db.query(models.Badge).filter(models.Badge.name == badge["name"]).first()
            if not existing:
                db.add(models.Badge(
                    name=badge["name"],
                    description=badge["desc"],
                    icon=badge["icon"],
                    tier=badge["tier"],
                    category=badge["cat"],
                    points=badge["points"],
                    requirements=badge["reqs"]
                ))
        db.commit()
        logger.info("  ✅ Gamification templates seeded successfully.")

        # 5. Seed Subscription Plans
        logger.info("\n💳 Seeding Subscription Plans...")
        for plan in SUBSCRIPTION_PLANS:
            existing = db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.name == plan["name"]).first()
            if not existing:
                db.add(models.SubscriptionPlan(
                    name=plan["name"],
                    price_cents=plan["price_cents"],
                    billing_interval=plan["interval"],
                    description=plan["desc"]
                ))
        db.commit()
        logger.info("  ✅ Subscription plans seeded successfully.")

        # Verification summary
        ex_count = db.query(models.ExerciseItem).count()
        female_ex_count = db.query(models.FemaleExerciseItem).count()
        food_count = db.query(models.FoodItem).count()
        ach_count = db.query(models.Achievement).count()
        badge_count = db.query(models.Badge).count()
        plan_count = db.query(models.SubscriptionPlan).count()

        logger.info("\n=====================================================")
        logger.info("📊 NEON POSTGRESQL SEEDING VERIFICATION")
        logger.info("=====================================================")
        logger.info(f"  • Total Exercises: {ex_count}")
        logger.info(f"  • Female-Specific Exercises: {female_ex_count}")
        logger.info(f"  • Total Food Items: {food_count}")
        logger.info(f"  • Achievements Templates: {ach_count}")
        logger.info(f"  • Badge Templates: {badge_count}")
        logger.info(f"  • Subscription Plans: {plan_count}")
        logger.info("=====================================================")
        logger.info("✅ ALL SEEDING COMPLETED CLEANLY WITH ZERO ERRORS!")
        logger.info("=====================================================")

    except Exception as e:
        logger.error(f"❌ Error during database seeding: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
