from fastapi import status
from fastapi.testclient import TestClient
from preprocess.main import app

client = TestClient(app)

def test_root_service_live_check():
    """
    The root endpoint should return 200 OK and the expected JSON.
    """
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "preprocess running"}
