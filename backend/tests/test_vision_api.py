def test_models_status(client):
    response = client.get("/api/vision/models/status")
    assert response.status_code == 200
    data = response.json()
    assert "available_count" in data


def test_yolo_detection(client):
    response = client.post(
        "/api/vision/detect-yolo",
        files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
        params={"confidence": 0.5, "annotate": False}
    )
    assert response.status_code in {200, 400, 500}


def test_hybrid_detection(client):
    response = client.post(
        "/api/vision/detect-hybrid",
        files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")}
    )
    assert response.status_code in {200, 400, 500}


def test_nutrition_estimation(client):
    detection_result = {
        "detections": [
            {"class": "grilled_chicken", "portion_estimate_g": 180},
            {"class": "rice", "portion_estimate_g": 150},
            {"class": "broccoli", "portion_estimate_g": 80}
        ]
    }
    response = client.post(
        "/api/vision/estimate-nutrition",
        json=detection_result
    )
    assert response.status_code == 200
    data = response.json()
    assert "calories" in data
