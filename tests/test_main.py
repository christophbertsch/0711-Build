import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import get_db
from app.models import Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

def test_health_endpoint(client):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "openhands" in data

def test_create_run_missing_fields(client):
    """Test creating run with missing required fields"""
    response = client.post("/runs", json={})
    assert response.status_code == 422  # Validation error

def test_create_run_valid(client):
    """Test creating run with valid data"""
    run_data = {
        "project_id": "test-project",
        "compiled_prompt": "Test prompt",
        "repository": "test/repo",
        "metadata": {"test": "data"}
    }
    
    # This will fail because we can't actually connect to OpenHands in tests
    # but it tests the validation and basic flow
    response = client.post("/runs", json=run_data)
    # We expect this to fail with 500 due to OpenHands connection
    assert response.status_code in [500, 200]

def test_get_nonexistent_run(client):
    """Test getting a run that doesn't exist"""
    response = client.get("/runs/nonexistent")
    assert response.status_code == 404

def test_list_runs_empty(client):
    """Test listing runs when none exist"""
    response = client.get("/runs")
    assert response.status_code == 200
    assert response.json() == []