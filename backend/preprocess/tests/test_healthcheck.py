from fastapi import status
from fastapi.testclient import TestClient
from preprocess.main import app

client = TestClient(app)

def test_healthcheck_ffmpeg_available():
    """
    /healthcheck must always return 200 with either 'healthy' or 'unhealthy'.
    """
    response = client.get("/healthcheck")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] in {"healthy", "unhealthy"}
