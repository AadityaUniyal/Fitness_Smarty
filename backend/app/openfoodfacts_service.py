"""
Open Food Facts API Service
===========================
Fetches product information and nutritional data from the free Open Food Facts database.
"""
import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class OpenFoodFactsService:
    BASE_URL = "https://world.openfoodfacts.org/cgi/search.pl"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "LyraFit - WebApp - Version 2.0.0 - www.lyrafit.com"
        })

    def search_products(self, query: str, page_size: int = 15) -> List[Dict[str, Any]]:
        """
        Search Open Food Facts database for a query term
        """
        params = {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": page_size
        }
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=8)
            if response.status_code == 200:
                data = response.json()
                products = data.get("products", [])
                
                results = []
                for p in products:
                    name = p.get("product_name") or p.get("product_name_en")
                    if not name:
                        continue
                    
                    nutriments = p.get("nutriments", {})
                    # Open Food Facts values are typically per 100g
                    calories = nutriments.get("energy-kcal_100g") or nutriments.get("energy-kcal") or 0.0
                    protein = nutriments.get("proteins_100g") or nutriments.get("proteins") or 0.0
                    carbs = nutriments.get("carbohydrates_100g") or nutriments.get("carbohydrates") or 0.0
                    fats = nutriments.get("fat_100g") or nutriments.get("fat") or 0.0
                    
                    results.append({
                        "name": name,
                        "brand": p.get("brands", "Generic"),
                        "calories": float(calories),
                        "protein": float(protein),
                        "carbs": float(carbs),
                        "fats": float(fats)
                    })
                return results
            else:
                logger.warning(f"Open Food Facts API returned status code {response.status_code}")
        except Exception as e:
            logger.error(f"Open Food Facts search error: {e}")
        return []
