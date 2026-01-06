import os
import sqlite3

import pytest
from fastapi.testclient import TestClient

from src.config import settings
from src.database.init_db import init_database
from src.main import app

# Use a test database
TEST_DB = "test_recitations.db"


@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Setup test database before each test"""
    # Set test database
    original_db = settings.database_url
    settings.database_url = TEST_DB

    # Initialize database
    init_database()

    yield

    # Cleanup - remove test database after test
    settings.database_url = original_db
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.fixture(scope="function")
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(scope="function")
def test_user(client):
    """Create a test user and return token"""
    response = client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
            "preferred_language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    return {"token": data["token"], "user_id": data["user_id"], "email": "test@example.com"}


@pytest.fixture(scope="function")
def admin_user(client):
    """Create an admin user and return token"""
    # Register regular user
    response = client.post(
        "/auth/register",
        json={
            "name": "Admin User",
            "email": "admin@example.com",
            "password": "adminpass123",
            "preferred_language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    user_id = data["user_id"]

    # Make user admin in database
    conn = sqlite3.connect(TEST_DB, check_same_thread=False)
    conn.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return {"token": data["token"], "user_id": user_id, "email": "admin@example.com"}


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Return authorization headers"""
    return {"Authorization": f"Bearer {test_user['token']}"}


@pytest.fixture(scope="function")
def admin_headers(admin_user):
    """Return admin authorization headers"""
    return {"Authorization": f"Bearer {admin_user['token']}"}
