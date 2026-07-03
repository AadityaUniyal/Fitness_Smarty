#!/usr/bin/env python
"""
Backend Verification Script
Tests that all modules can be imported and basic functionality works
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)
    
    tests = [
        ("app.models", "SQLAlchemy Models"),
        ("app.database", "Database Configuration"),
        ("app.auth", "Authentication Module"),
        ("app.nutrition_analytics", "Nutrition Analytics"),
        ("app.gemini_meal_scanner", "Gemini Meal Scanner"),
        ("main", "Main FastAPI App"),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"[OK] {description} ({module_name})")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {description} ({module_name})")
            print(f"  Error: {str(e)[:100]}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

def test_database():
    """Test database connectivity"""
    print("\n" + "=" * 60)
    print("TESTING DATABASE")
    print("=" * 60)
    
    try:
        from app.database import engine, SessionLocal
        from sqlalchemy import text
        
        # Test connection
        with SessionLocal() as db:
            result = db.execute(text("SELECT 1"))
            print(f"[OK] Database connection successful")
        
        # Test that Base is initialized
        from app.models import Base
        print(f"[OK] SQLAlchemy Base initialized")
        
        return True
    except Exception as e:
        print(f"[FAIL] Database test failed: {str(e)[:200]}")
        return False

def test_gemini():
    """Test Gemini API configuration"""
    print("\n" + "=" * 60)
    print("TESTING GEMINI API")
    print("=" * 60)
    
    try:
        from app.gemini_meal_scanner import PersonalizedMealScanner
        
        # Try to initialize without API key (should fallback gracefully)
        scanner = PersonalizedMealScanner()
        if scanner.model is None:
            print("[OK] Gemini API (graceful fallback - no API key configured)")
        else:
            print("[OK] Gemini API configured and ready")
        return True
    except Exception as e:
        print(f"[FAIL] Gemini test failed: {str(e)[:200]}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("SMARTY-RECO BACKEND VERIFICATION")
    print("=" * 60 + "\n")
    
    results = {
        "Imports": test_imports(),
        "Database": test_database(),
        "Gemini API": test_gemini(),
    }
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[OK] ALL TESTS PASSED - Backend is ready to run!")
        print("\nRun the backend with:")
        print("  python main.py")
    else:
        print("[FAIL] SOME TESTS FAILED - Fix issues above before running")
    print("=" * 60 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
