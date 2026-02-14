"""
Database Migration: Add FoodDetection Table (Phase 1)

Creates the food_detections table for YOLOv8 and computer vision results.
"""

from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os

Base = declarative_base()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smarty_neural_core.db")

def upgrade():
    """Create food_detections table"""
    engine = create_engine(DATABASE_URL)
    
    # Import models to ensure they're registered
    from app import models
    
    # Create only the new table
    models.FoodDetection.__table__.create(engine, checkfirst=True)
    
    print("✅ Created food_detections table")

def downgrade():
    """Drop food_detections table"""
    engine = create_engine(DATABASE_URL)
    from app import models
    
    models.FoodDetection.__table__.drop(engine, checkfirst=True)
    
    print("✅ Dropped food_detections table")

if __name__ == "__main__":
    print("Running migration: Add FoodDetection table...")
    upgrade()
    print("Migration complete!")
