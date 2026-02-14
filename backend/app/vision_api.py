"""
Vision API Router

Advanced computer vision endpoints for food detection using YOLOv8, ResNet, and portion estimation.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from pathlib import Path
import os
import shutil
from datetime import datetime

from app.database import get_db
from app.models.yolo_food_detector import get_yolo_detector
from app import models as db_models

router = APIRouter(prefix="/api/vision", tags=["vision"])

# Upload directory
UPLOAD_DIR = Path("uploads/vision")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/detect-yolo")
async def detect_with_yolo(
    file: UploadFile = File(...),
    confidence: float = 0.5,
    annotate: bool = False,
    db: Session = Depends(get_db)
):
    """
    Detect foods using YOLOv8 with bounding boxes and portion estimates
    
    - **file**: Image file to analyze
    - **confidence**: Minimum confidence threshold (0-1)
    - **annotate**: If true, returns annotated image with bounding boxes
    
    Returns:
        {
            'detections': [{class, confidence, bbox, portion_estimate_g}],
            'total_foods': int,
            'model_used': 'yolov8' or 'mock',
            'annotated_image_url': optional
        }
    """
    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = file.filename.split('.')[-1]
    filename = f"yolo_{timestamp}.{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Get YOLOv8 detector
        detector = get_yolo_detector()
        
        # Run detection
        if annotate:
            annotated_filename = f"annotated_{filename}"
            annotated_path = UPLOAD_DIR / annotated_filename
            results, _ = detector.detect_and_annotate(
                str(file_path),
                str(annotated_path)
            )
            results['annotated_image_url'] = f"/uploads/vision/{annotated_filename}"
        else:
            results = detector.detect(str(file_path), confidence)
        
        # Add file info
        results['original_filename'] = file.filename
        results['uploaded_at'] = timestamp
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/detect-hybrid")
async def detect_hybrid(
    file: UploadFile = File(...),
    user_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Hybrid detection: Use YOLOv8 + Gemini + ResNet ensemble
    
    Combines multiple models for best accuracy
    """
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = file.filename.split('.')[-1]
    filename = f"hybrid_{timestamp}.{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 1. YOLOv8 detection
        yolo_detector = get_yolo_detector()
        yolo_results = yolo_detector.detect(str(file_path))
        
        # 2. Gemini detection (from existing scanner)
        from app.gemini_meal_scanner import PersonalizedMealScanner
        gemini_scanner = PersonalizedMealScanner()
        
        try:
            # Read file as bytes for Gemini
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            gemini_results = gemini_scanner.scan_meal(image_bytes)
        except:
            gemini_results = None
        
        # 3. Combine results (ensemble)
        combined = {
            'yolo': yolo_results,
            'gemini': gemini_results,
            'final_detections': []
        }
        
        # Merge detected foods (prioritize YOLO if available)
        if yolo_results['model_used'] == 'yolov8':
            for detection in yolo_results['detections']:
                combined['final_detections'].append({
                    'food': detection['class'].replace('_', ' ').title(),
                    'confidence': detection['confidence'],
                    'portion_g': detection['portion_estimate_g'],
                    'source': 'yolov8'
                })
        
        # Add Gemini foods if detected
        if gemini_results:
            for food in gemini_results.get('detected_foods', []):
                combined['final_detections'].append({
                    'food': food,
                    'confidence': gemini_results.get('confidence', 0.8),
                    'source': 'gemini'
                })
        
        combined['total_unique_foods'] = len(set([d['food'] for d in combined['final_detections']]))
        combined['ensemble_confidence'] = sum([d['confidence'] for d in combined['final_detections']]) / max(len(combined['final_detections']), 1)
        
        # Save to database if user_id provided
        if user_id and db:
            food_detection = db_models.FoodDetection(
                user_id=user_id,
                image_path=str(file_path),
                yolo_detections=yolo_results,
                gemini_detections=gemini_results if gemini_results else {},
                final_result=combined,
                model_used='hybrid'
            )
            db.add(food_detection)
            db.commit()
        
        return combined
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid detection failed: {str(e)}")


