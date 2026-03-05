import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models.database import Base, get_session_local
from app.core.config import settings

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_session_local] = override_get_db

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_attack_scenarios():
    """Test listing attack scenarios"""
    response = client.get("/api/v1/attack-scenarios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_security_test():
    """Test creating a security test"""
    test_data = {
        "test_name": "Test Security Assessment",
        "attack_scenario_id": 1,
        "baseline_prompts": ["Test prompt 1", "Test prompt 2"],
        "techniques": ["poetry", "narrative"],
        "target_models": [
            {"adapter": "openai", "model": "gpt-4"}
        ]
    }
    
    response = client.post("/api/v1/security-tests/run", json=test_data)
    assert response.status_code == 200
    data = response.json()
    assert "test_id" in data
    assert data["status"] == "queued"


def test_list_security_tests():
    """Test listing security tests"""
    response = client.get("/api/v1/security-tests")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
