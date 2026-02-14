"""
Nutrition Analysis and Calculation Engine

Provides comprehensive nutrition data lookup, portion estimation algorithms,
and macro/micronutrient calculation logic for meal analysis.

This module implements Requirements 3.2 and 3.3:
- Nutrition data lookup from detected foods
- Portion estimation algorithms
- Macro/micronutrient calculation logic
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@dataclass
class NutritionData:
    """Complete nutrition data for a food item"""
    # Macronutrients (per 100g)
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sugar_g: float
    
    # Micronutrients (per 100g)
    sodium_mg: float = 0.0
    potassium_mg: float = 0.0
    calcium_mg: float = 0.0
    iron_mg: float = 0.0
    vitamin_c_mg: float = 0.0
    vitamin_d_ug: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'calories': self.calories,
            'protein_g': self.protein_g,
            'carbs_g': self.carbs_g,
            'fat_g': self.fat_g,
            'fiber_g': self.fiber_g,
            'sugar_g': self.sugar_g,
            'sodium_mg': self.sodium_mg,
            'potassium_mg': self.potassium_mg,
            'calcium_mg': self.calcium_mg,
            'iron_mg': self.iron_mg,
            'vitamin_c_mg': self.vitamin_c_mg,
            'vitamin_d_ug': self.vitamin_d_ug
        }


@dataclass
class PortionEstimate:
    """Estimated portion size with confidence"""
    quantity_g: float
    confidence: float
    estimation_method: str
    reference_used: Optional[str] = None


@dataclass
class CalculatedNutrition:
    """Nutrition values calculated for a specific portion"""
    portion_g: float
    nutrition: NutritionData
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'portion_g': self.portion_g,
            **self.nutrition.to_dict()
        }


class NutritionDataLookup:
    """
    Handles nutrition data lookup from detected foods
    Implements Requirement 3.2: Nutrition data lookup from detected foods
    """
    
    def __init__(self, food_database_service):
        """
        Initialize nutrition data lookup
        
        Args:
            food_database_service: Service for accessing food database
        """
        self.food_service = food_database_service
    
    def lookup_nutrition(self, food_name: str) -> Optional[NutritionData]:
        """
        Look up nutrition data for a food item by name
        
        Args:
            food_name: Name of the food item
            
        Returns:
            NutritionData object if found, None otherwise
        """
        try:
            # Search for food in database
            results = self.food_service.search_foods(food_name, use_fuzzy=True, limit=1)
            
            if not results:
                logger.warning(f"No nutrition data found for: {food_name}")
                return None
            
            food_data = results[0]
            nutrition_facts = food_data.get('nutrition')
            
            if not nutrition_facts:
                logger.warning(f"Food found but no nutrition facts: {food_name}")
                return None
            
            # Extract nutrition data
            return NutritionData(
                calories=nutrition_facts.get('calories_per_100g', 0.0) or 0.0,
                protein_g=nutrition_facts.get('protein_g', 0.0) or 0.0,
                carbs_g=nutrition_facts.get('carbs_g', 0.0) or 0.0,
                fat_g=nutrition_facts.get('fat_g', 0.0) or 0.0,
                fiber_g=nutrition_facts.get('fiber_g', 0.0) or 0.0,
                sugar_g=nutrition_facts.get('sugar_g', 0.0) or 0.0,
                sodium_mg=nutrition_facts.get('sodium_mg', 0.0) or 0.0,
                potassium_mg=nutrition_facts.get('potassium_mg', 0.0) or 0.0,
                calcium_mg=nutrition_facts.get('calcium_mg', 0.0) or 0.0,
                iron_mg=nutrition_facts.get('iron_mg', 0.0) or 0.0,
                vitamin_c_mg=nutrition_facts.get('vitamin_c_mg', 0.0) or 0.0,
                vitamin_d_ug=nutrition_facts.get('vitamin_d_ug', 0.0) or 0.0
            )
            
        except Exception as e:
            logger.error(f"Error looking up nutrition for {food_name}: {str(e)}")
            return None
    
    def lookup_nutrition_by_id(self, food_id: str) -> Optional[NutritionData]:
        """
        Look up nutrition data by food ID
        
        Args:
            food_id: UUID of the food item
            
        Returns:
            NutritionData object if found, None otherwise
        """
        try:
            import uuid
            food = self.food_service.get_food_by_id(uuid.UUID(food_id))
            
            if not food or not food.nutrition_facts:
                return None
            
            nf = food.nutrition_facts
            return NutritionData(
                calories=float(nf.calories_per_100g) if nf.calories_per_100g else 0.0,
                protein_g=float(nf.protein_g) if nf.protein_g else 0.0,
                carbs_g=float(nf.carbs_g) if nf.carbs_g else 0.0,
                fat_g=float(nf.fat_g) if nf.fat_g else 0.0,
                fiber_g=float(nf.fiber_g) if nf.fiber_g else 0.0,
                sugar_g=float(nf.sugar_g) if nf.sugar_g else 0.0,
                sodium_mg=float(nf.sodium_mg) if nf.sodium_mg else 0.0,
                potassium_mg=float(nf.potassium_mg) if nf.potassium_mg else 0.0,
                calcium_mg=float(nf.calcium_mg) if nf.calcium_mg else 0.0,
                iron_mg=float(nf.iron_mg) if nf.iron_mg else 0.0,
                vitamin_c_mg=float(nf.vitamin_c_mg) if nf.vitamin_c_mg else 0.0,
                vitamin_d_ug=float(nf.vitamin_d_ug) if nf.vitamin_d_ug else 0.0
            )
            
        except Exception as e:
            logger.error(f"Error looking up nutrition by ID {food_id}: {str(e)}")
            return None


class PortionEstimator:
    """
    Estimates portion sizes from image analysis and bounding boxes
    Implements Requirement 3.2: Portion estimation algorithms
    """
    
    # Default portion sizes for common foods (in grams)
    DEFAULT_PORTIONS = {
        'chicken': 150.0,
        'beef': 150.0,
        'pork': 150.0,
        'fish': 150.0,
        'salmon': 150.0,
        'tuna': 150.0,
        'rice': 200.0,
        'pasta': 200.0,
        'noodles': 200.0,
        'bread': 50.0,
        'toast': 30.0,
        'salad': 100.0,
        'lettuce': 50.0,
        'broccoli': 100.0,
        'carrot': 80.0,
        'potato': 150.0,
        'sweet potato': 150.0,
        'egg': 50.0,
        'cheese': 30.0,
        'yogurt': 150.0,
        'milk': 250.0,
        'apple': 150.0,
        'banana': 120.0,
        'orange': 130.0,
        'strawberry': 100.0,
        'avocado': 150.0,
        'tomato': 100.0,
        'cucumber': 100.0,
        'pizza': 300.0,
        'burger': 250.0,
        'sandwich': 150.0,
        'soup': 250.0,
        'cake': 100.0,
        'cookie': 30.0,
        'chocolate': 40.0
    }
    
    # Food density categories (affects weight estimation from visual size)
    DENSITY_MULTIPLIERS = {
        'dense': 1.5,      # Meat, cheese, dense proteins
        'medium': 1.0,     # Most foods
        'light': 0.6,      # Salads, leafy vegetables
        'liquid': 1.0      # Soups, beverages
    }
    
    def estimate_from_bounding_box(
        self,
        food_name: str,
        bounding_box: Dict[str, float],
        image_dimensions: Optional[Tuple[int, int]] = None,
        reference_objects: Optional[List[Dict[str, Any]]] = None
    ) -> PortionEstimate:
        """
        Estimate portion size from bounding box dimensions
        
        Args:
            food_name: Name of the food item
            bounding_box: Dict with x, y, width, height (normalized 0-1)
            image_dimensions: Optional (width, height) of image in pixels
            reference_objects: Optional list of reference objects for scale
            
        Returns:
            PortionEstimate with quantity and confidence
        """
        # Calculate bounding box area
        bbox_area = bounding_box['width'] * bounding_box['height']
        
        # Base estimation on area
        # Typical food item occupies 0.1-0.3 of image area
        # Scale accordingly
        base_weight = 100.0  # Base weight in grams
        area_multiplier = bbox_area / 0.15  # Normalize to typical area
        
        estimated_weight = base_weight * area_multiplier
        
        # Apply food-specific adjustments
        estimated_weight = self._apply_food_density(food_name, estimated_weight)
        
        # Apply reference object scaling if available
        if reference_objects:
            scale_factor = self._calculate_scale_from_references(
                bounding_box, reference_objects
            )
            estimated_weight *= scale_factor
            confidence = 0.8
            method = "bounding_box_with_reference"
        else:
            confidence = 0.6
            method = "bounding_box_only"
        
        # Clamp to reasonable range
        estimated_weight = max(10.0, min(estimated_weight, 1000.0))
        
        return PortionEstimate(
            quantity_g=round(estimated_weight, 1),
            confidence=confidence,
            estimation_method=method
        )
    
    def estimate_from_food_name(self, food_name: str) -> PortionEstimate:
        """
        Estimate portion size based on food name and typical portions
        
        Args:
            food_name: Name of the food item
            
        Returns:
            PortionEstimate with default quantity
        """
        # Try to find matching default portion
        food_lower = food_name.lower()
        
        for key, weight in self.DEFAULT_PORTIONS.items():
            if key in food_lower:
                return PortionEstimate(
                    quantity_g=weight,
                    confidence=0.5,
                    estimation_method="default_portion",
                    reference_used=key
                )
        
        # Generic default
        return PortionEstimate(
            quantity_g=100.0,
            confidence=0.4,
            estimation_method="generic_default"
        )
    
    def _apply_food_density(self, food_name: str, base_weight: float) -> float:
        """Apply density-based adjustments to weight estimation"""
        food_lower = food_name.lower()
        
        # Dense foods (meat, cheese)
        dense_foods = ['chicken', 'beef', 'pork', 'fish', 'meat', 'cheese', 'steak']
        if any(food in food_lower for food in dense_foods):
            return base_weight * self.DENSITY_MULTIPLIERS['dense']
        
        # Light foods (salads, leafy vegetables)
        light_foods = ['salad', 'lettuce', 'spinach', 'arugula', 'kale']
        if any(food in food_lower for food in light_foods):
            return base_weight * self.DENSITY_MULTIPLIERS['light']
        
        # Liquid foods
        liquid_foods = ['soup', 'juice', 'milk', 'smoothie', 'beverage']
        if any(food in food_lower for food in liquid_foods):
            return base_weight * self.DENSITY_MULTIPLIERS['liquid']
        
        return base_weight
    
    def _calculate_scale_from_references(
        self,
        food_bbox: Dict[str, float],
        reference_objects: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate scale factor using reference objects (plates, utensils)
        
        Args:
            food_bbox: Bounding box of the food item
            reference_objects: List of detected reference objects
            
        Returns:
            Scale factor to apply to weight estimation
        """
        # Known sizes of reference objects (in cm)
        REFERENCE_SIZES = {
            'plate': 25.0,      # Standard dinner plate diameter
            'fork': 18.0,       # Standard fork length
            'knife': 20.0,      # Standard knife length
            'spoon': 15.0,      # Standard spoon length
            'cup': 8.0,         # Standard cup diameter
            'glass': 7.0        # Standard glass diameter
        }
        
        # Find closest reference object
        for ref_obj in reference_objects:
            ref_type = ref_obj.get('type', '').lower()
            ref_bbox = ref_obj.get('bounding_box')
            
            if ref_type in REFERENCE_SIZES and ref_bbox:
                # Calculate relative size
                ref_size = max(ref_bbox['width'], ref_bbox['height'])
                food_size = max(food_bbox['width'], food_bbox['height'])
                
                # Scale factor based on reference
                scale_factor = (food_size / ref_size) * 1.2
                return max(0.5, min(scale_factor, 2.0))  # Clamp to reasonable range
        
        return 1.0  # No scaling if no valid reference found


