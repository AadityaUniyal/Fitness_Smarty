"""
NLP API Router

Natural Language Processing endpoints for recipe understanding and semantic search
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pathlib import Path
import os
import shutil
from datetime import datetime

from app.database import get_db
from app import models as db_models

router = APIRouter(prefix="/api/nlp", tags=["nlp"])

# Upload directory
UPLOAD_DIR = Path("uploads/nlp")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/analyze-recipe")
async def analyze_recipe_text(
    recipe_text: str,
    estimate_nutrition: bool = True
):
    """
    Analyze recipe text using BERT
    
    - **recipe_text**: Recipe as plain text or ingredients list
    - **estimate_nutrition**: Calculate nutrition from ingredients
    
    Returns extracted ingredients, quantities, and optional nutrition
    """
    try:
        # Get BERT recipe analyzer
        from app.models.recipe_bert import get_recipe_bert
        bert = get_recipe_bert()
        
        # Analyze recipe
        analysis = bert.analyze_recipe(recipe_text)
        
        # Estimate nutrition if requested
        if estimate_nutrition:
            nutrition = bert.recipe_to_nutrition(analysis)
            analysis['nutrition_estimate'] = nutrition
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recipe analysis failed: {str(e)}")


@router.post("/search-by-text")
async def search_meals_by_text(
    query: str,
    top_k: int = 10,
    db: Session = Depends(get_db)
):
    """
    Semantic search for meals using CLIP text embeddings
    
    - **query**: Text description (e.g., "high protein low carb breakfast")
    - **top_k**: Number of results to return
    
    Searches through user's meal history using semantic similarity
    """
    try:
        # Get CLIP search
        from app.models.clip_search import get_clip_search
        clip = get_clip_search()
        
        # In production, load meal embeddings from database
        # For now, use mock data
        mock_meal_embeddings = {
            1: clip.encode_text("grilled chicken with vegetables"),
            2: clip.encode_text("pasta with tomato sauce"),
            3: clip.encode_text("salmon with rice and broccoli"),
            4: clip.encode_text("greek salad with feta cheese"),
            5: clip.encode_text("oatmeal with berries and nuts")
        }
        
        # Search
        results = clip.search_by_description(query, mock_meal_embeddings, top_k)
        
        # Add meal details (mock)
        meal_details = {
            1: {"name": "Grilled Chicken Bowl", "calories": 450, "protein_g": 45},
            2: {"name": "Pasta Marinara", "calories": 520, "protein_g": 12},
            3: {"name": "Salmon Rice Bowl", "calories": 580, "protein_g": 38},
            4: {"name": "Greek Salad", "calories": 320, "protein_g": 15},
            5: {"name": "Berry Oatmeal", "calories": 380, "protein_g": 12}
        }
        
        for result in results:
            meal_id = result['meal_id']
            result['meal_details'] = meal_details.get(meal_id, {})
        
        return {
            'query': query,
            'results': results,
            'total_found': len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/search-similar-meals")
async def search_similar_meals(
    file: UploadFile = File(...),
    top_k: int = 5
):
    """
    Find visually similar meals using CLIP image embeddings
    
    - **file**: Image of a meal
    - **top_k**: Number of similar meals to return
    
    Uses CLIP to find meals that look similar
    """
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = file.filename.split('.')[-1]
    filename = f"clip_{timestamp}.{file_extension}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Get CLIP search
        from app.models.clip_search import get_clip_search
        clip = get_clip_search()
        
        # Mock meal embeddings (in production, load from database)
        mock_meal_embeddings = {
            1: clip.encode_text("grilled chicken"),
            2: clip.encode_text("pasta"),
            3: clip.encode_text("salmon"),
            4: clip.encode_text("salad"),
            5: clip.encode_text("oatmeal")
        }
        
        # Find similar
        results = clip.find_similar_images(str(file_path), mock_meal_embeddings, top_k)
        
        # Add details
        meal_details = {
            1: {"name": "Grilled Chicken", "calories": 450},
            2: {"name": "Pasta", "calories": 520},
            3: {"name": "Salmon", "calories": 580},
            4: {"name": "Salad", "calories": 320},
            5: {"name": "Oatmeal", "calories": 380}
        }
        
        for result in results:
            meal_id = result['meal_id']
            result['meal_details'] = meal_details.get(meal_id, {})
        
        return {
            'query_image': filename,
            'results': results,
            'total_found': len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar meal search failed: {str(e)}")


@router.post("/extract-ingredients")
async def extract_ingredients(
    recipe_text: str
):
    """
    Extract just the ingredients from recipe text
    
    Quick endpoint for ingredient extraction without full analysis
    """
    try:
        from app.models.recipe_bert import get_recipe_bert
        bert = get_recipe_bert()
        
        analysis = bert.analyze_recipe(recipe_text)
        
        return {
            'ingredients': analysis['ingredients'],
            'quantities': analysis['quantities'],
            'confidence': analysis['confidence']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingredient extraction failed: {str(e)}")


@router.get("/models/status")
async def get_nlp_models_status():
    """
    Check NLP model availability
    """
    try:
        from app.models.recipe_bert import TRANSFORMERS_AVAILABLE
        from app.models.clip_search import CLIP_AVAILABLE
    except:
        TRANSFORMERS_AVAILABLE = False
        CLIP_AVAILABLE = False
    
    status = {
        'bert': {
            'available': TRANSFORMERS_AVAILABLE,
            'status': 'ready' if TRANSFORMERS_AVAILABLE else 'not_installed',
            'description': 'Recipe text understanding and ingredient extraction'
        },
        'clip': {
            'available': CLIP_AVAILABLE,
            'status': 'ready' if CLIP_AVAILABLE else 'not_installed',
            'description': 'Multi-modal semantic search (text + images)'
        }
    }
    
    available_count = sum(1 for model in status.values() if model['available'])
    
    return {
        'models': status,
        'available_count': available_count,
        'total_count': len(status),
        'recommended_setup': 'Install transformers and clip-anytorch',
        'phase': 2
    }
