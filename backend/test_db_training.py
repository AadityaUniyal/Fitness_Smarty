
import requests
import time

BASE_URL = "http://localhost:8000"

def test_db_training_trigger():
    print("🧪 Testing DB-based Training Trigger...")
    try:
        # Simulate n8n request with query param
        response = requests.post(f"{BASE_URL}/api/training/recommendation/train?use_db=true&epochs=1")
        
        if response.status_code == 200:
            print(f"✅ Success: {response.json()}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("Ensure the backend server is running!")

if __name__ == "__main__":
    test_db_training_trigger()
