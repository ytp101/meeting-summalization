# vad/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from vad.main import app  # or wherever your FastAPI app is defined

@pytest.fixture
def client():
    return TestClient(app)
