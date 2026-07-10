import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import declarative_base, sessionmaker
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_APP_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_APP_DIR / ".env")
load_dotenv(_APP_DIR.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smarty_neural_core.db")
TRAINING_DATABASE_URL = os.getenv("TRAINING_DATABASE_URL", DATABASE_URL)


def _sqlite_engine(database_url: str):
    if database_url.startswith("sqlite:///"):
        db_path = database_url.replace("sqlite:///", "", 1)
        if db_path and db_path != ":memory:":
            db_dir = Path(db_path).expanduser().parent
            db_dir.mkdir(parents=True, exist_ok=True)
            # Run self-contained sqlite database migration
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                # User columns
                for col in [
                    "femmecare_enabled",
                    "menopause_mode",
                    "pregnancy_mode",
                    "local_only",
                ]:
                    try:
                        cursor.execute(
                            f"ALTER TABLE users "
                            f"ADD COLUMN {col} BOOLEAN DEFAULT 0"
                        )
                    except sqlite3.OperationalError:
                        pass
                    try:
                        cursor.execute(
                            f"ALTER TABLE user_profiles "
                            f"ADD COLUMN {col} BOOLEAN DEFAULT 0"
                        )
                    except sqlite3.OperationalError:
                        pass
                for col, col_type in [
                    ("full_name", "TEXT"),
                    ("age", "INTEGER"),
                    ("weight_kg", "REAL"),
                    ("height_cm", "REAL"),
                    ("gender", "TEXT"),
                    ("activity_level", "TEXT"),
                    ("primary_goal", "TEXT"),
                    ("version", "INTEGER DEFAULT 1 NOT NULL"),
                    ("created_at", "TEXT"),
                    ("updated_at", "TEXT"),
                ]:
                    try:
                        cursor.execute(
                            f"ALTER TABLE users ADD COLUMN {col} {col_type}"
                        )
                    except sqlite3.OperationalError:
                        pass
                # Menstrual columns
                for col in [
                    "encrypted_symptoms",
                    "encrypted_mood",
                    "encrypted_flow_intensity",
                    "encrypted_notes",
                ]:
                    try:
                        cursor.execute(
                            f"ALTER TABLE menstrual_cycle_logs "
                            f"ADD COLUMN {col} TEXT"
                        )
                    except sqlite3.OperationalError:
                        pass
                conn.commit()
                conn.close()
            except Exception as migration_err:
                print(
                    f"[Migration] Auto schema migration warning: "
                    f"{migration_err}"
                )

    kwargs = {"connect_args": {"check_same_thread": False}}
    if database_url == "sqlite:///:memory:":
        kwargs["poolclass"] = StaticPool

    return create_engine(database_url, **kwargs)


def ensure_compatible_schema(engine_obj) -> None:
    """Apply lightweight additive migrations for local compatibility."""
    try:
        dialect = engine_obj.dialect.name
        with engine_obj.begin() as conn:
            if dialect == "postgresql":
                for statement in [
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                    "femmecare_enabled BOOLEAN DEFAULT FALSE",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                    "menopause_mode BOOLEAN DEFAULT FALSE",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                    "pregnancy_mode BOOLEAN DEFAULT FALSE",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                    "local_only BOOLEAN DEFAULT FALSE",
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                    "version INTEGER DEFAULT 1",
                    "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS "
                    "femmecare_enabled BOOLEAN DEFAULT FALSE",
                    "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS "
                    "menopause_mode BOOLEAN DEFAULT FALSE",
                    "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS "
                    "pregnancy_mode BOOLEAN DEFAULT FALSE",
                    "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS "
                    "local_only BOOLEAN DEFAULT FALSE",
                    "ALTER TABLE menstrual_cycle_logs "
                    "ADD COLUMN IF NOT EXISTS "
                    "encrypted_symptoms TEXT",
                    "ALTER TABLE menstrual_cycle_logs "
                    "ADD COLUMN IF NOT EXISTS "
                    "encrypted_mood TEXT",
                    "ALTER TABLE menstrual_cycle_logs "
                    "ADD COLUMN IF NOT EXISTS "
                    "encrypted_flow_intensity TEXT",
                    "ALTER TABLE menstrual_cycle_logs "
                    "ADD COLUMN IF NOT EXISTS "
                    "encrypted_notes TEXT",
                ]:
                    conn.execute(text(statement))
    except Exception as schema_err:
        logger.warning(f"Schema compatibility migration skipped: {schema_err}")


try:
    if DATABASE_URL.startswith("postgresql"):
        from .neon_config import get_connection_manager
        connection_manager = get_connection_manager()
        engine = connection_manager.engine
        SessionLocal = connection_manager.session_factory
        ensure_compatible_schema(engine)
        if TRAINING_DATABASE_URL != DATABASE_URL:
            training_engine = create_engine(TRAINING_DATABASE_URL)
            TrainingSessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=training_engine
            )
        else:
            TrainingSessionLocal = SessionLocal
    else:
        engine = _sqlite_engine(DATABASE_URL)
        ensure_compatible_schema(engine)
        SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=engine
        )
        if TRAINING_DATABASE_URL != DATABASE_URL:
            training_engine = _sqlite_engine(TRAINING_DATABASE_URL)
            ensure_compatible_schema(training_engine)
            TrainingSessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=training_engine
            )
        else:
            TrainingSessionLocal = SessionLocal
