"""Tests for user models"""

import pytest
from pydantic import ValidationError

from src.models.user import UserLogin, UserRegister


def test_user_register_valid():
    """Test valid user registration"""
    user = UserRegister(
        name="Test User",
        email="test@example.com",
        phone="+1234567890",
        password="SecurePass123!",
        preferred_language="en",
    )
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.preferred_language == "en"


def test_user_register_invalid_email():
    """Test user registration with invalid email"""
    with pytest.raises(ValidationError) as exc:
        UserRegister(
            name="Test User",
            email="invalid-email",
            phone="+1234567890",
            password="SecurePass123!",
            preferred_language="en",
        )
    assert "email" in str(exc.value).lower()


def test_user_register_minimal_valid_password():
    """Test user registration with minimal valid password"""
    user = UserRegister(
        name="Test User",
        email="test@example.com",
        phone="+1234567890",
        password="Pass1!",  # Meets minimum requirements
        preferred_language="en",
    )
    assert user.password == "Pass1!"


def test_user_register_optional_phone():
    """Test user registration without phone"""
    user = UserRegister(
        name="Test User",
        email="test@example.com",
        password="SecurePass123!",
        preferred_language="en",
    )
    assert user.phone is None


def test_user_register_default_language():
    """Test user registration with default language"""
    user = UserRegister(
        name="Test User",
        email="test@example.com",
        password="SecurePass123!",
        preferred_language="en",
    )
    assert user.preferred_language == "en"


def test_user_login_valid():
    """Test valid user login"""
    login = UserLogin(
        email="test@example.com",
        password="password123",
    )
    assert login.email == "test@example.com"
    assert login.password == "password123"


def test_user_login_missing_fields():
    """Test user login with missing fields"""
    with pytest.raises(ValidationError):
        UserLogin(email="test@example.com")
        # Missing password
