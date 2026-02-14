#!/usr/bin/env python3
"""
Migration script to create enhanced database schema for Neon PostgreSQL
This migration adds new enhanced tables while preserving existing legacy tables
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to Python path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import text

def create_enhanced_schema():
    """Create enhanced database tables with proper UUID support"""
    print("Creating enhanced database schema...")
    
    # SQL statements for new enhanced tables
    enhanced_tables_sql = [
        # Enable UUID extension
        """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """,
        
        # Enhanced Users table (separate from legacy users table)
        """
        CREATE TABLE IF NOT EXISTS enhanced_users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # User Profiles table
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES enhanced_users(id) ON DELETE CASCADE UNIQUE,
            age INTEGER,
            weight_kg DECIMAL(5,2),
            height_cm INTEGER,
            activity_level VARCHAR(20) CHECK (activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active')),
            primary_goal VARCHAR(30) CHECK (primary_goal IN ('weight_loss', 'weight_gain', 'muscle_gain', 'maintenance', 'athletic_performance')),
            dietary_restrictions TEXT[],
            allergies TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Foods table with USDA integration
        """
        CREATE TABLE IF NOT EXISTS foods (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            fdc_id INTEGER UNIQUE,
            name VARCHAR(255) NOT NULL,
            brand VARCHAR(255),
            category VARCHAR(100),
            serving_size_g DECIMAL(8,2),
            serving_description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Nutrition Facts table
        """
        CREATE TABLE IF NOT EXISTS nutrition_facts (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            food_id UUID REFERENCES foods(id) ON DELETE CASCADE,
            calories_per_100g DECIMAL(8,2),
            protein_g DECIMAL(8,2),
            carbs_g DECIMAL(8,2),
            fat_g DECIMAL(8,2),
            fiber_g DECIMAL(8,2),
            sugar_g DECIMAL(8,2),
            sodium_mg DECIMAL(8,2),
            potassium_mg DECIMAL(8,2),
            calcium_mg DECIMAL(8,2),
            iron_mg DECIMAL(8,2),
            vitamin_c_mg DECIMAL(8,2),
            vitamin_d_ug DECIMAL(8,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Enhanced Exercises table
        """
        CREATE TABLE IF NOT EXISTS exercises (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            muscle_groups TEXT[],
            equipment TEXT[],
            difficulty_level VARCHAR(20) CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
            instructions TEXT,
            safety_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Enhanced Meal Logs table
        """
        CREATE TABLE IF NOT EXISTS meal_logs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES enhanced_users(id) ON DELETE CASCADE,
            meal_type VARCHAR(20) CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_url VARCHAR(500),
            analysis_confidence DECIMAL(3,2),
            total_calories DECIMAL(8,2),
            total_protein_g DECIMAL(8,2),
            total_carbs_g DECIMAL(8,2),
            total_fat_g DECIMAL(8,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Meal Components table
        """
        CREATE TABLE IF NOT EXISTS meal_components (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            meal_log_id UUID REFERENCES meal_logs(id) ON DELETE CASCADE,
            food_id UUID REFERENCES foods(id),
            estimated_quantity_g DECIMAL(8,2),
            confidence_score DECIMAL(3,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # User Goals table
        """
        CREATE TABLE IF NOT EXISTS user_goals (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES enhanced_users(id) ON DELETE CASCADE,
            goal_type VARCHAR(30),
            target_value DECIMAL(10,2),
            current_value DECIMAL(10,2),
            target_date DATE,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Recommendations table
        """
        CREATE TABLE IF NOT EXISTS recommendations (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES enhanced_users(id) ON DELETE CASCADE,
            recommendation_type VARCHAR(30),
            title VARCHAR(255),
            description TEXT,
            confidence_score DECIMAL(3,2),
            is_read BOOLEAN DEFAULT false,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    ]
    
    try:
        with engine.connect() as connection:
            # Execute each SQL statement
            for i, sql in enumerate(enhanced_tables_sql):
                print(f"Executing statement {i+1}/{len(enhanced_tables_sql)}...")
                connection.execute(text(sql))
                connection.commit()
        
        print("✅ Enhanced database schema created successfully!")
        
        # List all tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Total tables in database: {len(tables)}")
        
        # Show new enhanced tables
        enhanced_tables = [t for t in tables if t in ['enhanced_users', 'user_profiles', 'foods', 'nutrition_facts', 
                                                     'exercises', 'meal_logs', 'meal_components', 'user_goals', 'recommendations']]
        print(f"New enhanced tables ({len(enhanced_tables)}):")
        for table in sorted(enhanced_tables):
            print(f"  - {table}")
            
    except Exception as e:
        print(f"❌ Failed to create schema: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    create_enhanced_schema()