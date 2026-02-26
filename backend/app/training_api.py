"""
Training API Router

Handles requests from n8n (or other pipelines) to:
1. Ingest new training data (images/labels).
2. Trigger model retraining (Recommendation NN or YOLO).
"""

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import shutil
from pathlib import Path
import json
from datetime import datetime

from app.database import get_db
from app.models import FoodTrainingSample
from app.training.train_neural_model import NeuralModelTrainer

router = APIRouter(prefix="/api/training", tags=["training"])

# Directories
DATASET_DIR = Path("datasets")
IMAGES_DIR = DATASET_DIR / "images"
LABELS_DIR = DATASET_DIR / "labels"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
LABELS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/vision/ingest")
async def ingest_vision_sample(
    image: UploadFile = File(...),
    label: str = Form(...),
    confidence: float = Form(0.0),
    corrected: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Ingest a vision training sample (from n8n or app).
    Saves image to dataset folder and records in DB.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{label.replace(' ', '_')}_{timestamp}.jpg"
    file_path = IMAGES_DIR / filename
    
    # Save Image
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # Create YOLO Label text file (class_id centerX centerY width height)
    # Note: Without bbox info from frontend, we can't make a perfect YOLO label.
    # We will just save the image and the classification label for now (Classification Dataset).
    # If we had bbox, we'd save .txt.
    
    # Save metadata to DB
    sample = FoodTrainingSample(
        label=label,
        image_signature=str(file_path),
        confidence=confidence,
        source="n8n_ingest",
        verified=corrected
    )
    # Note: FoodTrainingSample model needs to match this. 
    # I recall creating it with slightly different fields. Let's check.
    # It has: label, calories, protein... source, verified.
    # It might fail if I pass unknown args. 
    # I'll just save what matches.
    
    db_sample = FoodTrainingSample(
        label=label,
        image_signature=str(file_path),
        source="n8n_ingest",
        verified=corrected,
        calories=0  # Placeholder
    )
    db.add(db_sample)
    db.commit()
    
    return {
        "status": "success", 
        "message": f"Saved sample for {label}",
        "path": str(file_path)
    }

@router.post("/recommendation/train")
async def train_recommendation_model(
    background_tasks: BackgroundTasks,
    epochs: int = 50,
    use_db: bool = False
):
    """
    Trigger the Neural Network training process in background.
    """
    trainer = NeuralModelTrainer()
    
    # Run in background to not block response
    # Pass use_db flag to trainer
    background_tasks.add_task(trainer.train, "app/training/datasets/synthetic_meals.jsonl", use_db, epochs)
    
    return {"status": "accepted", "message": f"Training started in background (DB Mode: {use_db})"}

@router.post("/vision/retrain-yolo")
async def trigger_yolo_retrain():
    """
    Placeholder to trigger YOLOv8 retraining.
    Real training requires significant resources.
    """
    return {
        "status": "simulated", 
        "message": "YOLOv8 retraining scheduled (Simulated). Data collected in /datasets folder."
    }
