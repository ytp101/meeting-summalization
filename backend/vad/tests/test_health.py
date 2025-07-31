def test_healthcheck(client):
    res = client.get("/healthcheck")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["status"] in ["healthy", "unhealthy"]
    assert "model_loaded" in json_data
