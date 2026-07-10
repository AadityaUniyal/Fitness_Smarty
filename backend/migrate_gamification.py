"""
Migrate Gamification Tables

This script migrates the existing achievements table to the new gamification schema.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import database
from sqlalchemy import text

def migrate_gamification():
    """Migrate gamification tables"""
    print("🔄 Migrating Gamification Tables...")
    print("=" * 60)
    
    db = database.SessionLocal()
    
    try:
        # Drop the old achievements table (old schema)
        print("\n📦 Dropping old achievements table...")
        db.execute(text("DROP TABLE IF EXISTS achievements CASCADE"))
        db.commit()
        print("✅ Old table dropped")
        
        # Import models to create new tables
        from app import models
        
        print("\n🏗️  Creating new gamification tables...")
        models.Base.metadata.create_all(bind=database.engine)
        print("✅ New tables created")
        
        # Initialize the system
        print("\n✨ Seeding achievements and badges...")
        from app.gamification_service import GamificationService
        
        GamificationService.initialize_system(db)
        
        # Show stats
        achievement_count = db.query(models.Achievement).count()
        badge_count = db.query(models.Badge).count()
        
        print("\n" + "=" * 60)
        print("📈 Migration Complete!")
        print(f"   • Achievements: {achievement_count}")
        print(f"   • Badges: {badge_count}")
        print("=" * 60)
        
        print("\n🎉 Gamification system is ready!")
        
    except Exception as e:
        print(f"❌ Migration Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    migrate_gamification()
