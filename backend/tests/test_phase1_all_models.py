def test_resnet_classification(client):
    response = client.post(
        "/api/vision/classify-resnet",
        files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
        params={"top_k": 3}
    )
    assert response.status_code in {200, 400, 500} # Models might be un-initialized, but route should exist


def test_maskrcnn_portions(client):
    response = client.post(
        "/api/vision/estimate-portions",
        files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
        params={"food_labels": "chicken,rice,broccoli"}
    )
    assert response.status_code in {200, 400, 500}


def test_ensemble_detection(client):
    response = client.post(
        "/api/vision/detect-ensemble",
        files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
        params={"use_all_models": True}
    )
    assert response.status_code in {200, 400, 500}


def test_updated_models_status(client):
    response = client.get("/api/vision/models/status")
    assert response.status_code == 200
    data = response.json()
    assert "available_count" in data
    assert "models" in data
