"""Pytest configuration and fixtures."""
import os
import sys

# Set test environment before any imports
os.environ["TESTING"] = "1"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "3306"
os.environ["DB_USER"] = "test"
os.environ["DB_PASSWORD"] = "test"
os.environ["DB_NAME"] = "test"

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.core.security import get_password_hash
from app.models.user import User

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def get_test_db():
    """Get test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_test_app():
    """Create a test FastAPI application without lifespan events."""
    from app.api import auth, users, pv, wind, battery, load, grid, strategy, alarm, analytics, config, logs
    from app.db.session import get_db
    
    test_app = FastAPI()
    
    # Include routers
    test_app.include_router(auth.router)
    test_app.include_router(users.router)
    test_app.include_router(pv.router)
    test_app.include_router(wind.router)
    test_app.include_router(battery.router)
    test_app.include_router(load.router)
    test_app.include_router(grid.router)
    test_app.include_router(strategy.router)
    test_app.include_router(alarm.router)
    test_app.include_router(analytics.router)
    test_app.include_router(config.router)
    test_app.include_router(logs.router)
    
    # Override database dependency
    test_app.dependency_overrides[get_db] = get_test_db
    
    return test_app


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    
    # Create test users
    admin_user = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    operator_user = User(
        username="operator",
        password_hash=get_password_hash("operator123"),
        role="operator",
        is_active=True
    )
    db.add(admin_user)
    db.add(operator_user)
    db.commit()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    test_app = create_test_app()
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    from app.db.session import get_db
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def admin_token(client):
    """Get admin user access token."""
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    return response.json()["data"]["access_token"]


@pytest.fixture
def operator_token(client):
    """Get operator user access token."""
    response = client.post(
        "/api/auth/login",
        data={"username": "operator", "password": "operator123"}
    )
    return response.json()["data"]["access_token"]


@pytest.fixture
def auth_headers(admin_token):
    """Get authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}
