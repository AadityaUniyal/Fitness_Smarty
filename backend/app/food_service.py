"""
Food Database Service

Provides comprehensive food database management with USDA integration,
fuzzy search capabilities, and data validation.
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fuzzywuzzy import fuzz, process
from decimal import Decimal
import uuid

try:
    from .models import Food, NutritionFact
except ImportError:
    from .models import FoodItem as Food
    NutritionFact = None  # Not available in current schema
from .usda_integration_service import USDAIntegrationService


class FoodValidationError(Exception):
    """Raised when food data validation fails"""
    pass


class FoodDataValidator:
    """Validates food and nutrition data for completeness and accuracy"""
    
    REQUIRED_FIELDS = ["name", "serving_size_g"]
    REQUIRED_NUTRITION_FIELDS = ["calories_per_100g", "protein_g", "carbs_g", "fat_g"]
    
    # Reasonable ranges for nutritional values per 100g
    NUTRITION_RANGES = {
        "calories_per_100g": (0, 900),
        "protein_g": (0, 100),
        "carbs_g": (0, 100),
        "fat_g": (0, 100),
        "fiber_g": (0, 50),
        "sugar_g": (0, 100),
        "sodium_mg": (0, 10000),
        "potassium_mg": (0, 5000),
        "calcium_mg": (0, 2000),
        "iron_mg": (0, 100),
        "vitamin_c_mg": (0, 1000),
        "vitamin_d_ug": (0, 100)
    }
    
    @classmethod
    def validate_food_data(cls, food_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate food data for required fields and reasonable values
        
        Args:
            food_data: Dictionary containing food information
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in food_data or food_data[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Validate serving size
        if "serving_size_g" in food_data and food_data["serving_size_g"] is not None:
            serving_size = float(food_data["serving_size_g"])
            if serving_size <= 0 or serving_size > 10000:
                errors.append(f"Invalid serving size: {serving_size}g (must be 0-10000g)")
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_nutrition_data(cls, nutrition_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate nutrition data for completeness and reasonable ranges
        
        Args:
            nutrition_data: Dictionary containing nutrition facts
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        warnings = []
        
        # Check required nutrition fields
        missing_fields = []
        for field in cls.REQUIRED_NUTRITION_FIELDS:
            if field not in nutrition_data or nutrition_data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            errors.append(f"Missing required nutrition fields: {', '.join(missing_fields)}")
        
        # Validate ranges for present fields
        for field, (min_val, max_val) in cls.NUTRITION_RANGES.items():
            if field in nutrition_data and nutrition_data[field] is not None:
                value = float(nutrition_data[field])
                if value < min_val or value > max_val:
                    warnings.append(
                        f"{field} value {value} outside typical range ({min_val}-{max_val})"
                    )
        
        # Check macronutrient balance (calories should roughly match macros)
        if all(field in nutrition_data and nutrition_data[field] is not None 
               for field in ["calories_per_100g", "protein_g", "carbs_g", "fat_g"]):
            
            calculated_calories = (
                float(nutrition_data["protein_g"]) * 4 +
                float(nutrition_data["carbs_g"]) * 4 +
                float(nutrition_data["fat_g"]) * 9
            )
            stated_calories = float(nutrition_data["calories_per_100g"])
            
            # Allow 20% variance
            if abs(calculated_calories - stated_calories) > stated_calories * 0.2:
                warnings.append(
                    f"Calorie mismatch: stated {stated_calories} vs calculated {calculated_calories:.1f}"
                )
        
        return len(errors) == 0, errors + warnings
    
    @classmethod
    def check_completeness(cls, nutrition_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check nutrition data completeness and return missing fields
        
        Args:
            nutrition_data: Dictionary containing nutrition facts
            
        Returns:
            Dictionary with completeness information
        """
        all_fields = list(cls.NUTRITION_RANGES.keys())
        present_fields = [f for f in all_fields if f in nutrition_data and nutrition_data[f] is not None]
        missing_fields = [f for f in all_fields if f not in present_fields]
        
        return {
            "completeness_percentage": (len(present_fields) / len(all_fields)) * 100,
            "present_fields": present_fields,
            "missing_fields": missing_fields,
            "has_required_fields": all(
                f in present_fields for f in cls.REQUIRED_NUTRITION_FIELDS
            )
        }


