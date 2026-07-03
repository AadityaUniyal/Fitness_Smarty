
from app.database import engine
from app.models import Base, EnhancedUser, ExerciseCategory, ExerciseItem, FoodCategory, FoodItem, MealLog, FoodDetection, WorkoutLog, BiometricReading, ProgressSnapshot, UserProfile, UserGoal, SocialActivity, Achievement, BiometricRecord, FoodTrainingSample, FemaleExerciseItem, MenstrualCycleLog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Manually create tables in order to avoid FK issues."""
    try:
        # Create core tables first
        logger.info("Creating core table: users")
        EnhancedUser.__table__.create(bind=engine, checkfirst=True)
        
        logger.info("Creating core table: exercise_categories")
        ExerciseCategory.__table__.create(bind=engine, checkfirst=True)
        
        logger.info("Creating core table: food_categories")
        FoodCategory.__table__.create(bind=engine, checkfirst=True)
        
        # Create tables that depend on core
        logger.info("Creating dependent tables...")
        tables_to_create = [
            ExerciseItem.__table__,
            FoodItem.__table__,
            MealLog.__table__,
            FoodDetection.__table__,
            WorkoutLog.__table__,
            BiometricReading.__table__,
            ProgressSnapshot.__table__,
            UserProfile.__table__,
            UserGoal.__table__,
            SocialActivity.__table__,
            Achievement.__table__,
            BiometricRecord.__table__,
            FoodTrainingSample.__table__,
            FemaleExerciseItem.__table__,
            MenstrualCycleLog.__table__,
        ]
        
        for table in tables_to_create:
            logger.info(f"Creating table: {table.name}")
            table.create(bind=engine, checkfirst=True)
            
        logger.info("✅ All tables created successfully (or already existed).")
    except Exception as e:
        logger.error(f"❌ Error setting up database: {e}")

if __name__ == "__main__":
    setup_database()
