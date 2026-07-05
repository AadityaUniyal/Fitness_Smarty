import sqlite3
import os

db_paths = [
    "smarty_neural_core.db",
    "backend/smarty_neural_core.db",
    "backend/test_assistant.db",
    "backend/test_extensions.db",
    "backend/test_smarty_temp.db"
]

for db_path in db_paths:
    print(f"\n==========================================")
    print(f"Checking database at: {os.path.abspath(db_path)}")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print("Tables:")
        for t in sorted(tables):
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {t}")
                count = cursor.fetchone()[0]
                print(f"  - {t}: {count} records")
            except Exception as ex:
                print(f"  - {t}: Error: {ex}")
        conn.close()
    else:
        print("File not found.")
