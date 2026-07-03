import sqlite3
import os

def run_migrations():
    db_path = "smarty_neural_core.db"
    if not os.path.exists(db_path):
        # Maybe running in parent or backend dir
        db_path = os.path.join("backend", db_path)
        if not os.path.exists(db_path):
            # Check current folder
            db_path = "../smarty_neural_core.db"
            if not os.path.exists(db_path):
                print("Database file not found; skipping column migration (SQLAlchemy create_all will handle fresh creations).")
                return

    print(f"Connecting to database at {db_path} to ensure FemmeCare schema updates...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # User table additions
    columns_to_add_users = [
        ("menopause_mode", "BOOLEAN DEFAULT 0"),
        ("pregnancy_mode", "BOOLEAN DEFAULT 0"),
        ("local_only", "BOOLEAN DEFAULT 0")
    ]
    for col, definition in columns_to_add_users:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
            print(f"Added column {col} to users table.")
        except sqlite3.OperationalError:
            # Column already exists
            pass

    # UserProfiles table additions
    for col, definition in columns_to_add_users:
        try:
            cursor.execute(f"ALTER TABLE user_profiles ADD COLUMN {col} {definition}")
            print(f"Added column {col} to user_profiles table.")
        except sqlite3.OperationalError:
            # Column already exists
            pass

    # Menstrual logs table additions
    columns_to_add_logs = [
        ("encrypted_symptoms", "TEXT"),
        ("encrypted_mood", "TEXT"),
        ("encrypted_flow_intensity", "TEXT"),
        ("encrypted_notes", "TEXT")
    ]
    for col, definition in columns_to_add_logs:
        try:
            cursor.execute(f"ALTER TABLE menstrual_cycle_logs ADD COLUMN {col} {definition}")
            print(f"Added column {col} to menstrual_cycle_logs table.")
        except sqlite3.OperationalError:
            # Column already exists
            pass

    conn.commit()
    conn.close()
    print("Database migrations applied successfully.")

if __name__ == "__main__":
    run_migrations()
