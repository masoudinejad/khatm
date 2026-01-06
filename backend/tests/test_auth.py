def test_register_with_email(client):
    """Test user registration with email"""
    response = client.post(
        "/auth/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "password123",
            "preferred_language": "en",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user_id" in data
    assert data["message"] == "User registered successfully"


def test_register_with_phone(client):
    """Test user registration with phone number"""
    response = client.post(
        "/auth/register",
        json={
            "name": "Ali Hassan",
            "phone": "+989123456789",
            "password": "password123",
            "preferred_language": "fa",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user_id" in data


def test_register_without_email_or_phone(client):
    """Test registration fails without email or phone"""
    response = client.post(
        "/auth/register", json={"name": "Invalid User", "password": "password123"}
    )

    assert response.status_code == 400
    assert "Either email or phone number is required" in response.json()["detail"]


def test_register_invalid_phone(client):
    """Test registration with invalid phone format"""
    response = client.post(
        "/auth/register",
        json={
            "name": "Invalid Phone",
            "phone": "123456",  # Missing country code
            "password": "password123",
        },
    )

    assert response.status_code == 422  # Validation error


def test_register_duplicate_email(client):
    """Test registration with duplicate email"""
    # First registration
    client.post(
        "/auth/register",
        json={"name": "First User", "email": "duplicate@example.com", "password": "password123"},
    )

    # Second registration with same email
    response = client.post(
        "/auth/register",
        json={"name": "Second User", "email": "duplicate@example.com", "password": "password456"},
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_with_email(client, test_user):
    """Test login with email"""
    response = client.post(
        "/auth/login", json={"email": test_user["email"], "password": "testpassword123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user_id"] == test_user["user_id"]


def test_login_with_phone(client):
    """Test login with phone number"""
    # Register
    phone = "+989123456789"
    client.post(
        "/auth/register", json={"name": "Phone User", "phone": phone, "password": "password123"}
    )

    # Login
    response = client.post("/auth/login", json={"phone": phone, "password": "password123"})

    assert response.status_code == 200
    data = response.json()
    assert "token" in data


def test_login_invalid_password(client, test_user):
    """Test login with wrong password"""
    response = client.post(
        "/auth/login", json={"email": test_user["email"], "password": "wrongpassword"}
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_nonexistent_user(client):
    """Test login with non-existent email"""
    response = client.post(
        "/auth/login", json={"email": "nonexistent@example.com", "password": "password123"}
    )

    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]
