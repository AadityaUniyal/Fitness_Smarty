import os
import sys
import re
import ast
import subprocess

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def get_tracked_files():
    res = subprocess.run(["git", "ls-files"], cwd=repo_root, capture_output=True, text=True, check=True)
    return [f.strip() for f in res.stdout.splitlines() if f.strip()]

def check_env_files(files):
    env_files = [f for f in files if f.startswith(".env") or "/.env" in f or f.endswith(".env") or ".env." in f]
    print(f"Scanning {len(env_files)} tracked .env* files...")
    findings = []
    
    for relative_path in env_files:
        full_path = os.path.join(repo_root, relative_path)
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines, 1):
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue
            if "=" in line_str:
                key, val = line_str.split("=", 1)
                key = key.strip()
                val = val.strip()
                # Check if password/secret keys have actual hardcoded values instead of placeholders or empty strings
                if any(sec in key.upper() for sec in ["PASSWORD", "SECRET", "TOKEN", "KEY", "CREDENTIAL"]):
                    # Known acceptable placeholders
                    placeholders = [
                        "", "your_secret_key_here", "your_admin_password_here",
                        "your_gemini_api_key_here", "your-sender-email-app-password",
                        "your-sender-email@gmail.com", "postgresql://user:password@host/dbname?sslmode=require"
                    ]
                    # Also strip comment from val
                    val_no_comment = val.split("#")[0].strip()
                    if val_no_comment and val_no_comment not in placeholders:
                        findings.append(f"{relative_path}:{idx}: Key '{key}' has non-placeholder value '{val}'")
    return findings

def check_py_files(files):
    py_files = [f for f in files if f.endswith(".py")]
    print(f"Scanning {len(py_files)} tracked .py files...")
    findings = []
    
    # Suspicious pattern regexes
    # Hardcoded default passwords in function defaults or variable assignments
    suspicious_patterns = [
        re.compile(r'admin_password\s*=\s*["\'](?!$)([^"\']+)["\']', re.IGNORECASE),
        re.compile(r'default_password\s*=\s*["\'](?!$)([^"\']+)["\']', re.IGNORECASE),
        re.compile(r'password\s*=\s*["\'](admin123|password|secret|123456|root|admin)["\']', re.IGNORECASE),
        re.compile(r'hashed_password\s*=\s*["\']\$2[abxy]\$.*["\']'),  # Hardcoded bcrypt hashes
    ]
    
    for relative_path in py_files:
        # Skip test files from strict hardcoded password rules for test mocks, but report if found
        full_path = os.path.join(repo_root, relative_path)
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            lines = content.splitlines()
            
        for idx, line in enumerate(lines, 1):
            # Check for suspicious hardcoded password assignments
            for pattern in suspicious_patterns:
                match = pattern.search(line)
                if match:
                    # Ignore os.getenv fallback checks like os.getenv("ADMIN_PASSWORD", "") if empty or None
                    matched_str = match.group(0)
                    if "os.getenv" in line or "os.environ" in line or "getenv" in line:
                        continue
                    # Check if it's in backend code (excluding tests)
                    findings.append(f"{relative_path}:{idx}: Hardcoded credential pattern found: {matched_str}")

    return findings

def main():
    tracked = get_tracked_files()
    env_findings = check_env_files(tracked)
    py_findings = check_py_files(tracked)
    
    print("\n--- TRACKED .ENV* FILES RESULTS ---")
    if env_findings:
        print(f"WARNING: {len(env_findings)} potential issues found:")
        for f in env_findings:
            print("  - " + f)
    else:
        print("OK: Zero hardcoded production passwords/secrets found in tracked .env* files.")
        
    print("\n--- TRACKED .PY FILES RESULTS ---")
    if py_findings:
        print(f"WARNING: {len(py_findings)} potential issues found:")
        for f in py_findings:
            print("  - " + f)
    else:
        print("OK: Zero hardcoded passwords found in tracked .py files.")

if __name__ == "__main__":
    main()
