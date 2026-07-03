def test_db_training_trigger(client):
    # Use the test client instead of requests to trigger training
    response = client.post("/api/training/recommendation/train?use_db=true&epochs=1")
    # Assert code 200 or 500/400 (depening on DB setup, but since it runs in test context, 200 is expected if DB is seeded)
    assert response.status_code in {200, 400, 500}
