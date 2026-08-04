"""
Seed Data Script for Smarty AI Fitness Recommender

Seeds exercises, food database, and creates default admin user using
ADMIN_PASSWORD from environment variables (or secure random fallback if omitted).
"""

import os
import secrets
import logging
from app.database import SessionLocal, seed_exercise_database, seed_nutrition_database
from app.models import EnhancedUser
from app.auth import PasswordHasher

logger = logging.getLogger(__name__)


def seed_admin_user(db=None):
    """Seed default admin user with ADMIN_PASSWORD env var or random fallback."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        admin_password = os.getenv("ADMIN_PASSWORD")
        generated = False
        if not admin_password:
            admin_password = secrets.token_urlsafe(16)
            generated = True

        admin = (
            db.query(EnhancedUser)
            .filter(EnhancedUser.email == "admin@smarty.ai")
            .first()
        )
        if not admin:
            admin = EnhancedUser(
                username="admin",
                email="admin@smarty.ai",
                hashed_password=PasswordHasher.hash_password(admin_password),
                is_admin=True,
            )
            db.add(admin)
            db.commit()
            if generated:
                print("=" * 70)
                print(
                    "SECURITY NOTICE: No ADMIN_PASSWORD environment variable specified."
                )
                print(
                    "A secure random password has been generated for default admin account:"
                )
                print("  Email:    admin@smarty.ai")
                print(f"  Password: {admin_password}")
                print(
                    "Please save this password securely. It will not be shown again."
                )
                print("=" * 70)
            else:
                print(
                    "Default admin user (admin@smarty.ai) created successfully with ADMIN_PASSWORD from environment!"
                )
        else:
            print("Default admin user (admin@smarty.ai) already exists.")
    except Exception as e:
        print(f"Failed to seed default admin: {e}")
    finally:
        if close_db:
            db.close()


def main():
    print("=" * 70)
    print("  SEEDING SMARTY AI DATABASE")
    print("=" * 70)
    print()
    print("Seeding exercise library...")
    seed_exercise_database()
    print()
    print("Seeding food library...")
    seed_nutrition_database()
    print()
    print("Seeding default admin user...")
    seed_admin_user()
    print()
    print("=" * 70)
    print("Seeding complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
