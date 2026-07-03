import urllib.request
import json
import logging

logger = logging.getLogger(__name__)

def lookup_barcode(barcode: str) -> dict:
    """
    Look up barcode nutrition metrics from the free Open Food Facts API.
    Returns standard mock data fallback if API is unreachable.
    """
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    
    try:
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "SmartyAI - FitnessApp - Version 4.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            
            if data.get("status") == 1:
                product = data.get("product", {})
                nutriments = product.get("nutriments", {})
                
                return {
                    "found": True,
                    "name": product.get("product_name", "Unknown Item"),
                    "calories": float(nutriments.get("energy-kcal_100g", 0)),
                    "protein": float(nutriments.get("proteins_100g", 0)),
                    "carbs": float(nutriments.get("carbohydrates_100g", 0)),
                    "fats": float(nutriments.get("fat_100g", 0)),
                    "brand": product.get("brands", "Generic")
                }
    except Exception as e:
        logger.warning(f"Open Food Facts lookup failed: {e}. Falling back to default library.")

    # Safe local mock fallback for testing
    mock_barcodes = {
        "012000000133": {"name": "Pepsi Zero Sugar", "calories": 0, "protein": 0, "carbs": 0, "fats": 0, "brand": "Pepsi"},
        "049000028904": {"name": "Coca-Cola Zero Sugar", "calories": 0, "protein": 0, "carbs": 0, "fats": 0, "brand": "Coca-Cola"},
    }
    
    if barcode in mock_barcodes:
        return {**mock_barcodes[barcode], "found": True}

    return {
        "found": False,
        "name": f"Unknown Product ({barcode})",
        "calories": 100,
        "protein": 5.0,
        "carbs": 15.0,
        "fats": 2.0,
        "brand": "Unknown"
    }