class FoodSearchEngine:
    """Advanced food search with fuzzy matching capabilities"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def exact_search(self, query: str, limit: int = 25) -> List[Food]:
        """
        Perform exact search on food names
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching Food objects
        """
        return self.db.query(Food).filter(
            or_(
                Food.name.ilike(f"%{query}%"),
                Food.brand.ilike(f"%{query}%")
            )
        ).limit(limit).all()
    
    def fuzzy_search(self, query: str, threshold: int = 60, limit: int = 25) -> List[Tuple[Food, int]]:
        """
        Perform fuzzy search on food names with similarity scoring
        
        Args:
            query: Search query
            threshold: Minimum similarity score (0-100)
            limit: Maximum results to return
            
        Returns:
            List of tuples (Food object, similarity_score)
        """
        # Get all foods from database
        all_foods = self.db.query(Food).all()
        
        # Calculate similarity scores
        scored_foods = []
        for food in all_foods:
            # Calculate similarity for name
            name_score = fuzz.partial_ratio(query.lower(), food.name.lower())
            
            # Calculate similarity for brand if present
            brand_score = 0
            if food.brand:
                brand_score = fuzz.partial_ratio(query.lower(), food.brand.lower())
            
            # Use the higher score
            max_score = max(name_score, brand_score)
            
            if max_score >= threshold:
                scored_foods.append((food, max_score))
        
        # Sort by score descending
        scored_foods.sort(key=lambda x: x[1], reverse=True)
        
        return scored_foods[:limit]
    
    def search_by_category(self, category: str, limit: int = 50) -> List[Food]:
        """
        Search foods by category
        
        Args:
            category: Food category
            limit: Maximum results to return
            
        Returns:
            List of Food objects
        """
        return self.db.query(Food).filter(
            Food.category.ilike(f"%{category}%")
        ).limit(limit).all()
    
    def search_with_nutrition_filter(
        self,
        query: str,
        max_calories: Optional[float] = None,
        min_protein: Optional[float] = None,
        max_carbs: Optional[float] = None,
        max_fat: Optional[float] = None,
        limit: int = 25
    ) -> List[Food]:
        """
        Search foods with nutritional filters
        
        Args:
            query: Search query
            max_calories: Maximum calories per 100g
            min_protein: Minimum protein per 100g
            max_carbs: Maximum carbs per 100g
            max_fat: Maximum fat per 100g
            limit: Maximum results to return
            
        Returns:
            List of Food objects matching criteria
        """
        query_obj = self.db.query(Food).join(NutritionFact)
        
        # Apply text search
        if query:
            query_obj = query_obj.filter(
                or_(
                    Food.name.ilike(f"%{query}%"),
                    Food.brand.ilike(f"%{query}%")
                )
            )
        
        # Apply nutrition filters
        if max_calories is not None:
            query_obj = query_obj.filter(NutritionFact.calories_per_100g <= max_calories)
        if min_protein is not None:
            query_obj = query_obj.filter(NutritionFact.protein_g >= min_protein)
        if max_carbs is not None:
            query_obj = query_obj.filter(NutritionFact.carbs_g <= max_carbs)
        if max_fat is not None:
            query_obj = query_obj.filter(NutritionFact.fat_g <= max_fat)
        
        return query_obj.limit(limit).all()


class FoodDatabaseService:
    """Main service for food database operations"""
    
    def __init__(self, db: Session, usda_service: Optional[USDAIntegrationService] = None):
        self.db = db
        self.usda_service = usda_service
        self.validator = FoodDataValidator()
        self.search_engine = FoodSearchEngine(db)
    
    def create_food(self, food_data: Dict[str, Any], nutrition_data: Dict[str, Any]) -> Food:
        """
        Create a new food entry with nutrition facts
        
        Args:
            food_data: Dictionary with food information
            nutrition_data: Dictionary with nutrition facts
            
        Returns:
            Created Food object
            
        Raises:
            FoodValidationError: If validation fails
        """
        # Validate food data
        is_valid, errors = self.validator.validate_food_data(food_data)
        if not is_valid:
            raise FoodValidationError(f"Food validation failed: {'; '.join(errors)}")
        
        # Validate nutrition data
        is_valid, errors = self.validator.validate_nutrition_data(nutrition_data)
        if not is_valid:
            raise FoodValidationError(f"Nutrition validation failed: {'; '.join(errors)}")
        
        # Create food entry
        food = Food(
            id=uuid.uuid4(),
            fdc_id=food_data.get("fdc_id"),
            name=food_data["name"],
            brand=food_data.get("brand"),
            category=food_data.get("category"),
            serving_size_g=Decimal(str(food_data["serving_size_g"])),
            serving_description=food_data.get("serving_description")
        )
        
        self.db.add(food)
        self.db.flush()  # Get the food ID
        
        # Create nutrition facts
        nutrition = NutritionFact(
            id=uuid.uuid4(),
            food_id=food.id,
            calories_per_100g=Decimal(str(nutrition_data["calories_per_100g"])) if nutrition_data.get("calories_per_100g") else None,
            protein_g=Decimal(str(nutrition_data["protein_g"])) if nutrition_data.get("protein_g") else None,
            carbs_g=Decimal(str(nutrition_data["carbs_g"])) if nutrition_data.get("carbs_g") else None,
            fat_g=Decimal(str(nutrition_data["fat_g"])) if nutrition_data.get("fat_g") else None,
            fiber_g=Decimal(str(nutrition_data["fiber_g"])) if nutrition_data.get("fiber_g") else None,
            sugar_g=Decimal(str(nutrition_data["sugar_g"])) if nutrition_data.get("sugar_g") else None,
            sodium_mg=Decimal(str(nutrition_data["sodium_mg"])) if nutrition_data.get("sodium_mg") else None,
            potassium_mg=Decimal(str(nutrition_data["potassium_mg"])) if nutrition_data.get("potassium_mg") else None,
            calcium_mg=Decimal(str(nutrition_data["calcium_mg"])) if nutrition_data.get("calcium_mg") else None,
            iron_mg=Decimal(str(nutrition_data["iron_mg"])) if nutrition_data.get("iron_mg") else None,
            vitamin_c_mg=Decimal(str(nutrition_data["vitamin_c_mg"])) if nutrition_data.get("vitamin_c_mg") else None,
            vitamin_d_ug=Decimal(str(nutrition_data["vitamin_d_ug"])) if nutrition_data.get("vitamin_d_ug") else None
        )
        
        self.db.add(nutrition)
        self.db.commit()
        self.db.refresh(food)
        
        return food
    
    def get_food_by_id(self, food_id: uuid.UUID) -> Optional[Food]:
        """Get food by ID"""
        return self.db.query(Food).filter(Food.id == food_id).first()
    
    def get_food_by_fdc_id(self, fdc_id: int) -> Optional[Food]:
        """Get food by USDA FDC ID"""
        return self.db.query(Food).filter(Food.fdc_id == fdc_id).first()
    
    def search_foods(self, query: str, use_fuzzy: bool = True, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Search for foods with optional fuzzy matching
        
        Args:
            query: Search query
            use_fuzzy: Whether to use fuzzy matching
            limit: Maximum results
            
        Returns:
            List of food dictionaries with nutrition data
        """
        if use_fuzzy:
            results = self.search_engine.fuzzy_search(query, limit=limit)
            foods = [food for food, score in results]
        else:
            foods = self.search_engine.exact_search(query, limit=limit)
        
        return [self._food_to_dict(food) for food in foods]
    
    def import_from_usda(self, query: str, limit: int = 10) -> List[Food]:
        """
        Search USDA database and import foods
        
        Args:
            query: Search query
            limit: Maximum foods to import
            
        Returns:
            List of imported Food objects
        """
        if not self.usda_service:
            raise Exception("USDA service not configured")
        
        # Search and extract nutrition data from USDA
        usda_foods = self.usda_service.search_and_extract(query, limit=limit)
        
        imported_foods = []
        for usda_food in usda_foods:
            # Check if food already exists
            if usda_food.get("fdc_id"):
                existing = self.get_food_by_fdc_id(usda_food["fdc_id"])
                if existing:
                    continue
            
            try:
                # Prepare food and nutrition data
                food_data = {
                    "fdc_id": usda_food.get("fdc_id"),
                    "name": usda_food["name"],
                    "brand": usda_food.get("brand"),
                    "category": usda_food.get("category"),
                    "serving_size_g": usda_food.get("serving_size_g", 100),
                    "serving_description": usda_food.get("serving_description", "100g")
                }
                
                nutrition_data = {
                    k: v for k, v in usda_food.items()
                    if k in self.validator.NUTRITION_RANGES
                }
                
                # Create food entry
                food = self.create_food(food_data, nutrition_data)
                imported_foods.append(food)
                
            except Exception as e:
                print(f"Error importing food {usda_food.get('name')}: {e}")
                continue
        
        return imported_foods
    
    def _food_to_dict(self, food: Food) -> Dict[str, Any]:
        """Convert Food object to dictionary with nutrition data"""
        result = {
            "id": str(food.id),
            "fdc_id": food.fdc_id,
            "name": food.name,
            "brand": food.brand,
            "category": food.category,
            "serving_size_g": float(food.serving_size_g) if food.serving_size_g else None,
            "serving_description": food.serving_description,
            "nutrition": None
        }
        
        if food.nutrition_facts:
            nf = food.nutrition_facts
            result["nutrition"] = {
                "calories_per_100g": float(nf.calories_per_100g) if nf.calories_per_100g is not None else None,
                "protein_g": float(nf.protein_g) if nf.protein_g is not None else None,
                "carbs_g": float(nf.carbs_g) if nf.carbs_g is not None else None,
                "fat_g": float(nf.fat_g) if nf.fat_g is not None else None,
                "fiber_g": float(nf.fiber_g) if nf.fiber_g is not None else None,
                "sugar_g": float(nf.sugar_g) if nf.sugar_g is not None else None,
                "sodium_mg": float(nf.sodium_mg) if nf.sodium_mg is not None else None,
                "potassium_mg": float(nf.potassium_mg) if nf.potassium_mg is not None else None,
                "calcium_mg": float(nf.calcium_mg) if nf.calcium_mg is not None else None,
                "iron_mg": float(nf.iron_mg) if nf.iron_mg is not None else None,
                "vitamin_c_mg": float(nf.vitamin_c_mg) if nf.vitamin_c_mg is not None else None,
                "vitamin_d_ug": float(nf.vitamin_d_ug) if nf.vitamin_d_ug is not None else None
            }
            
            # Add completeness info
            result["completeness"] = self.validator.check_completeness(result["nutrition"])
        
        return result