@router.post("/classify-resnet")
async def classify_with_resnet(
    file: UploadFile = File(...),
    top_k: int = 3
):
    """
    Classify food using ResNet50 fine-tuned classifier
    
    - **file**: Image file
    - **top_k**: Number of top predictions to return
    
    Returns top-K food classifications with confidence scores
    """
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = file.filename.split('.')[-1]
    filename = f"resnet_{timestamp}.{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Get ResNet50 classifier
        from app.models.resnet_classifier import get_resnet_classifier
        classifier = get_resnet_classifier()
        
        # Classify
        results = classifier.classify(str(file_path), top_k=top_k)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ResNet50 classification failed: {str(e)}")


@router.post("/estimate-portions")
async def estimate_portions_maskrcnn(
    file: UploadFile = File(...),
    food_labels: Optional[str] = None  # Comma-separated list
):
    """
    Estimate portion sizes using Mask R-CNN segmentation
    
    - **file**: Image file
    - **food_labels**: Optional comma-separated food names (e.g., "chicken,rice,broccoli")
    
    Returns pixel-level portion estimates with weight calculations
    """
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = file.filename.split('.')[-1]
    filename = f"maskrcnn_{timestamp}.{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Get Mask R-CNN estimator
        from app.models.portion_estimator import get_portion_estimator
        estimator = get_portion_estimator()
        
        # Parse food labels
        labels_list = food_labels.split(',') if food_labels else None
        
        # Estimate portions
        results = estimator.estimate_portions(str(file_path), food_labels=labels_list)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portion estimation failed: {str(e)}")


@router.post("/detect-ensemble")
async def detect_ensemble(
    file: UploadFile = File(...),
    use_all_models: bool = True
):
    """
    Ultimate ensemble: Combine ALL vision models
    
    - YOLOv8 for detection + bounding boxes
    - ResNet50 for classification
    - Mask R-CNN for portions
    - Gemini for context
    
    Returns best combined results from all models
    """
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = file.filename.split('.')[-1]
    filename = f"ensemble_{timestamp}.{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        results = {'models_used': []}
        
        # 1. YOLO detection
        from app.models.yolo_food_detector import get_yolo_detector
        yolo = get_yolo_detector()
        yolo_result = yolo.detect(str(file_path))
        results['yolo'] = yolo_result
        results['models_used'].append('yolov8')
        
        # 2. ResNet50 classification
        if use_all_models:
            from app.models.resnet_classifier import get_resnet_classifier
            resnet = get_resnet_classifier()
            resnet_result = resnet.classify(str(file_path), top_k=3)
            results['resnet'] = resnet_result
            results['models_used'].append('resnet50')
        
        # 3. Mask R-CNN portions
        if use_all_models:
            from app.models.portion_estimator import get_portion_estimator
            maskrcnn = get_portion_estimator()
            
            # Use YOLO detections as labels
            food_labels = [d['class'] for d in yolo_result['detections']]
            portion_result = maskrcnn.estimate_portions(str(file_path), food_labels=food_labels)
            results['maskrcnn'] = portion_result
            results['models_used'].append('maskrcnn')
        
        # 4. Combine into final prediction
        final_foods = []
        
        # Prioritize: Mask R-CNN portions > YOLO portions
        if 'maskrcnn' in results:
            for portion in results['maskrcnn']['portions']:
                final_foods.append({
                    'food': portion['food'],
                    'weight_g': portion['estimated_weight_g'],
                    'confidence': portion['confidence'],
                    'source': 'maskrcnn'
                })
        else:
            # Fallback to YOLO
            for detection in yolo_result['detections']:
                final_foods.append({
                    'food': detection['class'],
                    'weight_g': detection['portion_estimate_g'],
                    'confidence': detection['confidence'],
                    'source': 'yolov8'
                })
        
        # Add ResNet classification as verification
        if 'resnet' in results:
            results['classification_verification'] = {
                'top_match': resnet_result['top_class'],
                'confidence': resnet_result['top_confidence']
            }
        
        results['final_detections'] = final_foods
        results['ensemble_count'] = len(results['models_used'])
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ensemble detection failed: {str(e)}")


