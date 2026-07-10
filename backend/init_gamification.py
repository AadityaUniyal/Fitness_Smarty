"""
Initialize Gamification System

Run this script once to set up the gamification system:
- Creates all necessary database tables
- Seeds achievements and badges

Usage:
    python init_gamification.py
"""

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import database, models
from app.gamification_service import GamificationService
from sqlalchemy import inspect


def check_tables_exist():
    """Check if gamification tables exist"""
    inspector = inspect(database.engine)
    existing_tables = inspector.get_table_names()
    
    gamification_tables = [
        'user_streaks',
        'achievements',
        'user_achievements',
        'badges',
        'user_badges',
        'user_points'
    ]
    
    missing_tables = [t for t in gamification_tables if t not in existing_tables]
    
    return missing_tables


def init_gamification():
    """Initialize the gamification system"""
    print("🎮 Initializing Gamification System...")
    print("=" * 60)
    
    # Check for missing tables
    missing = check_tables_exist()
    
    if missing:
        print(f"\n⚠️  Missing tables detected: {', '.join(missing)}")
        print("Creating tables...")
        
        # Create all tables
        models.Base.metadata.create_all(bind=database.engine)
        print("✅ Tables created successfully!")
    else:
        print("✅ All gamification tables already exist")
    
    # Initialize achievements and badges
    print("\n📊 Seeding achievements and badges...")
    
    db = database.SessionLocal()
    try:
        GamificationService.initialize_system(db)
        print("✅ Gamification system initialized successfully!")
        
        # Show stats
        achievement_count = db.query(models.Achievement).count()
        badge_count = db.query(models.Badge).count()
        
        print("\n" + "=" * 60)
        print("📈 System Statistics:")
        print(f"   • Achievements: {achievement_count}")
        print(f"   • Badges: {badge_count}")
        print("=" * 60)
        
        print("\n🎉 Gamification system is ready!")
        print("\nNext steps:")
        print("1. Restart your backend server")
        print("2. Visit /docs to see the new /api/gamification endpoints")
        print("3. Test with: GET /api/gamification/achievements")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    init_gamification()