except Exception as e:
    logger.warning(
        f"PostgreSQL connection failed ({e}), falling back to SQLite"
    )
    fallback_url = os.getenv(
        "SQLITE_FALLBACK_URL", "sqlite:///./smarty_neural_core.db"
    )
    engine = _sqlite_engine(fallback_url)
    ensure_compatible_schema(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    TrainingSessionLocal = SessionLocal

Base = declarative_base()


def get_db():
    """Get database session with proper cleanup"""
    if DATABASE_URL.startswith("postgresql"):
        # Use enhanced connection manager
        from .neon_config import get_database_session
        yield from get_database_session()
    else:
        # SQLite fallback
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


def get_training_db():
    """Get session for the training data branch"""
    db = TrainingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_nutrition_database():
    """Injects a comprehensive food library.

    Uses per-100g macros and goal/muscle tags.
    """
    from . import models
    db = SessionLocal()
    try:
        if db.query(models.FoodCategory).first():
            db.close()
            return

        categories = [
            {
                "name": "Proteins",
                "description": (
                    "High-protein foods for muscle building and recovery."
                ),
            },
            {
                "name": "Carbohydrates",
                "description": "Complex carbs for sustained energy.",
            },
            {
                "name": "Healthy Fats",
                "description": "Essential fats for hormones and brain health.",
            },
            {
                "name": "Vegetables",
                "description": "Micronutrient-dense low-cal foods.",
            },
            {
                "name": "Dairy & Eggs",
                "description": "High-bioavailability proteins and fats.",
            },
            {
                "name": "Indian Foods",
                "description": (
                    "Common South Asian foods with accurate macros."
                ),
            },
            {
                "name": "Supplements & Shakes",
                "description": "Whey, plant proteins, creatine, gainers.",
            },
            {
                "name": "Treats",
                "description": "High-calorie indulgent foods (use in moderation).",
            },
        ]
        for cat in categories:
            db.add(models.FoodCategory(**cat))
        db.commit()

        prot_id = db.query(models.FoodCategory).filter_by(name="Proteins").first().id
        carb_id = db.query(models.FoodCategory).filter_by(name="Carbohydrates").first().id
        fat_id = db.query(models.FoodCategory).filter_by(name="Healthy Fats").first().id
        veg_id = db.query(models.FoodCategory).filter_by(name="Vegetables").first().id
        dai_id = db.query(models.FoodCategory).filter_by(name="Dairy & Eggs").first().id
        ind_id = db.query(models.FoodCategory).filter_by(name="Indian Foods").first().id
        shk_id = db.query(models.FoodCategory).filter_by(name="Supplements & Shakes").first().id
        tre_id = db.query(models.FoodCategory).filter_by(name="Treats").first().id

        # All values are per 100g unless noted
        foods = [
            # ============ PROTEINS ============
            {
                "category_id": prot_id, "name": "Chicken Breast",
                "calories": 165, "protein": 31.0, "carbs": 0.0, "fats": 3.6,
                "is_elite": True, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": prot_id, "name": "Turkey Breast",
                "calories": 135, "protein": 30.0, "carbs": 0.0, "fats": 1.0,
                "is_elite": True, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": prot_id, "name": "Salmon (Wild)",
                "calories": 208, "protein": 22.0, "carbs": 0.0, "fats": 13.0,
                "is_elite": True, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": prot_id, "name": "Tuna (canned in water)",
                "calories": 116, "protein": 26.0, "carbs": 0.0, "fats": 1.0,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": prot_id, "name": "Cod Fillet",
                "calories": 82, "protein": 18.0, "carbs": 0.0, "fats": 0.7,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": prot_id, "name": "Shrimp",
                "calories": 99, "protein": 24.0, "carbs": 0.0, "fats": 0.3,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": prot_id, "name": "Lean Ground Beef (95%)",
                "calories": 137, "protein": 21.4, "carbs": 0.0, "fats": 5.0,
                "is_elite": False, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": prot_id, "name": "Bison Steak",
                "calories": 143, "protein": 28.0, "carbs": 0.0, "fats": 2.4,
                "is_elite": True, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": prot_id, "name": "Tofu (Firm)",
                "calories": 83, "protein": 10.0, "carbs": 1.0, "fats": 5.0,
                "is_elite": True, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": prot_id, "name": "Tempeh",
                "calories": 192, "protein": 19.0, "carbs": 9.0, "fats": 11.0,
                "is_elite": True, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": prot_id, "name": "Lentils (cooked)",
                "calories": 116, "protein": 9.0, "carbs": 20.0, "fats": 0.4,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "all"
            },
            {
                "category_id": prot_id, "name": "Black Beans (cooked)",
                "calories": 132, "protein": 8.9, "carbs": 24.0, "fats": 0.5,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": prot_id, "name": "Cottage Cheese",
                "calories": 98, "protein": 11.0, "carbs": 3.4, "fats": 4.3,
                "is_elite": False, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": prot_id, "name": "Pork Tenderloin",
                "calories": 143, "protein": 26.0, "carbs": 0.0, "fats": 3.5,
                "is_elite": False, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": prot_id, "name": "Sardines (in water)",
                "calories": 208, "protein": 25.0, "carbs": 0.0, "fats": 11.5,
                "is_elite": True, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            # ============ CARBOHYDRATES ============
            {
                "category_id": carb_id, "name": "White Rice (cooked)",
                "calories": 130, "protein": 2.7, "carbs": 28.0, "fats": 0.3,
                "is_elite": False, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "legs"
            },
            {
                "category_id": carb_id, "name": "Brown Rice (cooked)",
                "calories": 112, "protein": 2.3, "carbs": 24.0, "fats": 0.8,
                "is_elite": True, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": carb_id, "name": "Sweet Potato (baked)",
                "calories": 86, "protein": 1.6, "carbs": 20.0, "fats": 0.1,
                "is_elite": True, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "legs"
            },
            {
                "category_id": carb_id, "name": "White Potato (boiled)",
                "calories": 77, "protein": 2.0, "carbs": 17.0, "fats": 0.1,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "legs"
            },
            {
                "category_id": carb_id, "name": "Quinoa (cooked)",
                "calories": 120, "protein": 4.4, "carbs": 21.0, "fats": 1.9,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "all"
            },
            {
                "category_id": carb_id, "name": "Oats (dry)",
                "calories": 389, "protein": 17.0, "carbs": 66.0, "fats": 7.0,
                "is_elite": True, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": carb_id, "name": "Oatmeal (cooked)",
                "calories": 68, "protein": 2.4, "carbs": 12.0, "fats": 1.4,
                "is_elite": True, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": carb_id, "name": "Banana",
                "calories": 89, "protein": 1.1, "carbs": 23.0, "fats": 0.3,
                "is_elite": True, "recommended_for_goal": "athletic",
                "target_muscle_group": "legs"
            },
            {
                "category_id": carb_id, "name": "Apple",
                "calories": 52, "protein": 0.3, "carbs": 14.0, "fats": 0.2,
                "is_elite": False, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "general"
            },
            {
                "category_id": carb_id, "name": "Blueberries",
                "calories": 57, "protein": 0.7, "carbs": 14.0, "fats": 0.3,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "general"
            },
            {
                "category_id": carb_id, "name": "Whole Wheat Bread (1 slice)",
                "calories": 80, "protein": 4.0, "carbs": 13.0, "fats": 1.1,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": carb_id, "name": "Chickpeas (cooked)",
                "calories": 164, "protein": 8.9, "carbs": 27.0, "fats": 2.6,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": carb_id, "name": "Corn (cooked)",
                "calories": 96, "protein": 3.4, "carbs": 21.0, "fats": 1.5,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "legs"
            },
            # ============ HEALTHY FATS ============
            {
                "category_id": fat_id, "name": "Avocado",
                "calories": 160, "protein": 2.0, "carbs": 8.5, "fats": 14.7,
                "is_elite": True, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": fat_id, "name": "Extra Virgin Olive Oil",
                "calories": 884, "protein": 0.0, "carbs": 0.0, "fats": 100.0,
                "is_elite": True, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": fat_id, "name": "Walnuts",
                "calories": 654, "protein": 15.2, "carbs": 13.7, "fats": 65.2,
                "is_elite": True, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": fat_id, "name": "Almonds",
                "calories": 579, "protein": 21.0, "carbs": 22.0, "fats": 50.0,
                "is_elite": True, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": fat_id, "name": "Chia Seeds",
                "calories": 486, "protein": 16.5, "carbs": 42.1, "fats": 30.7,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": fat_id, "name": "Flax Seeds",
                "calories": 534, "protein": 18.3, "carbs": 28.9, "fats": 42.2,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": fat_id, "name": "Peanut Butter",
                "calories": 588, "protein": 25.0, "carbs": 20.0, "fats": 50.0,
                "is_elite": False, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": fat_id, "name": "MCT Oil",
                "calories": 900, "protein": 0.0, "carbs": 0.0, "fats": 100.0,
                "is_elite": True, "recommended_for_goal": "athletic",
                "target_muscle_group": "all"
            },
            {
                "category_id": fat_id, "name": "Coconut Oil",
                "calories": 892, "protein": 0.0, "carbs": 0.0, "fats": 100.0,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            # ============ VEGETABLES ============
            {
                "category_id": veg_id, "name": "Broccoli",
                "calories": 34, "protein": 2.8, "carbs": 6.6, "fats": 0.4,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": veg_id, "name": "Spinach",
                "calories": 23, "protein": 2.9, "carbs": 3.6, "fats": 0.4,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": veg_id, "name": "Kale",
                "calories": 49, "protein": 4.3, "carbs": 8.8, "fats": 0.9,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": veg_id, "name": "Asparagus",
                "calories": 20, "protein": 2.2, "carbs": 3.7, "fats": 0.1,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": veg_id, "name": "Bell Pepper",
                "calories": 31, "protein": 1.0, "carbs": 6.0, "fats": 0.3,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "general"
            },
            {
                "category_id": veg_id, "name": "Zucchini",
                "calories": 17, "protein": 1.2, "carbs": 3.1, "fats": 0.3,
                "is_elite": False, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "general"
            },
            {
                "category_id": veg_id, "name": "Cucumber",
                "calories": 15, "protein": 0.7, "carbs": 3.6, "fats": 0.1,
                "is_elite": False, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "general"
            },
            {
                "category_id": veg_id, "name": "Cauliflower",
                "calories": 25, "protein": 1.9, "carbs": 5.0, "fats": 0.3,
                "is_elite": False, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": veg_id, "name": "Mushrooms",
                "calories": 22, "protein": 3.1, "carbs": 3.3, "fats": 0.3,
                "is_elite": False, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "general"
            },
            {
                "category_id": veg_id, "name": "Tomato",
                "calories": 18, "protein": 0.9, "carbs": 3.9, "fats": 0.2,
                "is_elite": False, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "general"
            },
            {
                "category_id": veg_id, "name": "Garlic",
                "calories": 149, "protein": 6.4, "carbs": 33.1, "fats": 0.5,
                "is_elite": True, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            # ============ DAIRY & EGGS ============
            {
                "category_id": dai_id, "name": "Whole Egg",
                "calories": 155, "protein": 13.0, "carbs": 1.1, "fats": 11.0,
                "is_elite": True, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": dai_id, "name": "Egg Whites",
                "calories": 52, "protein": 11.0, "carbs": 1.0, "fats": 0.2,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": dai_id, "name": "Greek Yogurt (0% fat)",
                "calories": 59, "protein": 10.0, "carbs": 3.6, "fats": 0.4,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": dai_id, "name": "Whole Milk",
                "calories": 61, "protein": 3.2, "carbs": 4.8, "fats": 3.3,
                "is_elite": False, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": dai_id, "name": "Skim Milk",
                "calories": 34, "protein": 3.4, "carbs": 4.9, "fats": 0.1,
                "is_elite": False, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "general"
            },
            {
                "category_id": dai_id, "name": "Cheddar Cheese",
                "calories": 403, "protein": 25.0, "carbs": 1.3, "fats": 33.0,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": dai_id, "name": "Mozzarella (low fat)",
                "calories": 254, "protein": 24.0, "carbs": 3.0, "fats": 16.0,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            # ============ INDIAN FOODS ============
            {
                "category_id": ind_id, "name": "Dal (cooked)",
                "calories": 116, "protein": 9.0, "carbs": 20.0, "fats": 0.4,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "all"
            },
            {
                "category_id": ind_id, "name": "Roti (whole wheat)",
                "calories": 265, "protein": 9.0, "carbs": 52.0, "fats": 3.7,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": ind_id, "name": "Paneer",
                "calories": 265, "protein": 18.0, "carbs": 3.6, "fats": 20.0,
                "is_elite": True, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": ind_id, "name": "Rajma (cooked)",
                "calories": 127, "protein": 8.7, "carbs": 22.8, "fats": 0.5,
                "is_elite": True, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": ind_id, "name": "Moong Dal (cooked)",
                "calories": 105, "protein": 7.0, "carbs": 19.0, "fats": 0.4,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": ind_id, "name": "Idli (1 piece ~30g)",
                "calories": 39, "protein": 2.0, "carbs": 8.0, "fats": 0.2,
                "is_elite": False, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "general"
            },
            {
                "category_id": ind_id, "name": "Poha (cooked)",
                "calories": 110, "protein": 2.2, "carbs": 23.0, "fats": 0.9,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": ind_id, "name": "Curd/Yogurt (full fat)",
                "calories": 98, "protein": 3.1, "carbs": 4.7, "fats": 4.3,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "all"
            },
            {
                "category_id": ind_id, "name": "Sprouts (mixed)",
                "calories": 65, "protein": 5.0, "carbs": 9.0, "fats": 0.7,
                "is_elite": True, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "abs"
            },
            {
                "category_id": ind_id, "name": "Sambar (per serving ~200g)",
                "calories": 80, "protein": 4.0, "carbs": 12.0, "fats": 2.0,
                "is_elite": False, "recommended_for_goal": "weight_loss",
                "target_muscle_group": "general"
            },
            # ============ SUPPLEMENTS & SHAKES ============
            {
                "category_id": shk_id, "name": "Whey Protein Powder",
                "calories": 400, "protein": 80.0, "carbs": 8.0, "fats": 5.0,
                "is_elite": True, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": shk_id, "name": "Casein Protein Powder",
                "calories": 380, "protein": 77.0, "carbs": 6.0, "fats": 3.0,
                "is_elite": True, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": shk_id, "name": "Plant Protein Powder",
                "calories": 360, "protein": 70.0, "carbs": 15.0, "fats": 6.0,
                "is_elite": False, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            {
                "category_id": shk_id, "name": "Creatine Monohydrate",
                "calories": 0, "protein": 0.0, "carbs": 0.0, "fats": 0.0,
                "is_elite": True, "recommended_for_goal": "athletic",
                "target_muscle_group": "all"
            },
            {
                "category_id": shk_id, "name": "Mass Gainer (per 100g powder)",
                "calories": 380, "protein": 25.0, "carbs": 60.0, "fats": 5.0,
                "is_elite": False, "recommended_for_goal": "muscle_gain",
                "target_muscle_group": "all"
            },
            # ============ TREATS ============
            {
                "category_id": tre_id, "name": "Dark Chocolate (85%)",
                "calories": 598, "protein": 7.8, "carbs": 45.9, "fats": 42.6,
                "is_elite": True, "recommended_for_goal": "general",
                "target_muscle_group": "general"
            },
            {
                "category_id": tre_id, "name": "Donut (glazed)",
                "calories": 452, "protein": 4.3, "carbs": 58.0, "fats": 22.0,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "general"
            },
            {
                "category_id": tre_id, "name": "Pizza Slice (pepperoni)",
                "calories": 285, "protein": 12.0, "carbs": 36.0, "fats": 10.0,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "general"
            },
            {
                "category_id": tre_id, "name": "French Fries (100g)",
                "calories": 312, "protein": 3.4, "carbs": 41.0, "fats": 15.0,
                "is_elite": False, "recommended_for_goal": "general",
                "target_muscle_group": "general"
            },
        ]
        for f in foods:
            db.add(models.FoodItem(**f))
        db.commit()
        print(f"✅ Food database seeded with {len(foods)} items.")
    except Exception as e:
        print(f"Error seeding food database: {e}")
        db.rollback()
    finally:
        db.close()


def seed_exercise_database():
    """Injects a comprehensive exercise library.

    Tagged by fitness_goal from JSON seed data.
    """
    import json
    from . import models
    from .generate_seed_data import generate_exercises_json

    db = SessionLocal()
    try:
        # wger categories (matches real wger data)
        wger_categories = [
            {
                "name": "Abs",
                "description": "Core and abdominal exercises.",
            },
            {
                "name": "Arms",
                "description": "Bicep, tricep, and forearm exercises.",
            },
            {
                "name": "Back",
                "description": "Lat, trap, and posterior chain exercises.",
            },
            {
                "name": "Calves",
                "description": "Calf raise and lower-leg exercises.",
            },
            {
                "name": "Cardio",
                "description": (
                    "Cardiovascular and conditioning exercises."
                ),
            },
            {
                "name": "Chest",
                "description": "Pectoral press and fly exercises.",
            },
            {
                "name": "Legs",
                "description": "Quadricep, hamstring, and glute exercises.",
            },
            {
                "name": "Shoulders",
                "description": "Deltoid press and raise exercises.",
            },
        ]

        # Detect if we need to re-seed
        # (old synthetic categories → new wger categories)
        existing_count = db.query(models.ExerciseItem).count()
        has_wger_cats = (
            db.query(models.ExerciseCategory)
            .filter_by(name="Abs")
            .first()
            is not None
        )
        json_path = generate_exercises_json()
        is_wger_source = "wger" in json_path

        if existing_count > 0 and has_wger_cats and not is_wger_source:
            # Already seeded with wger categories, skip
            db.close()
            return
        elif existing_count > 0 and not has_wger_cats and is_wger_source:
            # Old schema but new wger data available — re-seed
            logger.info(
                "Detected category schema change. "
                "Re-seeding exercises with wger data …"
            )
            db.query(models.ExerciseItem).delete()
            db.query(models.ExerciseCategory).delete()
            db.commit()
        elif existing_count > 0:
            # Already seeded, no schema change needed
            db.close()
            return

        # Ensure categories exist
        for cat in wger_categories:
            exists = (
                db.query(models.ExerciseCategory)
                .filter_by(name=cat["name"])
                .first()
            )
            if not exists:
                db.add(models.ExerciseCategory(**cat))
        db.commit()

        # Load category mappings
        cat_map = {
            c.name: c.id for c in db.query(models.ExerciseCategory).all()
        }

        # Load exercise JSON
        with open(json_path, "r", encoding="utf-8") as f:
            exercises_data = json.load(f)

        exercise_objects = []
        for ex in exercises_data:
            cat_id = cat_map.get(ex["category_name"])
            if cat_id:
                exercise_objects.append(models.ExerciseItem(
                    category_id=cat_id,
                    name=ex["name"],
                    targeted_muscle=ex["targeted_muscle"],
                    difficulty=ex["difficulty"],
                    equipment=ex["equipment"],
                    calories_per_min=ex["calories_per_min"],
                    fitness_goal=ex["fitness_goal"],
                    description=ex.get("description", "")
                ))

        db.bulk_save_objects(exercise_objects)
        db.commit()
        source_label = "wger API" if is_wger_source else "fallback"
        print(
            f"[OK] Exercise database seeded with {len(exercise_objects)} "
            f"exercises ({source_label})."
        )

        # Seed Specialized Female Exercises
        existing_female_count = db.query(models.FemaleExerciseItem).count()
        if existing_female_count == 0:
            print("Seeding specialized cycle-synced female exercises...")
            female_exercises = [
                # Menstrual Phase (Low intensity, recovery, gentle)
                {
                    "category_name": "Cardio",
                    "name": "Restorative Yoga Flow",
                    "targeted_muscle": "Full Body",
                    "difficulty": "Beginner",
                    "equipment": "Mat",
                    "calories_per_min": 3.2,
                    "suitable_cycle_phase": "Menstrual",
                    "description": (
                        "Gentle, restorative yoga postures designed to relieve "
                        "menstrual cramping, open the hips, and calm the "
                        "nervous system."
                    )
                },
                {
                    "category_name": "Cardio",
                    "name": "Slow Pelvic Floor Stretches",
                    "targeted_muscle": "Pelvic Floor",
                    "difficulty": "Beginner",
                    "equipment": "Mat",
                    "calories_per_min": 2.5,
                    "suitable_cycle_phase": "Menstrual",
                    "description": (
                        "Slow, ACOG-aligned breathing and deep stretching "
                        "targeting pelvic stability, relieving lower back "
                        "aches."
                    )
                },

                # Follicular Phase (Energy rising, progressive overload)
                {
                    "category_name": "Legs",
                    "name": "Progressive Kettlebell Deadlifts",
                    "targeted_muscle": "Glutes & Hamstrings",
                    "difficulty": "Intermediate",
                    "equipment": "Kettlebell",
                    "calories_per_min": 7.5,
                    "suitable_cycle_phase": "Follicular",
                    "description": (
                        "Focusing on strength development and glute "
                        "activation during the follicular peak when estrogen "
                        "supports hypertrophic growth."
                    )
                },
                {
                    "category_name": "Abs",
                    "name": "Pilates Core Alignment",
                    "targeted_muscle": "Abs",
                    "difficulty": "Intermediate",
                    "equipment": "Mat",
                    "calories_per_min": 5.0,
                    "suitable_cycle_phase": "Follicular",
                    "description": (
                        "Core-strengthening Pilates flow, building abdominal "
                        "strength and pelvic alignment."
                    )
                },

                # Ovulatory Phase (High testosterone/estrogen, peak output)
                {
                    "category_name": "Cardio",
                    "name": "High-Intensity Interval Training (HIIT)",
                    "targeted_muscle": "Full Body",
                    "difficulty": "Advanced",
                    "equipment": "None",
                    "calories_per_min": 12.5,
                    "suitable_cycle_phase": "Ovulatory",
                    "description": (
                        "Explosive intervals leveraging peak energy, maximum "
                        "strength capacity, and optimal insulin sensitivity."
                    )
                },
                {
                    "category_name": "Legs",
                    "name": "Barbell Squats (Peak Load)",
                    "targeted_muscle": "Quadriceps",
                    "difficulty": "Advanced",
                    "equipment": "Barbell",
                    "calories_per_min": 10.0,
                    "suitable_cycle_phase": "Ovulatory",
                    "description": (
                        "Heavy squats capitalizing on your peak strength levels "
                        "during ovulation. Go for progressive overload."
                    )
                },

                # Luteal Phase (Endurance, steady-state movement)
                {
                    "category_name": "Cardio",
                    "name": "Steady-State Aerobic Jogging",
                    "targeted_muscle": "Legs",
                    "difficulty": "Intermediate",
                    "equipment": "None",
                    "calories_per_min": 8.0,
                    "suitable_cycle_phase": "Luteal",
                    "description": (
                        "Low-to-moderate steady jogging. Fits perfectly with "
                        "high luteal body temperatures and fat oxidation "
                        "rates."
                    )
                },
                {
                    "category_name": "Arms",
                    "name": "Moderate Resistance Arm Sculpting",
                    "targeted_muscle": "Arms",
                    "difficulty": "Beginner",
                    "equipment": "Dumbbells",
                    "calories_per_min": 4.5,
                    "suitable_cycle_phase": "Luteal",
                    "description": (
                        "Moderate dumbbell circuits for arm preservation and "
                        "endurance, avoiding high central nervous system "
                        "fatigue."
                    )
                }
            ]

            female_objects = []
            for item in female_exercises:
                cat_id = cat_map.get(item["category_name"])
                if cat_id:
                    female_objects.append(models.FemaleExerciseItem(
                        category_id=cat_id,
                        name=item["name"],
                        targeted_muscle=item["targeted_muscle"],
                        difficulty=item["difficulty"],
                        equipment=item["equipment"],
                        calories_per_min=item["calories_per_min"],
                        suitable_cycle_phase=item["suitable_cycle_phase"],
                        description=item["description"]
                    ))
            db.bulk_save_objects(female_objects)
            db.commit()
            print(
                f"[OK] Seeded {len(female_objects)} cycle-synced female "
                f"exercises successfully."
            )
    except Exception as e:
        print(f"Error seeding exercise database: {e}")
        db.rollback()
    finally:
        db.close()
