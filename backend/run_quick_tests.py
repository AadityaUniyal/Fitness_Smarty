"""Quick test runner to identify failing tests"""
import subprocess
import sys

test_files = [
    "tests/test_authentication_security_property.py",
    "tests/test_file_classification.py",
    "tests/test_file_classification_property.py",
    "tests/test_food_data_validation_property.py",
    "tests/test_goal_validation_logic_property.py",
    "tests/test_image_upload_validation_property.py",
    "tests/test_meal_tracking.py",
    "tests/test_migration_data_safety_property.py",
    "tests/test_nutrition_data_lookup_property.py",
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
        print(f"✅ PASSED")
        passed_tests.append(test_file)
    else:
        print(f"❌ FAILED")
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
