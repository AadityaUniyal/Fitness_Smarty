import os
import sys
import io
import subprocess
import secrets
from contextlib import redirect_stdout

# Ensure backend directory is in python path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_dir = os.path.join(repo_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set test database URL
test_db_path = os.path.join(backend_dir, "test_m2_challenger.db")
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"

from app.database import engine, SessionLocal
from app.models import Base, EnhancedUser
from app.auth import PasswordHasher
from seed_data import seed_admin_user

def reset_db():
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_seed_admin_unset():
    print("\n--- TEST 1: seed_data.py with ADMIN_PASSWORD UNSET ---")
    reset_db()
    if "ADMIN_PASSWORD" in os.environ:
        del os.environ["ADMIN_PASSWORD"]
    
    f = io.StringIO()
    with redirect_stdout(f):
        seed_admin_user()
    output = f.getvalue()
    print("Captured Output:\n" + output)
    
    assert "SECURITY NOTICE: No ADMIN_PASSWORD environment variable specified." in output, "Notice missing!"
    assert "Email:    admin@smarty.ai" in output, "Email missing!"
    
    # Extract password line
    pass_line = [l for l in output.splitlines() if "Password:" in l]
    assert len(pass_line) > 0, "Generated password line not found in output!"
    gen_password = pass_line[0].split("Password:")[1].strip()
    print(f"Extracted generated password: {gen_password}")
    
    db = SessionLocal()
    admin = db.query(EnhancedUser).filter(EnhancedUser.email == "admin@smarty.ai").first()
    assert admin is not None, "Admin user not found in DB!"
    assert admin.username == "admin"
    assert admin.is_admin is True
    assert PasswordHasher.verify_password(gen_password, admin.hashed_password), "Generated password verification failed!"
    assert not PasswordHasher.verify_password("wrongpassword", admin.hashed_password), "False positive password match!"
    db.close()
    print("PASS: UNSET ADMIN_PASSWORD generated secure random password and verified successfully!")

def test_seed_admin_set():
    print("\n--- TEST 2: seed_data.py with ADMIN_PASSWORD SET ---")
    reset_db()
    custom_pass = "CustomAdminPassword2026!#"
    os.environ["ADMIN_PASSWORD"] = custom_pass
    
    f = io.StringIO()
    with redirect_stdout(f):
        seed_admin_user()
    output = f.getvalue()
    print("Captured Output:\n" + output)
    
    assert "Default admin user (admin@smarty.ai) created successfully with ADMIN_PASSWORD from environment!" in output
    assert custom_pass not in output, "Password leaked in stdout!"
    
    db = SessionLocal()
    admin = db.query(EnhancedUser).filter(EnhancedUser.email == "admin@smarty.ai").first()
    assert admin is not None, "Admin user not found in DB!"
    assert PasswordHasher.verify_password(custom_pass, admin.hashed_password), "Custom password verification failed!"
    assert not PasswordHasher.verify_password("wrongpassword", admin.hashed_password), "False positive password match!"
    
    # Test idempotent second run
    f2 = io.StringIO()
    with redirect_stdout(f2):
        seed_admin_user()
    output2 = f2.getvalue()
    print("Captured Output (2nd run):\n" + output2)
    assert "already exists" in output2
    db.close()
    print("PASS: SET ADMIN_PASSWORD created user with custom password and handles re-run cleanly!")

def test_init_database_script():
    print("\n--- TEST 3: init_database.py Subprocess execution ---")
    reset_db()
    # Test with UNSET ADMIN_PASSWORD
    env_unset = os.environ.copy()
    if "ADMIN_PASSWORD" in env_unset:
        del env_unset["ADMIN_PASSWORD"]
    
    res = subprocess.run(
        [sys.executable, "init_database.py"],
        cwd=backend_dir,
        env=env_unset,
        capture_output=True,
        text=True
    )
    print("STDOUT (init_database.py UNSET):\n" + res.stdout)
    assert res.returncode == 0, f"Script failed with code {res.returncode}: {res.stderr}"
    assert "SECURITY NOTICE: No ADMIN_PASSWORD environment variable specified." in res.stdout
    
    # Test with SET ADMIN_PASSWORD
    reset_db()
    env_set = os.environ.copy()
    env_set["ADMIN_PASSWORD"] = "SubprocessAdminPass999!"
    
    res_set = subprocess.run(
        [sys.executable, "init_database.py"],
        cwd=backend_dir,
        env=env_set,
        capture_output=True,
        text=True
    )
    print("STDOUT (init_database.py SET):\n" + res_set.stdout)
    assert res_set.returncode == 0, f"Script failed with code {res_set.returncode}: {res_set.stderr}"
    assert "created successfully with ADMIN_PASSWORD from environment!" in res_set.stdout
    print("PASS: init_database.py subprocess execution verified for both UNSET and SET ADMIN_PASSWORD!")

if __name__ == "__main__":
    try:
        test_seed_admin_unset()
        test_seed_admin_set()
        test_init_database_script()
        print("\n================ ALL EMPIRICAL SEED/INIT TESTS PASSED ================")
    except Exception as e:
        print(f"\nFAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
