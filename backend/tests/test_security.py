import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.utils.security import create_token, hash_password, verify_token


def test_hash_password():
    """Test password hashing"""
    password = "testpassword123"
    hashed = hash_password(password)

    # Hash should be consistent
    assert hashed == hash_password(password)

    # Different passwords should have different hashes
    assert hashed != hash_password("differentpassword")

    # Hash should be a hex string
    assert isinstance(hashed, str)
    assert len(hashed) == 64  # SHA-256 produces 64-character hex string


def test_create_token():
    """Test JWT token creation"""
    user_id = 123
    token = create_token(user_id)

    assert isinstance(token, str)
    assert len(token) > 0

    # Token should be different each time (due to timestamp)
    import time

    time.sleep(1)
    token2 = create_token(user_id)
    assert token != token2


def test_verify_valid_token():
    """Test verifying a valid token"""
    user_id = 456
    token = create_token(user_id)

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    verified_user_id = verify_token(credentials)

    assert verified_user_id == user_id


def test_verify_invalid_token():
    """Test verifying an invalid token"""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_token")

    with pytest.raises(HTTPException) as exc_info:
        verify_token(credentials)

    assert exc_info.value.status_code == 401
    assert "Invalid or expired token" in exc_info.value.detail
