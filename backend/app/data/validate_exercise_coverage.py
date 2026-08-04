#!/usr/bin/env python3
"""validate_exercise_coverage.py

Utility script to compute the coverage matrix of exercises across
muscle_group × equipment × difficulty and write the result to
`exercise_coverage.json` in the project root.

Usage:
    python -m backend.app.data.validate_exercise_coverage
"""

import sys
from pathlib import Path

# Add project root to PYTHONPATH
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from backend.app.database import SessionLocal
from backend.app.exercise_service import ExerciseService

def main():
    db = SessionLocal()
    try:
        coverage = ExerciseService.check_exercise_coverage(db)
        print("Exercise coverage matrix written to project root as 'exercise_coverage.json'.")
        for mg, eq_dict in coverage.items():
            for eq, diff_dict in eq_dict.items():
                for diff, count in diff_dict.items():
                    print(f"{mg:<15} | {eq:<15} | {diff:<12} : {count}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
