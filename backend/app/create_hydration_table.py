"""
Create hydration_logs table

Run this script once to add hydration tracking to your database.
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL

def create_hydration_table():
    """Create the hydration_logs table"""
    engine = create_engine(DATABASE_URL)
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS hydration_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date DATE NOT NULL DEFAULT CURRENT_DATE,
        water_ml REAL NOT NULL DEFAULT 0,
        glasses REAL NOT NULL DEFAULT 0,
        logged_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, date)
    );
    
    CREATE INDEX IF NOT EXISTS idx_hydration_user_date 
    ON hydration_logs(user_id, date);
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    
    print("✅ hydration_logs table created successfully!")

if __name__ == "__main__":
    create_hydration_table()
