"""
Initialize Database Tables

Creates all tables defined in models.py if they don't exist
"""

import os
import secrets
from app.database import engine, seed_exercise_database, seed_nutrition_database
from app import models
from app.database import SessionLocal
from app.models import EnhancedUser
from app.auth import PasswordHasher

print("="*70)
print("  DATABASE INITIALIZATION")
print("="*70)
print()

# Create all tables
print("Dropping existing tables to clean schema...")
models.Base.metadata.drop_all(bind=engine)
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

print("Seeding default admin user...")
db = SessionLocal()
try:
    admin_password = os.getenv("ADMIN_PASSWORD")
    generated = False
    if not admin_password:
        admin_password = secrets.token_urlsafe(16)
        generated = True
        
    admin = db.query(EnhancedUser).filter(EnhancedUser.email == "admin@smarty.ai").first()
    if not admin:
        admin = EnhancedUser(
            username="admin",
            email="admin@smarty.ai",
            hashed_password=PasswordHasher.hash_password(admin_password),
            is_admin=True
        )
        db.add(admin)
        db.commit()
        if generated:
            print("=" * 70)
            print("SECURITY NOTICE: No ADMIN_PASSWORD environment variable specified.")
            print("A secure random password has been generated for default admin user:")
            print("  Email:    admin@smarty.ai")
            print(f"  Password: {admin_password}")
            print("Please save this password securely. It will not be displayed again.")
            print("=" * 70)
        else:
            print("Default admin user (admin@smarty.ai) created successfully with ADMIN_PASSWORD from environment!")
    else:
        print("Default admin user already exists.")
except Exception as e:
    print(f"Failed to seed default admin: {e}")
finally:
    db.close()

print("="*70)
print("Database initialization complete!")
print("="*70)
print()
print("You can now start the backend server:")
print("  python -m uvicorn main:app --reload")
