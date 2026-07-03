"""Quick test runner to identify failing tests"""
import subprocess
import sys

test_files = [
    "tests/test_aim_foods.py",
    "tests/test_analytics.py",
    "tests/test_anomaly_detector.py",
    "tests/test_env_vars.py",
    "tests/test_explainability.py",
    "tests/test_meal_scanner.py",
    "tests/test_portion_optimizer.py",
    "tests/test_progressive_overload.py",
    "tests/test_recovery_engine.py",
]

print("Running quick test suite...")
print("=" * 60)

failed_tests = []
passed_tests = []

for test_file in test_files:
    print(f"\nTesting: {test_file}")
    result = subprocess.run(
        ["python", "-m", "pytest", test_file, "-x", "--tb=no", "-q", "--timeout=30"],
        capture_output=True,
        text=True,
        timeout=45
    )
    
    if result.returncode == 0:
        print("[OK] PASSED")
        passed_tests.append(test_file)
    else:
        print("[FAIL] FAILED")
        failed_tests.append(test_file)
        # Print first few lines of error
        lines = result.stdout.split('\n')
        for line in lines[-10:]:
            if line.strip():
                print(f"  {line}")

print("\n" + "=" * 60)
print(f"Summary: {len(passed_tests)} passed, {len(failed_tests)} failed")
print("\nFailed tests:")
for test in failed_tests:
    print(f"  - {test}")