@router.get("/models/status")
async def get_models_status():
    """
    Check which computer vision models are available
    """
    from app.models.yolo_food_detector import YOLO_AVAILABLE
    
    # Check PyTorch for ResNet and MaskRCNN
    try:
        import torch
        TORCH_AVAILABLE = True
    except:
        TORCH_AVAILABLE = False
    
    status = {
        'yolov8': {
            'available': YOLO_AVAILABLE,
            'status': 'ready' if YOLO_AVAILABLE else 'not_installed',
            'description': 'Real-time object detection with bounding boxes'
        },
        'resnet50': {
            'available': TORCH_AVAILABLE,
            'status': 'ready' if TORCH_AVAILABLE else 'not_installed',
            'description': 'High-accuracy food classification'
        },
        'maskrcnn': {
            'available': TORCH_AVAILABLE,
            'status': 'ready' if TORCH_AVAILABLE else 'not_installed',
            'description': 'Pixel-level segmentation for accurate portions'
        },
        'gemini': {
            'available': bool(os.getenv('GEMINI_API_KEY')),
            'status': 'ready' if os.getenv('GEMINI_API_KEY') else 'no_api_key',
            'description': 'AI-powered food identification'
        }
    }
    
    # Count available models
    available_count = sum(1 for model in status.values() if model['available'])
    
    return {
        'models': status,
        'available_count': available_count,
        'total_count': len(status),
        'recommended_setup': 'Install ultralytics, torch, and configure GEMINI_API_KEY',
        'ensemble_ready': available_count >= 2
    }


@router.post("/estimate-nutrition")
async def estimate_nutrition_from_detection(detection_result: Dict[str, Any]):
    """
    Convert food detections to nutrition estimates
    
    Uses detected foods + portion estimates to calculate macros
    """
    # Simple nutrition database (in production, use comprehensive DB)
    nutrition_db = {
        'chicken': {'protein_per_100g': 31, 'carbs_per_100g': 0, 'fat_per_100g': 3.6, 'calories_per_100g': 165},
        'rice': {'protein_per_100g': 2.7, 'carbs_per_100g': 28, 'fat_per_100g': 0.3, 'calories_per_100g': 130},
        'broccoli': {'protein_per_100g': 2.8, 'carbs_per_100g': 6.6, 'fat_per_100g': 0.4, 'calories_per_100g': 34},
        'salmon': {'protein_per_100g': 22, 'carbs_per_100g': 0, 'fat_per_100g': 13, 'calories_per_100g': 208},
        'pasta': {'protein_per_100g': 5.3, 'carbs_per_100g': 27, 'fat_per_100g': 0.5, 'calories_per_100g': 124},
    }
    
    total_nutrition = {
        'calories': 0,
        'protein_g': 0,
        'carbs_g': 0,
        'fat_g': 0,
        'items': []
    }
    
    detections = detection_result.get('detections', [])
    
    for detection in detections:
        food_name = detection['class'].lower()
        portion_g = detection.get('portion_estimate_g', 100)
        
        # Find matching nutrition
        nutrition = None
        for key, value in nutrition_db.items():
            if key in food_name:
                nutrition = value
                break
        
        if nutrition:
            # Scale by portion
            multiplier = portion_g / 100
            
            item_nutrition = {
                'food': food_name,
                'portion_g': portion_g,
                'calories': round(nutrition['calories_per_100g'] * multiplier),
                'protein_g': round(nutrition['protein_per_100g'] * multiplier, 1),
                'carbs_g': round(nutrition['carbs_per_100g'] * multiplier, 1),
                'fat_g': round(nutrition['fat_per_100g'] * multiplier, 1)
            }
            
            total_nutrition['items'].append(item_nutrition)
            total_nutrition['calories'] += item_nutrition['calories']
            total_nutrition['protein_g'] += item_nutrition['protein_g']
            total_nutrition['carbs_g'] += item_nutrition['carbs_g']
            total_nutrition['fat_g'] += item_nutrition['fat_g']
    
    total_nutrition['calories'] = round(total_nutrition['calories'])
    total_nutrition['protein_g'] = round(total_nutrition['protein_g'], 1)
    total_nutrition['carbs_g'] = round(total_nutrition['carbs_g'], 1)
    total_nutrition['fat_g'] = round(total_nutrition['fat_g'], 1)
    
    return total_nutrition
