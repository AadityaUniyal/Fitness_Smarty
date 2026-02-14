"""
USDA FoodData Central API Integration Service

This service provides integration with the USDA FoodData Central API
for retrieving comprehensive nutritional information about food items.
"""

import os
import time
import requests
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from functools import wraps
from .error_handler import retry_on_failure, ExternalAPIError, error_handler

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API calls to prevent exceeding API limits"""
    
    def __init__(self, max_calls: int = 100, time_window: int = 3600):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed in time window
            time_window: Time window in seconds (default 1 hour)
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_make_call(self) -> bool:
        """Check if a call can be made within rate limits"""
        now = datetime.now()
        # Remove calls outside the time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < timedelta(seconds=self.time_window)]
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record a successful API call"""
        self.calls.append(datetime.now())
    
    def wait_time(self) -> float:
        """Calculate wait time in seconds before next call can be made"""
        if self.can_make_call():
            return 0.0
        
        now = datetime.now()
        oldest_call = min(self.calls)
        wait_seconds = (oldest_call + timedelta(seconds=self.time_window) - now).total_seconds()
        return max(0.0, wait_seconds)


def rate_limited(func):
    """Decorator to enforce rate limiting on API calls"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.rate_limiter.can_make_call():
            wait_time = self.rate_limiter.wait_time()
            raise Exception(f"Rate limit exceeded. Please wait {wait_time:.0f} seconds.")
        
        result = func(self, *args, **kwargs)
        self.rate_limiter.record_call()
        return result
    
    return wrapper


class USDAIntegrationService:
    """Service for integrating with USDA FoodData Central API"""
    
    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    
    def __init__(self, api_key: Optional[str] = None, max_calls: int = 100):
        """
        Initialize USDA Integration Service
        
        Args:
            api_key: USDA FoodData Central API key (defaults to env variable)
            max_calls: Maximum API calls per hour (default 100)
        """
        self.api_key = api_key or os.getenv("USDA_API_KEY")
        if not self.api_key:
            raise ValueError("USDA API key is required. Set USDA_API_KEY environment variable.")
        
        self.rate_limiter = RateLimiter(max_calls=max_calls)
        self.session = requests.Session()
    
    @retry_on_failure(max_attempts=3, delay=1.0, exceptions=(requests.exceptions.RequestException,))
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make HTTP request to USDA API with retry logic
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response as dictionary
            
        Raises:
            ExternalAPIError: If API request fails after retries
        """
        if params is None:
            params = {}
        
        params["api_key"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            logger.error(f"USDA API timeout: {str(e)}")
            raise ExternalAPIError(
                f"USDA API request timed out: {str(e)}",
                api_name="USDA FoodData Central"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"USDA API request failed: {str(e)}")
            raise ExternalAPIError(
                f"USDA API request failed: {str(e)}",
                api_name="USDA FoodData Central"
            )
    
    @rate_limited
    def search_foods(self, query: str, page_size: int = 25, page_number: int = 1,
                    data_type: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search for foods in USDA database
        
        Args:
            query: Search query string
            page_size: Number of results per page (max 200)
            page_number: Page number for pagination
            data_type: Filter by data types (e.g., ['Foundation', 'SR Legacy'])
            
        Returns:
            Search results with food items and pagination info
        """
        params = {
            "query": query,
            "pageSize": min(page_size, 200),
            "pageNumber": page_number
        }
        
        if data_type:
            params["dataType"] = data_type
        
        return self._make_request("foods/search", params)
    
    @rate_limited
    def get_food_details(self, fdc_id: int, format: str = "full") -> Dict[str, Any]:
        """
        Get detailed information about a specific food item
        
        Args:
            fdc_id: FoodData Central ID
            format: Response format ('abridged' or 'full')
            
        Returns:
            Detailed food information including nutrients
        """
        params = {"format": format}
        return self._make_request(f"food/{fdc_id}", params)
    
    @retry_on_failure(max_attempts=3, delay=1.0, exceptions=(requests.exceptions.RequestException,))
    def get_foods_list(self, fdc_ids: List[int], format: str = "full") -> List[Dict[str, Any]]:
        """
        Get details for multiple foods by their FDC IDs with retry logic
        
        Args:
            fdc_ids: List of FoodData Central IDs
            format: Response format ('abridged' or 'full')
            
        Returns:
            List of food details
            
        Raises:
            ExternalAPIError: If API request fails after retries
        """
        # USDA API supports POST for multiple foods
        url = f"{self.BASE_URL}/foods"
        params = {"api_key": self.api_key}
        
        try:
            response = self.session.post(
                url,
                params=params,
                json={"fdcIds": fdc_ids, "format": format},
                timeout=10
            )
            response.raise_for_status()
            self.rate_limiter.record_call()
            return response.json()
        except requests.exceptions.Timeout as e:
            logger.error(f"USDA API timeout: {str(e)}")
            raise ExternalAPIError(
                f"USDA API request timed out: {str(e)}",
                api_name="USDA FoodData Central"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"USDA API request failed: {str(e)}")
            raise ExternalAPIError(
                f"USDA API request failed: {str(e)}",
                api_name="USDA FoodData Central"
            )
    
    def extract_nutrition_data(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize nutrition data from USDA food response
        
        Args:
            food_data: Raw food data from USDA API
            
        Returns:
            Normalized nutrition data dictionary
        """
        nutrition = {
            "fdc_id": food_data.get("fdcId"),
            "name": food_data.get("description", ""),
            "brand": food_data.get("brandOwner"),
            "category": food_data.get("foodCategory"),
            "serving_size_g": None,
            "serving_description": None,
            "calories_per_100g": None,
            "protein_g": None,
            "carbs_g": None,
            "fat_g": None,
            "fiber_g": None,
            "sugar_g": None,
            "sodium_mg": None,
            "potassium_mg": None,
            "calcium_mg": None,
            "iron_mg": None,
            "vitamin_c_mg": None,
            "vitamin_d_ug": None
        }
        
        # Extract serving size information
        if "servingSize" in food_data:
            nutrition["serving_size_g"] = food_data["servingSize"]
        if "servingSizeUnit" in food_data:
            nutrition["serving_description"] = food_data["servingSizeUnit"]
        
        # Extract nutrient data
        nutrients = food_data.get("foodNutrients", [])
        nutrient_map = {
            "Energy": "calories_per_100g",
            "Protein": "protein_g",
            "Carbohydrate, by difference": "carbs_g",
            "Total lipid (fat)": "fat_g",
            "Fiber, total dietary": "fiber_g",
            "Sugars, total including NLEA": "sugar_g",
            "Sodium, Na": "sodium_mg",
            "Potassium, K": "potassium_mg",
            "Calcium, Ca": "calcium_mg",
            "Iron, Fe": "iron_mg",
            "Vitamin C, total ascorbic acid": "vitamin_c_mg",
            "Vitamin D (D2 + D3)": "vitamin_d_ug"
        }
        
        for nutrient in nutrients:
            nutrient_name = nutrient.get("nutrient", {}).get("name")
            if nutrient_name in nutrient_map:
                field_name = nutrient_map[nutrient_name]
                value = nutrient.get("amount")
                if value is not None:
                    nutrition[field_name] = float(value)
        
        return nutrition
    
    def search_and_extract(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for foods and extract nutrition data in one operation
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of normalized nutrition data dictionaries
        """
        search_results = self.search_foods(query, page_size=limit)
        foods = search_results.get("foods", [])
        
        extracted_data = []
        for food in foods:
            try:
                nutrition = self.extract_nutrition_data(food)
                extracted_data.append(nutrition)
            except Exception as e:
                # Log error but continue processing other foods
                print(f"Error extracting nutrition data for {food.get('description')}: {e}")
                continue
        
        return extracted_data
