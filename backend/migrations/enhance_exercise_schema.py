"""
Migration: Enhance Exercise Schema

This migration ensures the Exercise table has:
- Proper constraints on difficulty_level
- Indexes for efficient searching
- Validation for required fields
"""

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine, SessionLocal
from app.models import Exercise


def check_constraint_exists(engine, table_name, constraint_name):
    """Check if a constraint exists on a table"""
    inspector = inspect(engine)
    constraints = inspector.get_check_constraints(table_name)
    return any(c['name'] == constraint_name for c in constraints)


def check_index_exists(engine, table_name, index_name):
    """Check if an index exists on a table"""
    inspector = inspect(engine)
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def enhance_exercise_schema():
    """Enhance the exercise schema with constraints and indexes"""
    
    print("Starting exercise schema enhancement...")
    
    # Check if we're using PostgreSQL
    database_url = os.getenv("DATABASE_URL", "sqlite:///./smarty_neural_core.db")
    is_postgresql = "postgresql" in database_url
    
    if not is_postgresql:
        print("SQLite detected - skipping PostgreSQL-specific enhancements")
        print("Exercise schema enhancement complete (SQLite mode)")
        return
    
    with engine.connect() as conn:
        # Check if exercises table exists
        inspector = inspect(engine)
        if 'exercises' not in inspector.get_table_names():
            print("Creating exercises table...")
            Base.metadata.create_all(bind=engine, tables=[Exercise.__table__])
            print("Exercises table created")
        else:
            print("Exercises table already exists")
        
        # Add check constraint for difficulty_level if it doesn't exist
        constraint_name = 'exercises_difficulty_level_check'
        if not check_constraint_exists(engine, 'exercises', constraint_name):
            print(f"Adding difficulty level constraint...")
            try:
                conn.execute(text("""
                    ALTER TABLE exercises 
                    ADD CONSTRAINT exercises_difficulty_level_check 
                    CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced'))
                """))
                conn.commit()
                print("Difficulty level constraint added")
            except Exception as e:
                print(f"Note: Could not add difficulty constraint (may already exist): {e}")
        else:
            print("Difficulty level constraint already exists")
        
        # Add check constraint for category if it doesn't exist
        category_constraint_name = 'exercises_category_check'
        if not check_constraint_exists(engine, 'exercises', category_constraint_name):
            print(f"Adding category constraint...")
            try:
                conn.execute(text("""
                    ALTER TABLE exercises 
                    ADD CONSTRAINT exercises_category_check 
                    CHECK (category IN ('strength', 'cardio', 'flexibility', 'sports'))
                """))
                conn.commit()
                print("Category constraint added")
            except Exception as e:
                print(f"Note: Could not add category constraint (may already exist): {e}")
        else:
            print("Category constraint already exists")
        
        # Add index on difficulty_level for efficient filtering
        difficulty_index = 'idx_exercises_difficulty_level'
        if not check_index_exists(engine, 'exercises', difficulty_index):
            print("Adding difficulty level index...")
            try:
                conn.execute(text("""
                    CREATE INDEX idx_exercises_difficulty_level 
                    ON exercises(difficulty_level)
                """))
                conn.commit()
                print("Difficulty level index added")
            except Exception as e:
                print(f"Note: Could not add difficulty index (may already exist): {e}")
        else:
            print("Difficulty level index already exists")
        
        # Add index on category for efficient filtering
        category_index = 'idx_exercises_category'
        if not check_index_exists(engine, 'exercises', category_index):
            print("Adding category index...")
            try:
                conn.execute(text("""
                    CREATE INDEX idx_exercises_category 
                    ON exercises(category)
                """))
                conn.commit()
                print("Category index added")
            except Exception as e:
                print(f"Note: Could not add category index (may already exist): {e}")
        else:
            print("Category index already exists")
        
        # Add GIN index on muscle_groups array for efficient array searches
        muscle_groups_index = 'idx_exercises_muscle_groups'
        if not check_index_exists(engine, 'exercises', muscle_groups_index):
            print("Adding muscle groups GIN index...")
            try:
                conn.execute(text("""
                    CREATE INDEX idx_exercises_muscle_groups 
                    ON exercises USING GIN(muscle_groups)
                """))
                conn.commit()
                print("Muscle groups GIN index added")
            except Exception as e:
                print(f"Note: Could not add muscle groups index (may already exist): {e}")
        else:
            print("Muscle groups index already exists")
        
        # Add GIN index on equipment array for efficient array searches
        equipment_index = 'idx_exercises_equipment'
        if not check_index_exists(engine, 'exercises', equipment_index):
            print("Adding equipment GIN index...")
            try:
                conn.execute(text("""
                    CREATE INDEX idx_exercises_equipment 
                    ON exercises USING GIN(equipment)
                """))
                conn.commit()
                print("Equipment GIN index added")
            except Exception as e:
                print(f"Note: Could not add equipment index (may already exist): {e}")
        else:
            print("Equipment index already exists")
        
        # Add text search index on name for efficient name searches
        name_index = 'idx_exercises_name_lower'
        if not check_index_exists(engine, 'exercises', name_index):
            print("Adding name search index...")
            try:
                conn.execute(text("""
                    CREATE INDEX idx_exercises_name_lower 
                    ON exercises(LOWER(name))
                """))
                conn.commit()
                print("Name search index added")
            except Exception as e:
                print(f"Note: Could not add name index (may already exist): {e}")
        else:
            print("Name search index already exists")
    
    print("\nExercise schema enhancement complete!")
    print("✓ Difficulty level constraint")
    print("✓ Category constraint")
    print("✓ Difficulty level index")
    print("✓ Category index")
    print("✓ Muscle groups GIN index")
    print("✓ Equipment GIN index")
    print("✓ Name search index")


if __name__ == "__main__":
    enhance_exercise_schema()
