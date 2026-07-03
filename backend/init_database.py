"""
Initialize Database Tables

Creates all tables defined in models.py if they don't exist
"""

from app.database import engine, seed_exercise_database, seed_nutrition_database
from app import models

print("="*70)
print("  DATABASE INITIALIZATION")
print("="*70)
print()

# Create all tables
print("Creating tables from models.py...")
models.Base.metadata.create_all(bind=engine)
print("Tables created/verified")
print()

# Seed exercise data
print("Seeding exercise database...")
seed_exercise_database()
print("Exercise data loaded")
print()

# Seed nutrition data
print("Seeding nutrition database...")
seed_nutrition_database()
print()

print("="*70)
print("Database initialization complete!")
print("="*70)
print()
print("You can now start the backend server:")
print("  python -m uvicorn main:app --reload")
