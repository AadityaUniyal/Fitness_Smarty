import os
from sqlalchemy import create_engine, inspect
from app.database import Base, engine
from app import models

def check_db():
    print(f"Connecting to: {engine.url}")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Existing tables: {tables}")
    
    try:
        print("Attempting to create tables...")
        models.Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully.")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_db()
