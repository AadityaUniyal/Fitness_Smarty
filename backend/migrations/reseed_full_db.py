"""
Full DB Reseed Migration Script
================================
Run this script to:
1. Add 'fitness_goal' column to exercise_items (if missing)
2. Clear existing exercise/food seed data
3. Re-seed with the new expanded data (50+ exercises, 65+ foods with per-100g macros and goal tags)

Usage:
    cd backend
    python migrations/reseed_full_db.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app import models

def add_fitness_goal_column():
    """Add fitness_goal column to exercise_items if missing."""
    with engine.connect() as conn:
        try:
            # Check if column exists (SQLite style)
            result = conn.execute(text("PRAGMA table_info(exercise_items)"))
            columns = [row[1] for row in result.fetchall()]
            if "fitness_goal" not in columns:
                conn.execute(text("ALTER TABLE exercise_items ADD COLUMN fitness_goal VARCHAR"))
                conn.commit()
                print("✅ Added fitness_goal column to exercise_items")
            else:
                print("ℹ️  fitness_goal column already exists")
        except Exception as e:
            # PostgreSQL fallback
            try:
                conn.execute(text("""
                    ALTER TABLE exercise_items 
                    ADD COLUMN IF NOT EXISTS fitness_goal VARCHAR
                """))
                conn.commit()
                print("✅ Added fitness_goal column (PostgreSQL)")
            except Exception as e2:
                print(f"Column may already exist: {e2}")


def clear_seed_tables():
    """Clear existing seeded data from exercise and food tables."""
    db = SessionLocal()
    try:
        count_ex = db.query(models.ExerciseItem).count()
        count_cat_ex = db.query(models.ExerciseCategory).count()
        count_food = db.query(models.FoodItem).count()
        count_cat_food = db.query(models.FoodCategory).count()

        print(f"\n📦 Current data in DB:")
        print(f"   Exercise categories: {count_cat_ex} | Exercise items: {count_ex}")
        print(f"   Food categories:     {count_cat_food} | Food items:     {count_food}")

        db.query(models.ExerciseItem).delete()
        db.query(models.ExerciseCategory).delete()
        db.query(models.FoodItem).delete()
        db.query(models.FoodCategory).delete()
        db.commit()
        print("\n🧹 Cleared all exercise and food data.")
    except Exception as e:
        db.rollback()
        print(f"Error clearing tables: {e}")
        raise
    finally:
        db.close()


def reseed():
    from app.database import seed_exercise_database, seed_nutrition_database
    print("\n🌱 Seeding exercise database...")
    seed_exercise_database()
    print("🌱 Seeding food database...")
    seed_nutrition_database()


if __name__ == "__main__":
    print("=" * 55)
    print("  SMARTY DB FULL RESEED MIGRATION")
    print("=" * 55)

    # Step 1: Ensure schema is up to date
    models.Base.metadata.create_all(bind=engine)
    add_fitness_goal_column()

    # Step 2: Clear old seed data
    clear_seed_tables()

    # Step 3: Reseed with new expanded data
    reseed()

    print("\n✅ Migration complete! Your DB now has:")
    db = SessionLocal()
    print(f"   🏋️  Exercise categories: {db.query(models.ExerciseCategory).count()}")
    print(f"   🏋️  Exercises:           {db.query(models.ExerciseItem).count()}")
    print(f"   🥗 Food categories:     {db.query(models.FoodCategory).count()}")
    print(f"   🥗 Food items:          {db.query(models.FoodItem).count()}")
    db.close()
    print("=" * 55)
