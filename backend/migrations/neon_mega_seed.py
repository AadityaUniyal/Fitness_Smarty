"""
Neon DB Mega Seed — All Tables
================================
Fills: exercises, foods, nutrition_facts, achievements, biometrics,
       biomechanical_faults, workouts, meals, social_feed,
       user_goals, recommendations
Drops: None (keeps all tables, just populates them)
Preserves: all users, enhanced_users, user_profiles, meal_logs, meal_components
"""
import os, sys, uuid, random
from datetime import datetime, timedelta

NEON_URL = os.getenv("DATABASE_URL")
if not NEON_URL:
    raise ValueError("DATABASE_URL environment variable is required to run the mega seed script.")
from sqlalchemy import create_engine, text
engine = create_engine(NEON_URL, pool_pre_ping=True)

def run():
    print("=== NEON MEGA SEED START ===")
    with engine.connect() as conn:
        # Load real user IDs for FK use
        user_ids_str  = [r[0] for r in conn.execute(text("SELECT id FROM users LIMIT 50")).fetchall()]
        euser_ids     = [r[0] for r in conn.execute(text("SELECT id FROM enhanced_users LIMIT 30")).fetchall()]
        food_uuids    = [r[0] for r in conn.execute(text("SELECT id FROM foods")).fetchall()]

        print(f"  users(str)={len(user_ids_str)}  enhanced_users={len(euser_ids)}  existing foods={len(food_uuids)}")

        # ─── 1. exercises (UUID table) ─────────────────────────────────
        print("\n[1] Seeding exercises (UUID table)...")
        conn.execute(text("DELETE FROM exercises"))
        exercise_data = [
            # Fat Loss
            ("Burpees",             "cardio",     ["full_body"],        ["none"],              "intermediate", "Start standing, drop to plank, push-up, jump back up.", "Keep core tight throughout."),
            ("Jump Rope",           "cardio",     ["full_body","calves"],["jump_rope"],         "beginner",    "Swing rope overhead, jump with both feet.", "Land softly on balls of feet."),
            ("Mountain Climbers",   "cardio",     ["core","shoulders"], ["none"],              "beginner",    "From plank, drive knees alternately to chest rapidly.", "Keep hips level."),
            ("High Knees",          "cardio",     ["legs","core"],      ["none"],              "beginner",    "Run in place lifting knees to hip height.", "Pump arms for intensity."),
            ("Battle Ropes",        "cardio",     ["arms","core"],      ["battle_ropes"],      "intermediate","Alternate arm waves with the ropes.", "Brace core, slight knee bend."),
            ("Treadmill Sprint",    "cardio",     ["legs","glutes"],    ["treadmill"],         "advanced",    "Sprint at max effort for 20-30s, rest, repeat.", "Set incline to 1-2% for realism."),
            ("Cycling Indoor",      "cardio",     ["legs","glutes"],    ["spin_bike"],         "beginner",    "Maintain cadence 80-100 RPM at moderate resistance.", "Keep back straight."),
            ("Rowing Machine",      "cardio",     ["full_body"],        ["rower"],             "intermediate","Drive with legs, lean back, pull handle to chest.", "60% legs, 20% back, 20% arms."),
            ("Box Jumps",           "plyometric", ["legs","glutes"],    ["plyo_box"],          "intermediate","Explode upward onto box, land softly, step down.", "Land with soft knees."),
            ("Kickboxing Combos",   "cardio",     ["full_body"],        ["none"],              "intermediate","Jab-cross-hook-kick combinations.", "Stay light on feet."),
            ("Stair Climber",       "cardio",     ["legs","glutes"],    ["stair_machine"],     "beginner",    "Continuous stepping on machine.", "Don't lean on handrails."),
            ("Elliptical",          "cardio",     ["full_body"],        ["elliptical"],        "beginner",    "Maintain smooth stride at moderate resistance.", "Great low-impact option."),
            # Muscle Building
            ("Barbell Back Squat",  "strength",   ["quads","glutes","hamstrings"],["barbell","rack"],"advanced","Bar on traps, squat to parallel, drive through heels.", "Knees track over toes."),
            ("Deadlift",            "strength",   ["back","glutes","hamstrings"],["barbell"],   "advanced",   "Hinge at hips, grip bar, drive hips forward to stand.", "Flat back throughout."),
            ("Bench Press",         "strength",   ["chest","triceps","shoulders"],["barbell","bench"],"intermediate","Lower bar to mid-chest, press up powerfully.", "Retract shoulder blades."),
            ("Overhead Press",      "strength",   ["shoulders","triceps"],["barbell"],          "intermediate","Press bar from shoulders overhead to lockout.", "Brace core, avoid back arch."),
            ("Pull-Ups",            "strength",   ["back","biceps"],    ["pull_up_bar"],       "intermediate","Dead hang, pull chin above bar, lower controlled.", "Full range of motion."),
            ("Bent-Over Row",       "strength",   ["back","biceps"],    ["barbell"],           "intermediate","Hinge forward, pull bar to lower ribcage.", "Keep back parallel to floor."),
            ("Dumbbell Curl",       "strength",   ["biceps"],           ["dumbbells"],         "beginner",    "Curl dumbbell from hip to shoulder, squeeze at top.", "No swinging."),
            ("Tricep Pushdown",     "strength",   ["triceps"],          ["cable_machine"],     "beginner",    "Push cable bar down until arms fully extended.", "Keep elbows pinned to sides."),
            ("Leg Press",           "strength",   ["quads","glutes"],   ["leg_press_machine"], "beginner",    "Push platform away, lower to 90 degrees.", "Feet shoulder-width apart."),
            ("Incline DB Press",    "strength",   ["upper_chest","shoulders"],["dumbbells","bench"],"intermediate","Press at 30-45 incline for upper chest emphasis.", "Control the negative."),
            ("Romanian Deadlift",   "strength",   ["hamstrings","glutes"],["barbell"],         "intermediate","Hinge hips back, lower bar along legs, feel hamstring stretch.", "Soft knees."),
            ("Cable Lateral Raise", "strength",   ["side_delts"],       ["cable_machine"],     "beginner",    "Raise cable to shoulder height, controlled descent.", "Slight forward lean."),
            ("Chest Dips",          "strength",   ["chest","triceps"],  ["dip_bars"],          "intermediate","Lean forward and lower until stretch felt, press up.", "Go below 90 degrees."),
            ("Face Pulls",          "strength",   ["rear_delts","traps"],["cable_machine"],    "beginner",    "Pull rope to face level, elbows flared.", "External rotation at top."),
            ("Hack Squat",          "strength",   ["quads"],            ["hack_squat_machine"],"intermediate","Controlled squat on machine with feet forward.", "Full depth if knees allow."),
            ("Lat Pulldown",        "strength",   ["back","biceps"],    ["cable_machine"],     "beginner",    "Pull bar to upper chest, lean slightly back.", "Drive elbows down."),
            ("Seated Cable Row",    "strength",   ["back","biceps"],    ["cable_machine"],     "beginner",    "Pull handle to abdomen, squeeze shoulder blades.", "Upright posture."),
            ("Bulgarian Split Squat","strength",  ["quads","glutes"],   ["dumbbells","bench"], "intermediate","Rear foot elevated, lunge down per leg.", "Front knee tracks over toe."),
            # Athletic
            ("Power Clean",         "olympic",    ["full_body"],        ["barbell"],           "advanced",    "Explosive pull from floor to front rack position.", "Triple extension: ankle, knee, hip."),
            ("Hang Snatch",         "olympic",    ["full_body"],        ["barbell"],           "advanced",    "Explosive pull from hang, catch overhead.", "Requires shoulder flexibility."),
            ("Kettlebell Swing",    "ballistic",  ["glutes","core"],    ["kettlebell"],        "intermediate","Hip hinge drive, swing KB to shoulder height.", "Power from hips, not arms."),
            ("Med Ball Slam",       "ballistic",  ["core","shoulders"], ["med_ball"],          "intermediate","Raise ball overhead, slam to floor with force.", "Full body extension then compression."),
            ("Depth Jumps",         "plyometric", ["legs"],             ["plyo_box"],          "advanced",    "Step off box, immediately jump upon landing.", "Minimise ground contact time."),
            ("Broad Jumps",         "plyometric", ["legs","glutes"],    ["none"],              "intermediate","Horizontal jump for max distance.", "Swing arms for momentum."),
            ("Agility Ladder",      "agility",    ["legs","core"],      ["agility_ladder"],    "intermediate","Rapid foot patterns through ladder on the ground.", "Stay on toes."),
            ("Sprint Intervals",    "cardio",     ["legs"],             ["track"],             "advanced",    "90-100% effort sprints with full recovery.", "Drive knees high, pump arms."),
            # Maintenance/Mobility
            ("Brisk Walking",       "cardio",     ["legs"],             ["none"],              "beginner",    "Walk at conversational-but-elevated pace for 30+ min.", "Swing arms naturally."),
            ("Yoga Vinyasa",        "flexibility",["full_body"],        ["yoga_mat"],          "beginner",    "Flowing Sun Salutation: plank, cobra, downward dog.", "Breathe with each movement."),
            ("Swimming Laps",       "cardio",     ["full_body"],        ["pool"],              "beginner",    "Freestyle or breaststroke at comfortable pace.", "Low joint impact."),
            ("Plank Hold",          "core",       ["core","shoulders"], ["none"],              "beginner",    "Hold push-up position on forearms for time.", "Avoid sagging hips."),
            ("Foam Rolling",        "recovery",   ["full_body"],        ["foam_roller"],       "beginner",    "Roll over muscle groups 60s each, pause on sore spots.", "Avoid rolling joints."),
            ("Light Jogging",       "cardio",     ["legs"],             ["none"],              "beginner",    "Easy conversational pace for 20-40 min.", "Land midfoot."),
            ("Static Stretching",   "flexibility",["full_body"],        ["none"],              "beginner",    "Hold each stretch 30s, major muscle groups.", "Post-workout only."),
            ("Tai Chi",             "balance",    ["full_body"],        ["none"],              "beginner",    "Slow flowing movements improving balance and mindfulness.", "Focus on breath."),
            ("Resistance Bands",    "strength",   ["full_body"],        ["resistance_bands"],  "beginner",    "Light banded exercises: rows, curls, presses.", "Good for travel."),
            ("Hip Flexor Stretch",  "flexibility",["hip_flexors"],      ["none"],              "beginner",    "Kneeling lunge stretch, hold 30-45s each side.", "Keep core braced."),
            ("Glute Bridge",        "strength",   ["glutes","hamstrings"],["none"],            "beginner",    "Lying supine, drive hips to ceiling, squeeze glutes.", "Pause at top 2 seconds."),
            ("Bird Dog",            "core",       ["core","lower_back"],["none"],              "beginner",    "From all-fours, extend opposite arm and leg.", "Keep spine neutral."),
            ("Dead Bug",            "core",       ["core"],             ["none"],              "beginner",    "Supine, lower opposite arm and leg slowly.", "Press lower back into floor."),
        ]
        for name, cat, muscles, equip, diff, instr, safety in exercise_data:
            conn.execute(text("""
                INSERT INTO exercises (id, name, category, muscle_groups, equipment, difficulty_level, instructions, safety_notes, created_at)
                VALUES (:id, :name, :cat, :muscles, :equip, :diff, :instr, :safety, :ts)
            """), {
                "id": str(uuid.uuid4()), "name": name, "cat": cat,
                "muscles": muscles, "equip": equip, "diff": diff,
                "instr": instr, "safety": safety, "ts": datetime.utcnow()
            })
        conn.commit()
        print(f"   -> {len(exercise_data)} exercises inserted.")

        # ─── 2. foods + nutrition_facts (UUID linked) ──────────────────
        print("\n[2] Seeding foods + nutrition_facts...")
        # Build list: (name, brand, category, serving_g, serving_desc, cal, pro, carb, fat, fiber, sugar, sodium, potassium, calcium, iron, vit_c, vit_d)
        food_entries = [
            ("Chicken Breast (cooked)",  None,       "Proteins",     100, "100g",      165, 31.0, 0.0,  3.6,  0.0, 0.0,  74,  256, 11, 0.7, 0.0, 0.0),
            ("Salmon Fillet (wild)",     None,       "Proteins",     100, "100g",      208, 22.0, 0.0, 13.0,  0.0, 0.0,  59,  363, 12, 0.4, 0.0,16.0),
            ("Whole Egg",                None,       "Dairy & Eggs", 60,  "1 large",   155, 13.0, 1.1, 11.0,  0.0, 1.0, 124,  126, 56, 1.8, 0.0, 2.0),
            ("Oatmeal (cooked)",         None,       "Grains",       240, "1 cup",      68,  2.4,12.0,  1.4,  1.7, 0.6,   2,   61,  9, 0.7, 0.0, 0.0),
            ("Brown Rice (cooked)",      None,       "Grains",       195, "1 cup",     216,  4.5,45.0,  1.8,  3.5, 0.0,  10,  84, 20, 0.8, 0.0, 0.0),
            ("Sweet Potato (baked)",     None,       "Vegetables",   150, "1 medium",  130,  2.4,30.0,  0.2,  4.5,6.2,  41, 542, 43, 0.9,19.6, 0.0),
            ("Avocado",                  None,       "Healthy Fats", 150, "1 medium",  240,  3.0,12.8, 22.0,  9.8, 0.4,  11, 728, 18, 0.8,15.0, 0.0),
            ("Greek Yogurt (0% fat)",    "Chobani",  "Dairy & Eggs", 170, "6oz cup",   100, 17.0, 6.0,  0.0,  0.0, 5.0,  65,  240,200, 0.0, 0.0, 0.0),
            ("Almonds",                  None,       "Healthy Fats", 28,  "1oz",       164,  6.0, 6.1, 14.2,  3.5, 1.2,   0,  200, 76, 1.1, 0.0, 0.0),
            ("Banana",                   None,       "Fruits",       118, "1 medium",  105,  1.3,27.0,  0.4,  3.1,14.4,   1,  422, 6,  0.3, 9.0, 0.0),
            ("Blueberries",              None,       "Fruits",       148, "1 cup",      84,  1.1,21.4,  0.5,  3.6,14.7,   1,  114, 9,  0.4,14.4, 0.0),
            ("Lentils (cooked)",         None,       "Proteins",     198, "1 cup",     230, 17.9,39.8,  0.8, 15.6, 3.6,   4,  731, 38, 6.6, 2.9, 0.0),
            ("Quinoa (cooked)",          None,       "Grains",       185, "1 cup",     222,  8.1,39.4,  3.6,  5.2, 1.6,  13,  318, 31, 2.8, 0.0, 0.0),
            ("Tofu (firm)",              None,       "Proteins",     126, "3oz",        87,  9.4, 2.2,  4.8,  0.6, 0.5,  11,  149,350, 2.7, 0.0, 0.0),
            ("Cottage Cheese (low fat)", None,       "Dairy & Eggs", 226, "1 cup",     206, 28.0, 8.2,  4.5,  0.0, 7.0, 764,  217,187, 0.2, 0.0, 0.0),
            ("Whey Protein Powder",      "Optimum",  "Supplements",  30,  "1 scoop",   120, 24.0, 3.0,  1.0,  0.0, 1.0, 130,  180,150, 0.4, 0.0, 0.0),
            ("Peanut Butter (natural)",  None,       "Healthy Fats", 32,  "2 tbsp",    190,  8.0, 7.0, 16.0,  2.0, 3.0, 140,  200, 14, 0.6, 0.0, 0.0),
            ("Chia Seeds",               None,       "Healthy Fats", 28,  "1oz",       138,  4.7,12.0,  8.7, 10.6, 0.0,   5,  115,179, 2.2, 1.2, 0.0),
            ("Spinach (raw)",            None,       "Vegetables",   30,  "1 cup",       7,  0.9, 1.1,  0.1,  0.7, 0.1,  24,  167, 30, 0.8, 8.4, 0.0),
            ("Broccoli (steamed)",       None,       "Vegetables",   148, "1 cup",      54,  3.7,11.2,  0.6,  5.1, 2.7,  64,  457, 62, 1.0,101.1,0.0),
            ("White Rice (cooked)",      None,       "Grains",       186, "1 cup",     242,  4.4,53.4,  0.4,  0.6, 0.0,   0,   55, 16, 0.4, 0.0, 0.0),
            ("Dal (yellow lentil)",      None,       "Indian",       150, "3/4 cup",   174, 13.5,30.0,  0.6, 11.3, 2.0,   3,  550, 57, 4.5, 2.2, 0.0),
            ("Paneer",                   None,       "Indian",       100, "100g",      265, 18.0, 3.6, 20.0,  0.0, 3.0,   8,   83,480, 0.2, 0.0, 0.0),
            ("Roti (whole wheat)",       None,       "Indian",       40,  "1 roti",   106,  3.6,20.8,  1.5,  2.6, 0.0, 180,   80, 16, 1.1, 0.0, 0.0),
            ("Rajma (kidney beans)",     None,       "Indian",       170, "3/4 cup",  216, 14.8,38.8,  0.9, 12.0, 0.6,   4,  713, 62, 3.9, 2.0, 0.0),
            ("Dark Chocolate 85%",       "Lindt",    "Treats",       40,  "1.5oz",    239,  3.1,18.4, 17.0,  5.6,10.4,   5,  206, 28, 4.6, 0.0, 0.0),
            ("Green Tea",                None,       "Beverages",    240, "1 cup",       2,  0.0, 0.0,  0.0,  0.0, 0.0,   2,   21, 2,  0.0,  0.0, 0.0),
            ("Gatorade (Sport)",         "Gatorade", "Beverages",    591, "20oz",      140,  0.0,36.0,  0.0,  0.0,34.0, 270,   75, 0,  0.0,  0.0, 0.0),
            ("Casein Protein Powder",    "Optimum",  "Supplements",  33,  "1 scoop",   120, 24.0, 4.0,  1.0,  1.0, 2.0, 230,  420,500, 0.0,  0.0, 0.0),
            ("Tuna (canned water)",      None,       "Proteins",     142, "5oz can",   130, 30.0, 0.0,  0.5,  0.0, 0.0, 320,  450, 15, 1.3,  0.0, 0.0),
        ]
        new_food_ids = []
        for entry in food_entries:
            name,brand,cat,serv_g,serv_desc,cal,pro,carb,fat,fiber,sugar,sodium,potassium,calcium,iron,vit_c,vit_d = entry
            food_id = str(uuid.uuid4())
            new_food_ids.append((food_id, cal, pro, carb, fat, fiber, sugar, sodium, potassium, calcium, iron, vit_c, vit_d))
            conn.execute(text("""
                INSERT INTO foods (id, name, brand, category, serving_size_g, serving_description, created_at, updated_at)
                VALUES (:id, :name, :brand, :cat, :sg, :sd, :ts, :ts)
                ON CONFLICT DO NOTHING
            """), {"id": food_id,"name": name,"brand": brand,"cat": cat,
                   "sg": serv_g,"sd": serv_desc,"ts": datetime.utcnow()})
            conn.execute(text("""
                INSERT INTO nutrition_facts (id, food_id, calories_per_100g, protein_g, carbs_g, fat_g, fiber_g, sugar_g, sodium_mg, potassium_mg, calcium_mg, iron_mg, vitamin_c_mg, vitamin_d_ug, created_at)
                VALUES (:id, :fid, :cal, :pro, :carb, :fat, :fiber, :sugar, :sodium, :pot, :calc, :iron, :vitc, :vitd, :ts)
            """), {"id": str(uuid.uuid4()),"fid": food_id,"cal": cal,"pro": pro,"carb": carb,
                   "fat": fat,"fiber": fiber,"sugar": sugar,"sodium": sodium,"pot": potassium,
                   "calc": calcium,"iron": iron,"vitc": vit_c,"vitd": vit_d,"ts": datetime.utcnow()})
        conn.commit()
        print(f"   -> {len(food_entries)} foods + nutrition_facts inserted.")

        # ─── 3. achievements (linked to users string PK) ──────────────
        print("\n[3] Seeding achievements...")
        conn.execute(text("DELETE FROM achievements"))
        achievement_templates = [
            ("First Workout", "Completed your very first workout session!", "workout"),
            ("10 Workouts", "Completed 10 workouts. You are on a roll!", "milestone"),
            ("Calorie Crusher", "Burned 500+ calories in a single session.", "performance"),
            ("Protein Pro", "Hit your daily protein goal 7 days in a row.", "nutrition"),
            ("Early Bird", "Logged a workout before 7 AM.", "habit"),
            ("Consistency King", "Worked out 5 days in a single week.", "habit"),
            ("Meal Tracker", "Logged 10 meals with photo detection.", "nutrition"),
            ("Squat Beast", "Squatted bodyweight x 1.5 for 5 reps.", "strength"),
            ("Cardio Champion", "Completed 20 cardio sessions.", "endurance"),
            ("Fat Burner", "Lost 2kg since joining.", "body_comp"),
        ]
        for uid in user_ids_str[:20]:
            # Give each user 2-4 random achievements
            for tmpl in random.sample(achievement_templates, random.randint(2, 4)):
                offset = random.randint(1, 60)
                conn.execute(text("""
                    INSERT INTO achievements (user_id, title, description, icon, unlocked_at)
                    VALUES (:uid, :title, :desc, :icon, :ts)
                """), {"uid": uid, "title": tmpl[0], "desc": tmpl[1],
                       "icon": tmpl[2], "ts": datetime.utcnow() - timedelta(days=offset)})
        conn.commit()
        print("   -> achievements seeded.")

        # ─── 4. biometrics (linked to users string PK) ────────────────
        print("\n[4] Seeding biometrics...")
        conn.execute(text("DELETE FROM biometrics"))
        categories = ["weight_kg", "body_fat_pct", "heart_rate_bpm", "steps_count", "sleep_hours", "water_ml"]
        base_vals  = [75.0,         22.0,            70.0,             8000.0,         7.0,           2000.0]
        for uid in user_ids_str[:30]:
            for i, (cat, base) in enumerate(zip(categories, base_vals)):
                for day in range(7):
                    val = base + random.uniform(-base*0.05, base*0.05)
                    conn.execute(text("""
                        INSERT INTO biometrics (user_id, category, value, timestamp)
                        VALUES (:uid, :cat, :val, :ts)
                    """), {"uid": uid, "cat": cat, "val": round(val, 1),
                           "ts": datetime.utcnow() - timedelta(days=day)})
        conn.commit()
        print("   -> biometrics seeded.")

        # ─── 5. biomechanical_faults (linked to users string PK) ──────
        print("\n[5] Seeding biomechanical_faults...")
        conn.execute(text("DELETE FROM biomechanical_faults"))
        fault_data = [
            ("knee", "warning", "Knee caving noted during squat. Strengthen glute medius."),
            ("lower_back", "caution", "Slight lumbar rounding on deadlift. Brace core harder."),
            ("shoulder", "info", "Shoulder impingement risk. Add face pulls and band pull-aparts."),
            ("neck", "info", "Forward head posture. Stretch pecs and strengthen upper back."),
            ("ankle", "warning", "Limited dorsiflexion affecting squat depth. Stretch calves daily."),
            ("hip", "info", "Hip flexor tightness. Add hip flexor stretches post-workout."),
        ]
        for uid in user_ids_str[:15]:
            fault = random.choice(fault_data)
            conn.execute(text("""
                INSERT INTO biomechanical_faults (user_id, part, status, feedback, timestamp)
                VALUES (:uid, :part, :status, :fb, :ts)
            """), {"uid": uid, "part": fault[0], "status": fault[1],
                   "fb": fault[2], "ts": datetime.utcnow() - timedelta(days=random.randint(1,30))})
        conn.commit()
        print("   -> biomechanical_faults seeded.")

        # ─── 6. workouts (linked to users string PK) ──────────────────
        print("\n[6] Seeding workouts...")
        conn.execute(text("DELETE FROM workouts"))
        workout_plans = [
            ("Push Day A",   "high",   60, {"exercises": ["Bench Press","Overhead Press","Incline DB Press","Tricep Pushdown","Lateral Raise"]}),
            ("Pull Day A",   "high",   60, {"exercises": ["Deadlift","Pull-Ups","Bent-Over Row","Dumbbell Curl","Face Pulls"]}),
            ("Leg Day A",    "high",   70, {"exercises": ["Barbell Back Squat","Romanian Deadlift","Leg Press","Calf Raise","Bulgarian Split Squat"]}),
            ("HIIT Cardio",  "sehr",   40, {"exercises": ["Burpees","Mountain Climbers","Box Jumps","Battle Ropes","Jump Rope"]}),
            ("Full Body",    "moderate",55,{"exercises": ["Squat","Bench Press","Bent-Over Row","Overhead Press","Deadlift"]}),
            ("Recovery Day", "low",    30, {"exercises": ["Foam Rolling","Static Stretching","Light Jogging","Yoga Vinyasa"]}),
        ]
        import json
        for uid in user_ids_str[:25]:
            for _ in range(random.randint(3, 6)):
                plan = random.choice(workout_plans)
                conn.execute(text("""
                    INSERT INTO workouts (user_id, plan_data, intensity, duration, timestamp)
                    VALUES (:uid, :plan, :intensity, :dur, :ts)
                """), {"uid": uid, "plan": json.dumps(plan[3]),
                       "intensity": plan[1], "dur": plan[2],
                       "ts": datetime.utcnow() - timedelta(days=random.randint(1, 60))})
        conn.commit()
        print("   -> workouts seeded.")

        # ─── 7. meals (linked to users string PK) ─────────────────────
        print("\n[7] Seeding meals...")
        conn.execute(text("DELETE FROM meals"))
        meal_examples = [
            ("Oatmeal with Banana",          387),
            ("Chicken Rice Bowl",            612),
            ("Protein Shake",                240),
            ("Dal and Roti",                 480),
            ("Egg White Omelette",           210),
            ("Greek Yogurt with Blueberries",185),
            ("Grilled Salmon with Broccoli", 420),
            ("Paneer Sabzi with Roti",       550),
            ("Mixed Sprouts Salad",          180),
            ("Whey Protein + Almonds",       310),
        ]
        for uid in user_ids_str[:25]:
            for _ in range(random.randint(5, 10)):
                meal = random.choice(meal_examples)
                conn.execute(text("""
                    INSERT INTO meals (user_id, food_name, calories, timestamp)
                    VALUES (:uid, :fname, :cal, :ts)
                """), {"uid": uid, "fname": meal[0], "cal": meal[1],
                       "ts": datetime.utcnow() - timedelta(days=random.randint(0, 30),
                                                           hours=random.randint(0,23))})
        conn.commit()
        print("   -> meals seeded.")

        # ─── 8. social_feed ────────────────────────────────────────────
        print("\n[8] Seeding social_feed...")
        conn.execute(text("DELETE FROM social_feed"))
        social_items = [
            ("AadiKumar",   "WORKOUT",  "Just crushed leg day! 5x5 squats at 100kg. No excuses."),
            ("PriyaFit",    "MEAL",     "Meal prepped for the whole week - Dal, rice and veggies!"),
            ("ArjunGains",  "LEVEL_UP", "Reached Level 12! Consistency is the key."),
            ("SunilRunner", "WORKOUT",  "10km run done in 52 minutes. New PR!"),
            ("NehaYoga",    "MILESTONE","30-day yoga streak complete. Mind and body in sync."),
            ("RahulLift",   "WORKOUT",  "Bench press 1RM hit 100kg today. Hard work pays off!"),
            ("MayaSlim",    "MILESTONE","Lost 5kg in 2 months with Smarty. Feeling amazing!"),
            ("KaranBox",    "WORKOUT",  "Kickboxing HIIT session done. Burned 650 kcal!"),
            ("AnanyaRun",   "MEAL",     "Post-run protein: Greek yogurt + blueberries. Perfect recovery."),
            ("VijayStrong", "LEVEL_UP", "Just unlocked the Protein Pro badge. 7-day streak!"),
            ("DeepikaCycle","WORKOUT",  "50km cycling ride completed. Legs are jelly but worth it."),
            ("SumitSwim",   "WORKOUT",  "Morning swim - 40 laps done. Great way to start the day."),
            ("MeenaPower",  "MILESTONE","First pull-up achieved! Months of practice finally paid off."),
            ("RohanFlex",   "WORKOUT",  "Mobility session today. Foam rolling and yoga. Feeling loose."),
            ("AishaFit",    "MEAL",     "Paneer tikka made at home with low-oil recipe. Yum and healthy!"),
        ]
        for item in social_items:
            conn.execute(text("""
                INSERT INTO social_feed (operator_name, activity_type, content, timestamp)
                VALUES (:name, :atype, :content, :ts)
            """), {"name": item[0], "atype": item[1], "content": item[2],
                   "ts": datetime.utcnow() - timedelta(hours=random.randint(1, 72))})
        conn.commit()
        print("   -> social_feed seeded.")

        # ─── 9. user_goals (linked to enhanced_users UUID) ────────────
        print("\n[9] Seeding user_goals...")
        goal_types = [
            ("weight_loss",       80.0,  75.0),
            ("muscle_gain",       65.0,  70.0),
            ("daily_calories",  2200.0,2200.0),
            ("weekly_workouts",    5.0,   5.0),
            ("body_fat_pct",      25.0,  20.0),
        ]
        for euid in euser_ids[:20]:
            goal = random.choice(goal_types)
            target_date = (datetime.utcnow() + timedelta(days=random.randint(30, 90))).date()
            conn.execute(text("""
                INSERT INTO user_goals (id, user_id, goal_type, target_value, current_value, target_date, is_active, created_at, updated_at)
                VALUES (:id, :uid, :gt, :tv, :cv, :td, true, :ts, :ts)
            """), {"id": str(uuid.uuid4()), "uid": str(euid), "gt": goal[0],
                   "tv": goal[1], "cv": goal[2], "td": target_date, "ts": datetime.utcnow()})
        conn.commit()
        print("   -> user_goals seeded.")

        # ─── 10. recommendations (linked to enhanced_users UUID) ───────
        print("\n[10] Seeding recommendations...")
        conn.execute(text("DELETE FROM recommendations"))
        rec_templates = [
            ("meal",     "Boost Your Protein Intake",        "You are averaging 80g protein/day vs your 130g target. Add a whey shake post-workout."),
            ("meal",     "Include More Vegetables",          "Log at least 3 vegetable servings today. Spinach and broccoli are great choices."),
            ("exercise", "Try a Fat Burn Cardio Session",    "Based on your goal, 30 min of HIIT today will put you in an optimal calorie deficit."),
            ("exercise", "Rest Day Recommended",             "You have trained 5 days straight. A recovery session or rest day will maximise gains."),
            ("meal",     "Pre-Workout Meal Suggestion",      "Have banana + peanut butter 60 mins before training for sustained energy."),
            ("exercise", "Strength Plateau Buster",          "Increase your bench press weight by 2.5kg this week to continue progressive overload."),
            ("meal",     "Post-Workout Recovery Window",     "Consume 30-40g protein within 30 minutes post-workout. Whey + banana works great."),
            ("goal",     "You Are 80% to Your Weight Goal",  "Only 1.5kg left to reach your target. Keep your current deficit and stay consistent."),
            ("exercise", "Add Mobility Work",                "Your workout data shows no flexibility sessions. Add 10 min stretching 3x/week."),
            ("meal",     "Hydration Reminder",               "You may be under-hydrated. Aim for 2.5-3 litres of water today for optimal performance."),
        ]
        for euid in euser_ids[:20]:
            for rec in random.sample(rec_templates, random.randint(3, 5)):
                conn.execute(text("""
                    INSERT INTO recommendations (id, user_id, recommendation_type, title, description, confidence_score, is_read, expires_at, created_at)
                    VALUES (:id, :uid, :rtype, :title, :desc, :score, false, :exp, :ts)
                """), {"id": str(uuid.uuid4()), "uid": str(euid), "rtype": rec[0],
                       "title": rec[1], "desc": rec[2],
                       "score": round(random.uniform(0.70, 0.99), 2),
                       "exp": datetime.utcnow() + timedelta(days=7),
                       "ts": datetime.utcnow() - timedelta(hours=random.randint(1, 48))})
        conn.commit()
        print("   -> recommendations seeded.")

    # Final summary
    with engine.connect() as conn:
        tables = ["exercises","foods","nutrition_facts","achievements","biometrics",
                  "biomechanical_faults","workouts","meals","social_feed","user_goals","recommendations"]
        print("\n=== FINAL COUNTS ===")
        for t in tables:
            cnt = conn.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
            print(f"  {t:30s} {cnt}")
    print("\n=== MEGA SEED COMPLETE ===")

if __name__ == "__main__":
    random.seed(42)
    run()
