import os
import sys
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_migration():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        from dotenv import load_dotenv
        # load from backend folder
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
        database_url = os.getenv("DATABASE_URL", "sqlite:///./smarty_neural_core.db")

    print(f"Connecting to database at {database_url}")
    engine = create_engine(database_url, pool_pre_ping=True)

    with engine.connect() as conn:
        print("Checking/Adding femmecare_enabled column to users table...")
        if "postgresql" in database_url:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS femmecare_enabled BOOLEAN DEFAULT FALSE;"))
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS femmecare_enabled BOOLEAN DEFAULT FALSE;"))
        else:
            # SQLite fallback
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN femmecare_enabled BOOLEAN DEFAULT 0;"))
            except Exception as e:
                print(f"Note (users): {e}")
            try:
                conn.execute(text("ALTER TABLE user_profiles ADD COLUMN femmecare_enabled BOOLEAN DEFAULT 0;"))
            except Exception as e:
                print(f"Note (user_profiles): {e}")
        conn.commit()
    print("Migration complete!")

if __name__ == "__main__":
    run_migration()
