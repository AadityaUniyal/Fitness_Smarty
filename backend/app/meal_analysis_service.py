"""
Meal Analysis Service
Orchestrates the complete meal analysis workflow:
1. Image processing and validation
2. Food detection using computer vision
3. Nutrition data lookup
4. Portion estimation
5. Result storage and recommendation generation
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal
import logging
import datetime
import uuid

from .image_processor import ImageProcessor, ImageValidationError
from .food_detection_model import FoodDetectionModel, FoodDetectionResult, DetectedFood
from .food_service import FoodDatabaseService
from .nutrition_calculator import NutritionCalculator
from .models import MealLog, MealComponent
from .error_handler import (
    retry_on_failure, graceful_degradation, error_handler,
    AIAnalysisError, ExternalAPIError, ErrorCategory
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class MealAnalysisResult:
    """Complete result of meal analysis"""
    success: bool
    meal_log_id: Optional[str]
    image_url: str
    detected_foods: List[Dict[str, Any]]
    total_nutrition: Dict[str, float]
    analysis_confidence: float
    recommendations: List[str]
    requires_manual_review: bool
    error_message: Optional[str] = None


class MealAnalysisService:
    """
    Complete meal analysis service integrating all components
    """
    
    def __init__(
        self, 
        db: Session,
        image_processor: Optional[ImageProcessor] = None,
        food_detection_model: Optional[FoodDetectionModel] = None,
        food_service: Optional[FoodDatabaseService] = None,
        nutrition_calculator: Optional[NutritionCalculator] = None
    ):
        """
        Initialize MealAnalysisService
        
        Args:
            db: Database session
            image_processor: Image processing component
            food_detection_model: Food detection model
            food_service: Food database service
            nutrition_calculator: Nutrition calculation engine
        """
        self.db = db
        self.image_processor = image_processor or ImageProcessor()
        self.food_detection_model = food_detection_model or FoodDetectionModel()
        self.food_service = food_service or FoodDatabaseService(db)
        self.nutrition_calculator = nutrition_calculator or NutritionCalculator(self.food_service)
    
    def analyze_meal_photo(
        self, 
        image_bytes: bytes, 
        user_id: str,
        meal_type: str = "lunch"
    ) -> MealAnalysisResult:
        """
        Complete meal analysis workflow
        
        Args:
            image_bytes: Raw image data
            user_id: User identifier
            meal_type: Type of meal (breakfast, lunch, dinner, snack)
            
        Returns:
            MealAnalysisResult with complete analysis
        """
        try:
            # Step 1: Process and validate image
            logger.info(f"Starting meal analysis for user {user_id}")
            
            try:
                image_result = self.image_processor.process_meal_image(image_bytes, user_id)
                image_url = image_result['storage_url']
                logger.info(f"Image processed successfully: {image_url}")
            except ImageValidationError as e:
                logger.error(f"Image validation failed: {str(e)}")
                return MealAnalysisResult(
                    success=False,
                    meal_log_id=None,
                    image_url="",
                    detected_foods=[],
                    total_nutrition={},
                    analysis_confidence=0.0,
                    recommendations=["Please check your image and try again", "You can enter meal details manually"],
                    requires_manual_review=True,
                    error_message=f"Image validation failed: {str(e)}"
                )
            
            # Step 2: Assess image quality
            quality_assessment = self.image_processor.assess_image_quality(image_bytes)
            if not quality_assessment['suitable_for_analysis']:
                logger.warning(f"Image quality issues detected: {quality_assessment['issues']}")
                # Add manual entry recommendation
                recommendations = quality_assessment['recommendations'] + [
                    "Alternatively, you can enter meal details manually"
                ]
                return MealAnalysisResult(
                    success=False,
                    meal_log_id=None,
                    image_url=image_url,
                    detected_foods=[],
                    total_nutrition={},
                    analysis_confidence=0.0,
                    recommendations=recommendations,
                    requires_manual_review=True,
                    error_message="Image quality too low for analysis. " + "; ".join(quality_assessment['issues'])
                )
            
            # Step 3: Detect foods using computer vision
            optimized_bytes = self.image_processor.optimize_for_analysis(image_bytes)
            detection_result = self.food_detection_model.detect_foods(optimized_bytes)
            logger.info(f"Food detection complete: {len(detection_result.detected_foods)} items detected")
            
            # Step 4: Check if fallback to manual entry is needed
            if self.food_detection_model.should_request_manual_entry(detection_result):
                fallback_msg = self.food_detection_model.get_fallback_message(detection_result)
                logger.warning(f"Manual entry required: {fallback_msg}")
                return MealAnalysisResult(
                    success=False,
                    meal_log_id=None,
                    image_url=image_url,
                    detected_foods=[],
                    total_nutrition={},
                    analysis_confidence=detection_result.overall_confidence,
                    recommendations=[fallback_msg],
                    requires_manual_review=True,
                    error_message=fallback_msg
                )
            
            # Step 5: Lookup nutrition data for detected foods
            enriched_foods = []
            for detected_food in detection_result.detected_foods:
                enriched_food = self._enrich_detected_food(detected_food, optimized_bytes)
                if enriched_food:
                    enriched_foods.append(enriched_food)
            
            if not enriched_foods:
                logger.error("No foods could be enriched with nutrition data")
                return MealAnalysisResult(
                    success=False,
                    meal_log_id=None,
                    image_url=image_url,
                    detected_foods=[],
                    total_nutrition={},
                    analysis_confidence=detection_result.overall_confidence,
                    recommendations=["Could not find nutrition data for detected foods. Please enter manually."],
                    requires_manual_review=True,
                    error_message="Nutrition data lookup failed"
                )
            
            # Step 6: Calculate total nutrition
            total_nutrition = self._calculate_total_nutrition(enriched_foods)
            logger.info(f"Total nutrition calculated: {total_nutrition['calories']} calories")
            
            # Step 7: Store meal log in database
            meal_log = self._store_meal_log(
                user_id=user_id,
                meal_type=meal_type,
                image_url=image_url,
                enriched_foods=enriched_foods,
                total_nutrition=total_nutrition,
                confidence=detection_result.overall_confidence
            )
            
            # Step 8: Generate recommendations
            recommendations = self._generate_recommendations(
                total_nutrition=total_nutrition,
                detected_foods=enriched_foods,
                confidence=detection_result.overall_confidence
            )
            
            # Step 9: Determine if manual review is needed
            requires_review = detection_result.overall_confidence < 0.7
            
            logger.info(f"Meal analysis complete for user {user_id}: meal_log_id={meal_log.id}")
            
            return MealAnalysisResult(
                success=True,
                meal_log_id=str(meal_log.id),
                image_url=image_url,
                detected_foods=[self._format_detected_food(f) for f in enriched_foods],
                total_nutrition=total_nutrition,
                analysis_confidence=detection_result.overall_confidence,
                recommendations=recommendations,
                requires_manual_review=requires_review,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Meal analysis failed with exception: {str(e)}", exc_info=True)
            return MealAnalysisResult(
                success=False,
                meal_log_id=None,
                image_url="",
                detected_foods=[],
                total_nutrition={},
                analysis_confidence=0.0,
                recommendations=["An error occurred during analysis. Please try again or enter manually."],
                requires_manual_review=True,
                error_message=f"Analysis error: {str(e)}"
            )
    
    def _enrich_detected_food(
        self, 
        detected_food: DetectedFood, 
        image_bytes: bytes
    ) -> Optional[Dict[str, Any]]:
        """
        Enrich detected food with nutrition data and portion estimation
        
        Args:
            detected_food: Detected food from computer vision
            image_bytes: Image data for portion estimation
            
        Returns:
            Enriched food dict with nutrition data
        """
        try:
            # Lookup food in database
            food_results = self.food_service.search_foods(detected_food.food_name, limit=1)
            
            if not food_results:
                logger.warning(f"No nutrition data found for: {detected_food.food_name}")
                return None
            
            food_data = food_results[0]
            
            # Estimate portion size
            portion_g = self.food_detection_model.estimate_portion_size(
                detected_food, 
                image_bytes
            )
            
            # Calculate nutrition for this portion
            nutrition = self._calculate_portion_nutrition(food_data, portion_g)
            
            return {
                'food_id': food_data.get('id'),
                'food_name': detected_food.food_name,
                'confidence_score': detected_food.confidence_score,
                'bounding_box': detected_food.bounding_box,
                'estimated_quantity_g': portion_g,
                'nutrition': nutrition
            }
            
        except Exception as e:
            logger.error(f"Failed to enrich food {detected_food.food_name}: {str(e)}")
            return None
    
    def _calculate_portion_nutrition(
        self, 
        food_data: Dict[str, Any], 
        portion_g: float
    ) -> Dict[str, float]:
        """
        Calculate nutrition for a specific portion size
        
        Note: This method is kept for backward compatibility.
        The new NutritionCalculator module provides more comprehensive
        nutrition calculation capabilities.
        
        Args:
            food_data: Food nutrition data (per 100g)
            portion_g: Portion size in grams
            
        Returns:
            Nutrition values for the portion
        """
        # Get nutrition facts (per 100g)
        nutrition_facts = food_data.get('nutrition_facts', {})
        
        # Calculate multiplier
        multiplier = portion_g / 100.0
        
        return {
            'calories': float(nutrition_facts.get('calories_per_100g', 0)) * multiplier,
            'protein_g': float(nutrition_facts.get('protein_g', 0)) * multiplier,
            'carbs_g': float(nutrition_facts.get('carbs_g', 0)) * multiplier,
            'fat_g': float(nutrition_facts.get('fat_g', 0)) * multiplier,
            'fiber_g': float(nutrition_facts.get('fiber_g', 0)) * multiplier,
            'sugar_g': float(nutrition_facts.get('sugar_g', 0)) * multiplier,
        }
    
    def _calculate_total_nutrition(self, enriched_foods: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate total nutrition from all detected foods
        
        Args:
            enriched_foods: List of enriched food items
            
        Returns:
            Total nutrition values
        """
        totals = {
            'calories': 0.0,
            'protein_g': 0.0,
            'carbs_g': 0.0,
            'fat_g': 0.0,
            'fiber_g': 0.0,
            'sugar_g': 0.0,
        }
        
        for food in enriched_foods:
            nutrition = food.get('nutrition', {})
            for key in totals.keys():
                totals[key] += nutrition.get(key, 0.0)
        
        # Round to 1 decimal place
        return {k: round(v, 1) for k, v in totals.items()}
    
    def _store_meal_log(
        self,
        user_id: str,
        meal_type: str,
        image_url: str,
        enriched_foods: List[Dict[str, Any]],
        total_nutrition: Dict[str, float],
        confidence: float
    ) -> MealLog:
        """
        Store meal log and components in database
        
        Args:
            user_id: User identifier
            meal_type: Type of meal
            image_url: URL of stored image
            enriched_foods: List of detected foods with nutrition
            total_nutrition: Total nutrition values
            confidence: Overall analysis confidence
            
        Returns:
            Created MealLog object
        """
        # Create meal log
        meal_log = MealLog(
            user_id=user_id,
            meal_type=meal_type,
            image_url=image_url,
            analysis_confidence=Decimal(str(round(confidence, 2))),
            total_calories=Decimal(str(round(total_nutrition['calories'], 2))),
            total_protein_g=Decimal(str(round(total_nutrition['protein_g'], 2))),
            total_carbs_g=Decimal(str(round(total_nutrition['carbs_g'], 2))),
            total_fat_g=Decimal(str(round(total_nutrition['fat_g'], 2)))
        )
        
        self.db.add(meal_log)
        self.db.flush()  # Get meal_log.id
        
        # Create meal components
        for food in enriched_foods:
            component = MealComponent(
                meal_log_id=meal_log.id,
                food_id=food.get('food_id'),
                estimated_quantity_g=Decimal(str(round(food['estimated_quantity_g'], 2))),
                confidence_score=Decimal(str(round(food['confidence_score'], 2)))
            )
            self.db.add(component)
        
        self.db.commit()
        
        return meal_log
    
    def _generate_recommendations(
        self,
        total_nutrition: Dict[str, float],
        detected_foods: List[Dict[str, Any]],
        confidence: float
    ) -> List[str]:
        """
        Generate personalized recommendations based on meal analysis
        
        Args:
            total_nutrition: Total nutrition values
            detected_foods: List of detected foods
            confidence: Analysis confidence
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Confidence-based recommendations
        if confidence < 0.7:
            recommendations.append(
                "Please review the detected items for accuracy. "
                "You can edit quantities or add missing items."
            )
        
        # Nutrition-based recommendations
        calories = total_nutrition.get('calories', 0)
        protein = total_nutrition.get('protein_g', 0)
        carbs = total_nutrition.get('carbs_g', 0)
        fat = total_nutrition.get('fat_g', 0)
        
        # Calorie recommendations
        if calories > 800:
            recommendations.append(
                f"This meal is quite substantial at {calories:.0f} calories. "
                "Consider balancing with lighter meals throughout the day."
            )
        elif calories < 300:
            recommendations.append(
                f"This meal is relatively light at {calories:.0f} calories. "
                "Make sure you're meeting your daily calorie goals."
            )
        
        # Protein recommendations
        if protein < 15:
            recommendations.append(
                "This meal is low in protein. Consider adding lean meat, fish, eggs, or legumes."
            )
        elif protein > 50:
            recommendations.append(
                f"Great protein content ({protein:.0f}g)! This will help with muscle recovery and satiety."
            )
        
        # Macronutrient balance
        total_macros = protein + carbs + fat
        if total_macros > 0:
            protein_pct = (protein * 4 / (calories or 1)) * 100
            carbs_pct = (carbs * 4 / (calories or 1)) * 100
            fat_pct = (fat * 9 / (calories or 1)) * 100
            
            if carbs_pct > 60:
                recommendations.append(
                    "This meal is carb-heavy. Consider adding more protein or healthy fats for balance."
                )
            elif fat_pct > 40:
                recommendations.append(
                    "This meal is high in fats. Balance with vegetables and lean proteins."
                )
        
        # Variety recommendations
        if len(detected_foods) == 1:
            recommendations.append(
                "Try adding more variety to your meals with vegetables, whole grains, or fruits."
            )
        
        # Default positive message if no specific recommendations
        if not recommendations:
            recommendations.append(
                f"Meal logged successfully! Total: {calories:.0f} calories, "
                f"{protein:.0f}g protein, {carbs:.0f}g carbs, {fat:.0f}g fat."
            )
        
        return recommendations
    
    def _format_detected_food(self, enriched_food: Dict[str, Any]) -> Dict[str, Any]:
        """Format enriched food for API response"""
        return {
            'food_name': enriched_food['food_name'],
            'confidence_score': round(enriched_food['confidence_score'], 2),
            'estimated_quantity_g': round(enriched_food['estimated_quantity_g'], 1),
            'nutrition': {
                k: round(v, 1) for k, v in enriched_food['nutrition'].items()
            },
            'bounding_box': enriched_food.get('bounding_box')
        }
    
    def get_meal_log(self, meal_log_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a meal log with all components
        
        Args:
            meal_log_id: Meal log identifier (string or UUID)
            
        Returns:
            Meal log data with components
        """
        try:
            # Convert string to UUID if needed
            if isinstance(meal_log_id, str):
                meal_log_id = uuid.UUID(meal_log_id)
            
            meal_log = self.db.query(MealLog).filter(MealLog.id == meal_log_id).first()
            
            if not meal_log:
                return None
            
            # Get components
            components = []
            for component in meal_log.components:
                food = component.food
                components.append({
                    'food_name': food.name if food else 'Unknown',
                    'quantity_g': float(component.estimated_quantity_g),
                    'confidence_score': float(component.confidence_score)
                })
            
            return {
                'id': str(meal_log.id),
                'meal_log_id': str(meal_log.id),
                'user_id': str(meal_log.user_id),
                'meal_type': meal_log.meal_type,
                'logged_at': meal_log.logged_at.isoformat(),
                'image_url': meal_log.image_url,
                'analysis_confidence': float(meal_log.analysis_confidence),
                'total_nutrition': {
                    'calories': float(meal_log.total_calories),
                    'protein_g': float(meal_log.total_protein_g),
                    'carbs_g': float(meal_log.total_carbs_g),
                    'fat_g': float(meal_log.total_fat_g)
                },
                'components': components
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve meal log {meal_log_id}: {str(e)}")
            return None
    
    def get_user_meal_history(
        self,
        user_id: str,
        start_date: Optional[datetime.datetime] = None,
        end_date: Optional[datetime.datetime] = None,
        meal_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Retrieve historical meal logs for a user with filtering options
        
        Args:
            user_id: User identifier (string or UUID)
            start_date: Filter meals after this date (inclusive)
            end_date: Filter meals before this date (inclusive)
            meal_type: Filter by meal type (breakfast, lunch, dinner, snack)
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            Dictionary with meal logs and metadata
        """
        try:
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
            
            # Build query
            query = self.db.query(MealLog).filter(MealLog.user_id == user_id)
            
            # Apply filters
            if start_date:
                query = query.filter(MealLog.logged_at >= start_date)
            if end_date:
                query = query.filter(MealLog.logged_at <= end_date)
            if meal_type:
                query = query.filter(MealLog.meal_type == meal_type)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply ordering and pagination
            meal_logs = query.order_by(MealLog.logged_at.desc()).limit(limit).offset(offset).all()
            
            # Format results
            meals = []
            for meal_log in meal_logs:
                meals.append({
                    'meal_log_id': str(meal_log.id),
                    'meal_type': meal_log.meal_type,
                    'logged_at': meal_log.logged_at.isoformat(),
                    'image_url': meal_log.image_url,
                    'analysis_confidence': float(meal_log.analysis_confidence),
                    'total_nutrition': {
                        'calories': float(meal_log.total_calories),
                        'protein_g': float(meal_log.total_protein_g),
                        'carbs_g': float(meal_log.total_carbs_g),
                        'fat_g': float(meal_log.total_fat_g)
                    },
                    'detected_foods_count': len(meal_log.components)
                })
            
            return {
                'meals': meals,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + len(meals)) < total_count
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve meal history for user {user_id}: {str(e)}")
            return {
                'meals': [],
                'total_count': 0,
                'limit': limit,
                'offset': offset,
                'has_more': False,
                'error': str(e)
            }
    
    def get_daily_nutrition_summary(
        self,
        user_id: str,
        date: Optional[datetime.datetime] = None
    ) -> Dict[str, Any]:
        """
        Get nutrition summary for a specific day
        
        Args:
            user_id: User identifier (string or UUID)
            date: Date to get summary for (defaults to today)
            
        Returns:
            Daily nutrition summary with meal breakdown
        """
        try:
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
            
            # Default to today if no date provided
            if date is None:
                date = datetime.datetime.utcnow()
            
            # Get start and end of day
            start_of_day = datetime.datetime.combine(date.date(), datetime.time.min)
            end_of_day = datetime.datetime.combine(date.date(), datetime.time.max)
            
            # Query meals for the day
            meal_logs = self.db.query(MealLog).filter(
                MealLog.user_id == user_id,
                MealLog.logged_at >= start_of_day,
                MealLog.logged_at <= end_of_day
            ).order_by(MealLog.logged_at).all()
            
            # Calculate totals
            total_calories = 0.0
            total_protein = 0.0
            total_carbs = 0.0
            total_fat = 0.0
            
            meals_by_type = {
                'breakfast': [],
                'lunch': [],
                'dinner': [],
                'snack': []
            }
            
            for meal_log in meal_logs:
                total_calories += float(meal_log.total_calories)
                total_protein += float(meal_log.total_protein_g)
                total_carbs += float(meal_log.total_carbs_g)
                total_fat += float(meal_log.total_fat_g)
                
                meal_data = {
                    'id': str(meal_log.id),
                    'logged_at': meal_log.logged_at.isoformat(),
                    'calories': float(meal_log.total_calories),
                    'protein_g': float(meal_log.total_protein_g),
                    'carbs_g': float(meal_log.total_carbs_g),
                    'fat_g': float(meal_log.total_fat_g)
                }
                
                if meal_log.meal_type in meals_by_type:
                    meals_by_type[meal_log.meal_type].append(meal_data)
            
            return {
                'date': date.date().isoformat(),
                'total_nutrition': {
                    'calories': round(total_calories, 1),
                    'protein_g': round(total_protein, 1),
                    'carbs_g': round(total_carbs, 1),
                    'fat_g': round(total_fat, 1)
                },
                'meal_count': len(meal_logs),
                'meals_by_type': meals_by_type
            }
            
        except Exception as e:
            logger.error(f"Failed to get daily summary for user {user_id}: {str(e)}")
            return {
                'date': date.date().isoformat() if date else None,
                'total_nutrition': {
                    'calories': 0.0,
                    'protein_g': 0.0,
                    'carbs_g': 0.0,
                    'fat_g': 0.0
                },
                'meal_count': 0,
                'meals_by_type': {},
                'error': str(e)
            }
    
    def get_nutrition_trends(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get nutrition trends over a period of days
        
        Args:
            user_id: User identifier (string or UUID)
            days: Number of days to analyze (default 7)
            
        Returns:
            Nutrition trends with daily averages and patterns
        """
        try:
            # Convert string to UUID if needed
            if isinstance(user_id, str):
                user_id = uuid.UUID(user_id)
            
            # Calculate date range
            end_date = datetime.datetime.utcnow()
            start_date = end_date - datetime.timedelta(days=days)
            
            # Query meals in date range
            meal_logs = self.db.query(MealLog).filter(
                MealLog.user_id == user_id,
                MealLog.logged_at >= start_date,
                MealLog.logged_at <= end_date
            ).order_by(MealLog.logged_at).all()
            
            if not meal_logs:
                return {
                    'period_days': days,
                    'total_meals': 0,
                    'daily_averages': {},
                    'trends': {},
                    'daily_breakdown': []
                }
            
            # Group by date
            daily_data = {}
            for meal_log in meal_logs:
                date_key = meal_log.logged_at.date().isoformat()
                
                if date_key not in daily_data:
                    daily_data[date_key] = {
                        'calories': 0.0,
                        'protein_g': 0.0,
                        'carbs_g': 0.0,
                        'fat_g': 0.0,
                        'meal_count': 0
                    }
                
                daily_data[date_key]['calories'] += float(meal_log.total_calories)
                daily_data[date_key]['protein_g'] += float(meal_log.total_protein_g)
                daily_data[date_key]['carbs_g'] += float(meal_log.total_carbs_g)
                daily_data[date_key]['fat_g'] += float(meal_log.total_fat_g)
                daily_data[date_key]['meal_count'] += 1
            
            # Calculate averages
            num_days_with_data = len(daily_data)
            total_calories = sum(d['calories'] for d in daily_data.values())
            total_protein = sum(d['protein_g'] for d in daily_data.values())
            total_carbs = sum(d['carbs_g'] for d in daily_data.values())
            total_fat = sum(d['fat_g'] for d in daily_data.values())
            
            daily_averages = {
                'calories': round(total_calories / num_days_with_data, 1) if num_days_with_data > 0 else 0,
                'protein_g': round(total_protein / num_days_with_data, 1) if num_days_with_data > 0 else 0,
                'carbs_g': round(total_carbs / num_days_with_data, 1) if num_days_with_data > 0 else 0,
                'fat_g': round(total_fat / num_days_with_data, 1) if num_days_with_data > 0 else 0,
                'meals_per_day': round(len(meal_logs) / num_days_with_data, 1) if num_days_with_data > 0 else 0
            }
            
            # Calculate trends (simple comparison of first half vs second half)
            sorted_dates = sorted(daily_data.keys())
            mid_point = len(sorted_dates) // 2
            
            if mid_point > 0:
                first_half_avg = sum(daily_data[d]['calories'] for d in sorted_dates[:mid_point]) / mid_point
                second_half_avg = sum(daily_data[d]['calories'] for d in sorted_dates[mid_point:]) / (len(sorted_dates) - mid_point)
                
                calorie_trend = 'increasing' if second_half_avg > first_half_avg * 1.05 else \
                               'decreasing' if second_half_avg < first_half_avg * 0.95 else 'stable'
            else:
                calorie_trend = 'insufficient_data'
            
            return {
                'period_days': days,
                'total_meals': len(meal_logs),
                'days_with_data': num_days_with_data,
                'daily_averages': daily_averages,
                'trends': {
                    'calorie_trend': calorie_trend
                },
                'daily_breakdown': [
                    {
                        'date': date,
                        'calories': round(data['calories'], 1),
                        'protein_g': round(data['protein_g'], 1),
                        'carbs_g': round(data['carbs_g'], 1),
                        'fat_g': round(data['fat_g'], 1),
                        'meal_count': data['meal_count']
                    }
                    for date, data in sorted(daily_data.items())
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get nutrition trends for user {user_id}: {str(e)}")
            return {
                'period_days': days,
                'total_meals': 0,
                'daily_averages': {},
                'trends': {},
                'daily_breakdown': [],
                'error': str(e)
            }
