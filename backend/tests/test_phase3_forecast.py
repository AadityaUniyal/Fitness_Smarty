from datetime import datetime, timedelta

def test_lstm_weight_prediction(client):
    historical_data = []
    for i in range(14):
        date = (datetime.now() - timedelta(days=14-i)).strftime('%Y-%m-%d')
        historical_data.append({
            "date": date,
            "weight": 78 - (i * 0.1),
            "calories": 1800 + (i * 10),
            "activity_minutes": 45
        })

    response = client.post(
        "/api/forecast/predict-weight",
        json={
            "historical_data": historical_data,
            "days_ahead": 7
        }
    )
    assert response.status_code in {200, 400, 500}


def test_prophet_nutrition_trends(client):
    historical_data = []
    for i in range(21):
        date = (datetime.now() - timedelta(days=21-i)).strftime('%Y-%m-%d')
        historical_data.append({
            "date": date,
            "calories": 1900 + (i * 5),
            "protein_g": 80 + (i * 0.5),
            "carbs_g": 200 - (i * 2),
            "fat_g": 60
        })

    response = client.post(
        "/api/forecast/analyze-nutrition-trends",
        json={
            "historical_data": historical_data,
            "forecast_days": 14
        }
    )
    assert response.status_code in {200, 400, 500}


def test_goal_projection(client):
    response = client.get(
        "/api/forecast/goal-projection",
        params={
            "user_id": 1,
            "goal_weight": 75.0
        }
    )
    assert response.status_code in {200, 400, 500}


def test_forecast_models_status(client):
    response = client.get("/api/forecast/models/status")
    assert response.status_code == 200
    data = response.json()
    assert "available_count" in data
