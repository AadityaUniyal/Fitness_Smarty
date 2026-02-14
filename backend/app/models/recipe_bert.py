"""
BERT Recipe Analyzer

Extracts food items and nutrition from recipe text using BERT
"""

import os
from typing import Dict, List, Any, Optional
import re

try:
    from transformers import BertTokenizer, BertModel, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️  Transformers not available. Install with: pip install transformers")


class RecipeBERT:
    """
    BERT-based recipe understanding and nutrition extraction
    """
    
    # Common food keywords to extract
    FOOD_KEYWORDS = [
        'chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'shrimp',
        'rice', 'pasta', 'noodles', 'bread', 'quinoa', 'oats',
        'broccoli', 'spinach', 'kale', 'carrot', 'potato', 'tomato',
        'egg', 'cheese', 'milk', 'yogurt', 'butter', 'oil',
        'beans', 'lentils', 'chickpeas', 'tofu', 'tempeh',
        'apple', 'banana', 'orange', 'berries', 'avocado'
    ]
    
    # Nutrition keywords
    NUTRITION_KEYWORDS = [
        'calories', 'protein', 'carbs', 'carbohydrates', 'fat', 'fiber',
        'sugar', 'sodium', 'cholesterol', 'vitamins', 'minerals'
    ]
    
    def __init__(self):
        """Initialize BERT model"""
        self.model = None
        self.tokenizer = None
        self.ner_pipeline = None
        self.mock_mode = False
        
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use DistilBERT for efficiency
                model_name = "distilbert-base-uncased"
                self.tokenizer = BertTokenizer.from_pretrained(model_name)
                self.model = BertModel.from_pretrained(model_name)
                
                # NER pipeline for entity extraction
                self.ner_pipeline = pipeline(
                    "ner",
                    model="dslim/bert-base-NER",
                    aggregation_strategy="simple"
                )
                
                print(f"✓ Loaded BERT model: {model_name}")
                
            except Exception as e:
                print(f"⚠️  Could not load BERT: {e}")
                self.mock_mode = True
        else:
            print("⚠️  Transformers not installed. Using mock mode.")
            self.mock_mode = True
    
    def analyze_recipe(self, recipe_text: str) -> Dict[str, Any]:
        """
        Analyze recipe text and extract foods + nutrition
        
        Args:
            recipe_text: Recipe as plain text
            
        Returns:
            {
                'ingredients': [list of extracted foods],
                'quantities': {food: amount},
                'nutrition_mentions': [any nutrition info found],
                'confidence': float,
                'method': 'bert' or 'mock'
            }
        """
        if self.mock_mode:
            return self._mock_analysis(recipe_text)
        
        try:
            # Extract entities using NER
            entities = self.ner_pipeline(recipe_text)
            
            # Extract ingredient list
            ingredients = self._extract_ingredients(recipe_text, entities)
            
            # Extract quantities
            quantities = self._extract_quantities(recipe_text, ingredients)
            
            # Look for nutrition mentions
            nutrition_mentions = self._extract_nutrition_mentions(recipe_text)
            
            # Calculate confidence based on number of extracted items
            confidence = min(0.9, 0.5 + (len(ingredients) * 0.05))
            
            return {
                'ingredients': ingredients,
                'quantities': quantities,
                'nutrition_mentions': nutrition_mentions,
                'confidence': round(confidence, 2),
                'method': 'bert',
                'entities_found': len(entities)
            }
            
        except Exception as e:
            print(f"Error in BERT analysis: {e}")
            return self._mock_analysis(recipe_text)
    
    def _extract_ingredients(self, text: str, entities: List[Dict]) -> List[str]:
        """Extract food ingredients from text"""
        ingredients = set()
        
        # Method 1: From NER entities (MISC category often contains foods)
        for entity in entities:
            word = entity['word'].lower().strip()
            if any(food in word for food in self.FOOD_KEYWORDS):
                ingredients.add(word)
        
        # Method 2: Direct keyword matching
        text_lower = text.lower()
        for food in self.FOOD_KEYWORDS:
            if food in text_lower:
                ingredients.add(food)
        
        # Method 3: Common ingredient patterns
        # e.g., "2 cups rice", "150g chicken"
        ingredient_pattern = r'\d+\s*(?:cups?|tbsp|tsp|g|oz|lbs?|pounds?)\s+(\w+)'
        matches = re.findall(ingredient_pattern, text_lower)
        for match in matches:
            if len(match) > 3:  # Filter out units
                ingredients.add(match)
        
        return sorted(list(ingredients))
    
    def _extract_quantities(self, text: str, ingredients: List[str]) -> Dict[str, str]:
        """Extract quantities for each ingredient"""
        quantities = {}
        
        for ingredient in ingredients:
            # Look for patterns like "2 cups chicken", "150g rice"
            patterns = [
                rf'(\d+\.?\d*)\s*(?:cups?|c)\s+{ingredient}',
                rf'(\d+\.?\d*)\s*(?:grams?|g)\s+{ingredient}',
                rf'(\d+\.?\d*)\s*(?:oz|ounces?)\s+{ingredient}',
                rf'{ingredient}.*?(\d+\.?\d*)\s*(?:g|grams?|oz)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text.lower())
                if match:
                    quantities[ingredient] = match.group(1)
                    break
        
        return quantities
    
    def _extract_nutrition_mentions(self, text: str) -> List[Dict[str, Any]]:
        """Extract any nutrition information mentioned"""
        nutrition = []
        text_lower = text.lower()
        
        for nutrient in self.NUTRITION_KEYWORDS:
            # Pattern: "450 calories", "30g protein"
            pattern = rf'(\d+\.?\d*)\s*(?:g|grams?)?\s*{nutrient}'
            matches = re.findall(pattern, text_lower)
            
            if matches:
                for value in matches:
                    nutrition.append({
                        'nutrient': nutrient,
                        'value': value,
                        'unit': 'g' if nutrient in ['protein', 'carbs', 'fat', 'fiber'] else 'kcal'
                    })
        
        return nutrition
    
    def _mock_analysis(self, recipe_text: str) -> Dict[str, Any]:
        """Mock analysis when BERT not available"""
        # Simple keyword extraction
        text_lower = recipe_text.lower()
        
        ingredients = []
        for food in self.FOOD_KEYWORDS:
            if food in text_lower:
                ingredients.append(food)
        
        # Extract numbers that might be quantities
        numbers = re.findall(r'\d+', recipe_text)
        
        return {
            'ingredients': ingredients[:5],  # Limit to 5
            'quantities': {ing: numbers[i] if i < len(numbers) else '100' for i, ing in enumerate(ingredients[:3])},
            'nutrition_mentions': [],
            'confidence': 0.6,
            'method': 'mock',
            'entities_found': len(ingredients)
        }
    
    def recipe_to_nutrition(self, recipe_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert recipe analysis to nutrition estimate
        
        Uses a simple nutrition database lookup
        """
        # Simple nutrition database (protein, carbs, fat per 100g)
        nutrition_db = {
            'chicken': (31, 0, 3.6, 165),
            'beef': (26, 0, 15, 250),
            'salmon': (22, 0, 13, 208),
            'rice': (2.7, 28, 0.3, 130),
            'pasta': (5.3, 27, 0.5, 124),
            'broccoli': (2.8, 6.6, 0.4, 34),
            'egg': (13, 1, 11, 143),
            'avocado': (2, 8.5, 14.7, 160),
        }
        
        total_nutrition = {
            'calories': 0,
            'protein_g': 0,
            'carbs_g': 0,
            'fat_g': 0,
            'estimated': True
        }
        
        ingredients = recipe_analysis.get('ingredients', [])
        quantities = recipe_analysis.get('quantities', {})
        
        for ingredient in ingredients:
            # Find nutrition data
            nutrition = None
            for key, value in nutrition_db.items():
                if key in ingredient:
                    nutrition = value
                    break
            
            if nutrition:
                protein, carbs, fat, calories = nutrition
                
                # Get quantity (default to 100g if not specified)
                quantity = float(quantities.get(ingredient, 100))
                multiplier = quantity / 100
                
                total_nutrition['protein_g'] += protein * multiplier
                total_nutrition['carbs_g'] += carbs * multiplier
                total_nutrition['fat_g'] += fat * multiplier
                total_nutrition['calories'] += calories * multiplier
        
        # Round values
        total_nutrition['calories'] = round(total_nutrition['calories'])
        total_nutrition['protein_g'] = round(total_nutrition['protein_g'], 1)
        total_nutrition['carbs_g'] = round(total_nutrition['carbs_g'], 1)
        total_nutrition['fat_g'] = round(total_nutrition['fat_g'], 1)
        
        return total_nutrition


# Singleton instance
_bert_instance: Optional[RecipeBERT] = None

def get_recipe_bert() -> RecipeBERT:
    """Get singleton BERT instance"""
    global _bert_instance
    if _bert_instance is None:
        _bert_instance = RecipeBERT()
    return _bert_instance
