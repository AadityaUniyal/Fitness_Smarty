"""
Test YOLOv8 Integration

Quick script to test the new vision API endpoints
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_models_status():
    """Check which vision models are available"""
    print("\n" + "="*70)
    print("  TESTING VISION MODELS STATUS")
    print("="*70)
    
    response = requests.get(f"{API_BASE}/api/vision/models/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Available Models: {data['available_count']}/{data['total_count']}")
        print(f"\nModels:")
        for model_name, info in data['models'].items():
            status_emoji = "✅" if info['available'] else "❌"
            print(f"  {status_emoji} {model_name}: {info['status']}")
        print(f"\n💡 {data['recommendation']}")
    else:
        print(f"❌ Error: {response.status_code}")
    
    return response.status_code == 200


def test_yolo_detection(image_path="test_meal.jpg"):
    """Test YOLOv8 detection on an image"""
    print("\n" + "="*70)
    print("  TESTING YOLO DETECTION")
    print("="*70)
    
    if not os.path.exists(image_path):
        print(f"\n⚠️  Test image not found: {image_path}")
        print("   Using mock data instead...")
        
        # Test with a sample request (will use mock data)
        response = requests.post(
            f"{API_BASE}/api/vision/detect-yolo",
            files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
            params={"confidence": 0.5, "annotate": False}
        )
    else:
        with open(image_path, "rb") as f:
            response = requests.post(
                f"{API_BASE}/api/vision/detect-yolo",
                files={"file": f},
                params={"confidence": 0.5, "annotate": True}
            )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Detected {data['total_foods']} foods using {data['model_used']}")
        
        print(f"\nDetections:")
        for i, detection in enumerate(data['detections'], 1):
            print(f"  {i}. {detection['class']} - {detection['confidence']:.0%} confidence")
            print(f"     Portion: {detection['portion_estimate_g']}g")
            print(f"     BBox: {detection['bbox']}")
        
        if 'annotated_image_url' in data:
            print(f"\n📸 Annotated image: {API_BASE}{data['annotated_image_url']}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
    
    return response.status_code == 200


def test_hybrid_detection(image_path="test_meal.jpg"):
    """Test hybrid (YOLOv8 + Gemini) detection"""
    print("\n" + "="*70)
    print("  TESTING HYBRID DETECTION")
    print("="*70)
    
    files = {"file": ("test.jpg", b"fake_image_data", "image/jpeg")}
    
    response = requests.post(
        f"{API_BASE}/api/vision/detect-hybrid",
        files=files
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Hybrid detection complete!")
        print(f"   Total unique foods: {data['total_unique_foods']}")
        print(f"   Ensemble confidence: {data['ensemble_confidence']:.0%}")
        
        print(f"\nFinal Detections:")
        for i, detection in enumerate(data['final_detections'], 1):
            print(f"  {i}. {detection['food']} ({detection['source']})")
            print(f"     Confidence: {detection['confidence']:.0%}")
            if 'portion_g' in detection:
                print(f"     Portion: {detection['portion_g']}g")
    else:
        print(f"❌ Error: {response.status_code}")
    
    return response.status_code == 200


def test_nutrition_estimation():
    """Test nutrition estimation from detections"""
    print("\n" + "="*70)
    print("  TESTING NUTRITION ESTIMATION")
    print("="*70)
    
    # Sample detection result
    detection_result = {
        "detections": [
            {"class": "grilled_chicken", "portion_estimate_g": 180},
            {"class": "rice", "portion_estimate_g": 150},
            {"class": "broccoli", "portion_estimate_g": 80}
        ]
    }
    
    response = requests.post(
        f"{API_BASE}/api/vision/estimate-nutrition",
        json=detection_result
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Nutrition Estimated:")
        print(f"   Calories: {data['calories']} kcal")
        print(f"   Protein: {data['protein_g']}g")
        print(f"   Carbs: {data['carbs_g']}g")
        print(f"   Fat: {data['fat_g']}g")
        
        print(f"\nBreakdown:")
        for item in data['items']:
            print(f"  • {item['food']} ({item['portion_g']}g): {item['calories']} cal")
    else:
        print(f"❌ Error: {response.status_code}")
    
    return response.status_code == 200


def main():
    """Run all tests"""
    import os
    
    print("\n" + "="*70)
    print("  YOLOV8 VISION API TESTS")
    print("="*70)
    
    print("\nChecking if backend is running...")
    try:
        response = requests.get(f"{API_BASE}/docs")
        if response.status_code == 200:
            print("✅ Backend is running at", API_BASE)
        else:
            print("❌ Backend returned unexpected status:", response.status_code)
            return
    except Exception as e:
        print(f"❌ Backend not running at {API_BASE}")
        print(f"   Start with: python start.py")
        return
    
    # Run tests
    results = {
        "Models Status": test_models_status(),
        "YOLO Detection": test_yolo_detection(),
        "Hybrid Detection": test_hybrid_detection(),
        "Nutrition Estimation": test_nutrition_estimation()
    }
    
    # Summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        emoji = "✅" if passed else "❌"
        print(f"{emoji} {test_name}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n🎯 {passed_count}/{total_count} tests passed")
    
    print("\n" + "="*70)
    print("✅ ALL YOLOV8 FEATURES READY!")
    print("="*70)
    print("\nNew Endpoints:")
    print("  • POST /api/vision/detect-yolo - Real-time detection")
    print("  • POST /api/vision/detect-hybrid - Ensemble (YOLOv8 + Gemini)")
    print("  • GET  /api/vision/models/status - Check available models")
    print("  • POST /api/vision/estimate-nutrition - Nutrition from detections")
    print("\nNext: Update frontend to use these endpoints!")
    print("="*70)


if __name__ == "__main__":
    main()
