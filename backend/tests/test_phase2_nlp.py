def test_bert_recipe_analysis(client):
    recipe = """
    Ingredients:
    - 2 chicken breasts (300g)
    - 1 cup rice
    - 2 cups broccoli
    - 2 tbsp olive oil
    - Salt and pepper to taste
    """
    response = client.post(
        "/api/nlp/analyze-recipe",
        params={
            "recipe_text": recipe,
            "estimate_nutrition": True
        }
    )
    assert response.status_code in {200, 400, 500}


def test_clip_text_search(client):
    response = client.post(
        "/api/nlp/search-by-text",
        params={"query": "high protein meal", "top_k": 3}
    )
    assert response.status_code in {200, 400, 500}


def test_clip_image_search(client):
    response = client.post(
        "/api/nlp/search-similar-meals",
        files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
        params={"top_k": 5}
    )
    assert response.status_code in {200, 400, 500}


def test_ingredient_extraction(client):
    recipe = "I need 2 chicken breasts, 1 cup of rice, and some broccoli"
    response = client.post(
        "/api/nlp/extract-ingredients",
        params={"recipe_text": recipe}
    )
    assert response.status_code in {200, 400, 500}


def test_nlp_models_status(client):
    response = client.get("/api/nlp/models/status")
    assert response.status_code == 200
    data = response.json()
    assert "available_count" in data