class NutritionCalculator:
    """
    Main nutrition calculation engine
    Implements Requirement 3.3: Macro/micronutrient calculation logic
    """
    
    def __init__(self, food_database_service):
        """
        Initialize nutrition calculator
        
        Args:
            food_database_service: Service for accessing food database
        """
        self.nutrition_lookup = NutritionDataLookup(food_database_service)
        self.portion_estimator = PortionEstimator()
    
    def calculate_portion_nutrition(
        self,
        food_name: str,
        portion_g: float
    ) -> Optional[CalculatedNutrition]:
        """
        Calculate nutrition for a specific portion of food
        
        Args:
            food_name: Name of the food item
            portion_g: Portion size in grams
            
        Returns:
            CalculatedNutrition with values for the portion
        """
        # Look up base nutrition data (per 100g)
        base_nutrition = self.nutrition_lookup.lookup_nutrition(food_name)
        
        if not base_nutrition:
            logger.warning(f"Could not calculate nutrition for {food_name}: no data found")
            return None
        
        # Calculate multiplier for portion
        multiplier = portion_g / 100.0
        
        # Scale all nutrition values
        portion_nutrition = NutritionData(
            calories=base_nutrition.calories * multiplier,
            protein_g=base_nutrition.protein_g * multiplier,
            carbs_g=base_nutrition.carbs_g * multiplier,
            fat_g=base_nutrition.fat_g * multiplier,
            fiber_g=base_nutrition.fiber_g * multiplier,
            sugar_g=base_nutrition.sugar_g * multiplier,
            sodium_mg=base_nutrition.sodium_mg * multiplier,
            potassium_mg=base_nutrition.potassium_mg * multiplier,
            calcium_mg=base_nutrition.calcium_mg * multiplier,
            iron_mg=base_nutrition.iron_mg * multiplier,
            vitamin_c_mg=base_nutrition.vitamin_c_mg * multiplier,
            vitamin_d_ug=base_nutrition.vitamin_d_ug * multiplier
        )
        
        return CalculatedNutrition(
            portion_g=portion_g,
            nutrition=portion_nutrition
        )
    
    def calculate_total_nutrition(
        self,
        food_items: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate total nutrition from multiple food items
        
        Args:
            food_items: List of dicts with 'food_name' and 'portion_g'
            
        Returns:
            Dictionary with total nutrition values
        """
        totals = {
            'calories': 0.0,
            'protein_g': 0.0,
            'carbs_g': 0.0,
            'fat_g': 0.0,
            'fiber_g': 0.0,
            'sugar_g': 0.0,
            'sodium_mg': 0.0,
            'potassium_mg': 0.0,
            'calcium_mg': 0.0,
            'iron_mg': 0.0,
            'vitamin_c_mg': 0.0,
            'vitamin_d_ug': 0.0
        }
        
        for item in food_items:
            food_name = item.get('food_name')
            portion_g = item.get('portion_g', 100.0)
            
            if not food_name:
                continue
            
            # Calculate nutrition for this item
            calculated = self.calculate_portion_nutrition(food_name, portion_g)
            
            if calculated:
                nutrition_dict = calculated.nutrition.to_dict()
                for key in totals.keys():
                    totals[key] += nutrition_dict.get(key, 0.0)
        
        # Round to 1 decimal place
        return {k: round(v, 1) for k, v in totals.items()}
    
    def calculate_macronutrient_distribution(
        self,
        nutrition: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate macronutrient distribution as percentages
        
        Args:
            nutrition: Dictionary with nutrition values
            
        Returns:
            Dictionary with percentage distribution
        """
        protein_g = nutrition.get('protein_g', 0.0)
        carbs_g = nutrition.get('carbs_g', 0.0)
        fat_g = nutrition.get('fat_g', 0.0)
        
        # Calculate calories from each macro
        protein_cal = protein_g * 4
        carbs_cal = carbs_g * 4
        fat_cal = fat_g * 9
        
        total_cal = protein_cal + carbs_cal + fat_cal
        
        if total_cal == 0:
            return {
                'protein_percent': 0.0,
                'carbs_percent': 0.0,
                'fat_percent': 0.0
            }
        
        return {
            'protein_percent': round((protein_cal / total_cal) * 100, 1),
            'carbs_percent': round((carbs_cal / total_cal) * 100, 1),
            'fat_percent': round((fat_cal / total_cal) * 100, 1)
        }
    
    def estimate_and_calculate(
        self,
        food_name: str,
        bounding_box: Optional[Dict[str, float]] = None,
        image_dimensions: Optional[Tuple[int, int]] = None
    ) -> Optional[CalculatedNutrition]:
        """
        Estimate portion size and calculate nutrition in one step
        
        Args:
            food_name: Name of the food item
            bounding_box: Optional bounding box for portion estimation
            image_dimensions: Optional image dimensions
            
        Returns:
            CalculatedNutrition with estimated portion and nutrition
        """
        # Estimate portion size
        if bounding_box:
            portion_estimate = self.portion_estimator.estimate_from_bounding_box(
                food_name, bounding_box, image_dimensions
            )
        else:
            portion_estimate = self.portion_estimator.estimate_from_food_name(food_name)
        
        # Calculate nutrition for estimated portion
        return self.calculate_portion_nutrition(food_name, portion_estimate.quantity_g)
