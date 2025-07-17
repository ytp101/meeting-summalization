def test_root_status(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"status": "running"}
