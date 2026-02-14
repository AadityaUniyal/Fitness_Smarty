"""
Test Phase 2: NLP & Language Models

Tests for BERT recipe analysis and CLIP semantic search
"""

import requests

API_BASE = "http://localhost:8000"

def test_bert_recipe_analysis():
    """Test BERT recipe analyzer"""
    print("\n" + "="*70)
    print("  TESTING BERT RECIPE ANALYSIS")
    print("="*70)
    
    recipe = """
    Ingredients:
    - 2 chicken breasts (300g)
    - 1 cup rice
    - 2 cups broccoli
    - 2 tbsp olive oil
    - Salt and pepper to taste
    
    Instructions:
    1. Grill chicken for 20 minutes
    2. Cook rice according to package
    3. Steam broccoli for 5 minutes
    4. Serve together
    """
    
    response = requests.post(
        f"{API_BASE}/api/nlp/analyze-recipe",
        params={
            "recipe_text": recipe,
            "estimate_nutrition": True
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ BERT Recipe Analysis:")
        print(f"   Method: {data['method']}")
        print(f"   Confidence: {data['confidence']}")
        print(f"   Entities found: {data.get('entities_found', 'N/A')}")
        
        print(f"\n   Extracted ingredients:")
        for ing in data['ingredients'][:5]:
            qty = data['quantities'].get(ing, 'N/A')
            print(f"     • {ing}: {qty}")
        
        if 'nutrition_estimate' in data:
            nutr = data['nutrition_estimate']
            print(f"\n   Nutrition estimate:")
            print(f"     Calories: {nutr['calories']}")
            print(f"     Protein: {nutr['protein_g']}g")
            print(f"     Carbs: {nutr['carbs_g']}g")
            print(f"     Fat: {nutr['fat_g']}g")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    return response.status_code == 200


def test_clip_text_search():
    """Test CLIP semantic search"""
    print("\n" + "="*70)
    print("  TESTING CLIP SEMANTIC SEARCH")
    print("="*70)
    
    queries = [
        "high protein low carb meal",
        "vegetarian breakfast",
        "healthy dinner under 500 calories"
    ]
    
    for query in queries:
        response = requests.post(
            f"{API_BASE}/api/nlp/search-by-text",
            params={"query": query, "top_k": 3}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Query: '{query}'")
            print(f"   Found: {data['total_found']} meals")
            
            for i, result in enumerate(data['results'][:3], 1):
                details = result.get('meal_details', {})
                print(f"     {i}. {details.get('name', 'Unknown')} "
                      f"(similarity: {result['similarity']:.0%})")
        else:
            print(f"❌ Failed for '{query}': {response.status_code}")
    
    return response.status_code == 200


def test_clip_image_search():
    """Test CLIP visual similarity"""
    print("\n" + "="*70)
    print("  TESTING CLIP IMAGE SIMILARITY")
    print("="*70)
    
    response = requests.post(
        f"{API_BASE}/api/nlp/search-similar-meals",
        files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
        params={"top_k": 5}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Image Similarity Search:")
        print(f"   Query image: {data['query_image']}")
        print(f"   Found: {data['total_found']} similar meals")
        
        print(f"\n   Most similar meals:")
        for i, result in enumerate(data['results'], 1):
            details = result.get('meal_details', {})
            print(f"     {i}. {details.get('name', 'Unknown')} "
                  f"(similarity: {result['similarity']:.0%})")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    return response.status_code == 200


def test_ingredient_extraction():
    """Test quick ingredient extraction"""
    print("\n" + "="*70)
    print("  TESTING INGREDIENT EXTRACTION")
    print("="*70)
    
    recipe = "I need 2 chicken breasts, 1 cup of rice, and some broccoli"
    
    response = requests.post(
        f"{API_BASE}/api/nlp/extract-ingredients",
        params={"recipe_text": recipe}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Ingredient Extraction:")
        print(f"   Confidence: {data['confidence']}")
        
        print(f"\n   Ingredients:")
        for ing in data['ingredients']:
            qty = data['quantities'].get(ing, 'N/A')
            print(f"     • {ing}: {qty}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    return response.status_code == 200


def test_nlp_models_status():
    """Test NLP models status"""
    print("\n" + "="*70)
    print("  TESTING NLP MODELS STATUS")
    print("="*70)
    
    response = requests.get(f"{API_BASE}/api/nlp/models/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ NLP Models: {data['available_count']}/{data['total_count']} available")
        print(f"   Phase: {data['phase']}")
        
        print(f"\n   Models:")
        for model_name, info in data['models'].items():
            status_emoji = "✅" if info['available'] else "❌"
            print(f"     {status_emoji} {model_name}: {info['status']}")
            print(f"        {info['description']}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    return response.status_code == 200


def main():
    """Run all Phase 2 tests"""
    print("\n" + "="*70)
    print("  PHASE 2 TESTING")
    print("  (BERT + CLIP)")
    print("="*70)
    
    # Check backend
    try:
        response = requests.get(f"{API_BASE}/docs")
        if response.status_code == 200:
            print("\n✅ Backend running\n")
        else:
            print(f"❌ Backend issue: {response.status_code}")
            return
    except:
        print(f"❌ Backend not running at {API_BASE}")
        return
    
    # Run tests
    results = {
        "BERT Recipe Analysis": test_bert_recipe_analysis(),
        "CLIP Text Search": test_clip_text_search(),
        "CLIP Image Similarity": test_clip_image_search(),
        "Ingredient Extraction": test_ingredient_extraction(),
        "NLP Models Status": test_nlp_models_status()
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
    print("✅ PHASE 2 NLP TESTING COMPLETE!")
    print("="*70)
    print("\n🔥 NLP Features:")
    print("  • BERT recipe understanding")
    print("  • Ingredient extraction")
    print("  • Nutrition estimation from text")
    print("  • CLIP semantic search (text)")
    print("  • CLIP visual similarity (image)")
    print("\n📊 Total Endpoints: 5")
    print("  • POST /api/nlp/analyze-recipe")
    print("  • POST /api/nlp/search-by-text")
    print("  • POST /api/nlp/search-similar-meals")
    print("  • POST /api/nlp/extract-ingredients")
    print("  • GET  /api/nlp/models/status")
    print("="*70)


if __name__ == "__main__":
    main()
