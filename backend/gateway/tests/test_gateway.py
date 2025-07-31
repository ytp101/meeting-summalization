"""
Test suite for Meeting Summarization Gateway Service.

This module includes unit tests for the API Gateway's core endpoints:
- Root health check
- Downstream services healthcheck (with HTTPX client monkeypatched)
- File upload validation

Uses pytest and FastAPI TestClient.
"""
import pytest
import httpx
from fastapi.testclient import TestClient

from gateway.main import app

# Initialize TestClient for the FastAPI app
client = TestClient(app)

# Dummy response and client for healthcheck endpoint
class DummyResponse:
    def __init__(self, status_code=200, text="OK"):
        self.status_code = status_code
        self.text = text

class DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass
    async def get(self, url, timeout=None):
        return DummyResponse()

@pytest.fixture(autouse=True)
def patch_async_client(monkeypatch):
    """Monkeypatch httpx.AsyncClient to use DummyAsyncClient"""
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "gateway running"}


def test_healthcheck_all_services_up():
    response = client.get("/healthcheck")
    assert response.status_code == 200
    data = response.json()
    # Expect a list of service status objects
    assert isinstance(data, list)
    expected_services = {"preprocess", "diarization", "whisper", "summarization"}
    returned_services = {item["service"] for item in data}
    assert returned_services == expected_services
    # All services should report 'up' with empty message
    for item in data:
        assert item["status"] == "up"
        assert item["message"] == ""


def test_upload_unsupported_extension():
    """
    Ensure that uploading an unsupported file type returns a 400 error.
    """
    files = {"file": ("test.txt", b"dummy content")}  # .txt is not allowed
    response = client.post("/uploadfile/", files=files)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

# PYTHONPATH=. pytest gateway/tests 