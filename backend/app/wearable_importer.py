import csv
import io
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def import_wearable_csv(file_content: str) -> list:
    """
    Ingests exported CSV files from Google Fit/Apple Health.
    Parses datetime, steps, calories, or weight logs.
    """
    results = []
    
    # Read CSV
    f = io.StringIO(file_content.strip())
    reader = csv.reader(f)
    
    headers = []
    try:
        headers = [h.strip().lower() for h in next(reader)]
    except StopIteration:
        return []

    # Map headers to standard fields
    for row in reader:
        if not row:
            continue
        
        row_dict = dict(zip(headers, row))
        try:
            # Look for date/time columns
            date_str = row_dict.get("date") or row_dict.get("time") or row_dict.get("start time") or row_dict.get("timestamp")
            if not date_str:
                continue
                
            parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
            
            # Map steps
            steps = 0
            if "steps" in row_dict:
                steps = int(float(row_dict["steps"]))
            elif "step count" in row_dict:
                steps = int(float(row_dict["step count"]))
                
            # Map calories
            calories = 0.0
            if "calories" in row_dict:
                calories = float(row_dict["calories"])
            elif "calories burned" in row_dict:
                calories = float(row_dict["calories burned"])
                
            # Map weight
            weight = 0.0
            if "weight" in row_dict:
                weight = float(row_dict["weight"])
            elif "weight (kg)" in row_dict:
                weight = float(row_dict["weight (kg)"])

            results.append({
                "timestamp": parsed_date.isoformat(),
                "steps": steps,
                "calories_burned": calories,
                "weight_kg": weight
            })
        except Exception as e:
            logger.warning(f"Failed to parse CSV row {row}: {e}")
            
    return results
