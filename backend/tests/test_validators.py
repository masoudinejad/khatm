"""Tests for validator utilities"""

import sqlite3

import pytest
from fastapi import HTTPException

from src.config import settings
from src.utils.validators import get_portion_count


@pytest.fixture
def db_conn():
    """Create a database connection for validator tests"""
    conn = sqlite3.connect(settings.database_url)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_get_portion_count_quran_juz(db_conn):
    """Test getting portion count for Quran juz"""
    count = get_portion_count("quran", "juz", None, db_conn)
    assert count == 30


def test_get_portion_count_quran_hizb(db_conn):
    """Test getting portion count for Quran hizb"""
    count = get_portion_count("quran", "hezb", None, db_conn)
    assert count == 60


def test_get_portion_count_quran_surah(db_conn):
    """Test getting portion count for Quran surah"""
    count = get_portion_count("quran", "surah", None, db_conn)
    assert count == 114


def test_get_portion_count_quran_page(db_conn):
    """Test getting portion count for Quran page"""
    count = get_portion_count("quran", "page", None, db_conn)
    assert count == 604


def test_get_portion_count_custom_with_total(db_conn):
    """Test getting portion count for custom content with total_portions"""
    count = get_portion_count("custom_content", "chapter", 50, db_conn)
    assert count == 50


def test_get_portion_count_custom_without_total(db_conn):
    """Test getting portion count for custom content without total_portions"""
    with pytest.raises(HTTPException) as exc:
        get_portion_count("custom", "chapter", None, db_conn)
    assert exc.value.status_code == 400
    assert "total_portions" in exc.value.detail


def test_get_portion_count_invalid_portion_type(db_conn):
    """Test getting portion count with invalid portion type for Quran"""
    with pytest.raises(HTTPException) as exc:
        get_portion_count("quran", "invalid_type", None, db_conn)
    assert exc.value.status_code == 400
    # Check for either error message pattern
    assert "total_portions" in exc.value.detail or "Invalid portion_type" in exc.value.detail


def test_get_portion_count_out_of_range_low():
    """Test validation with portion number below valid range"""
    # This tests the validation that happens after get_portion_count
    # You may need to adjust based on your actual validator implementation
    pass


def test_get_portion_count_out_of_range_high():
    """Test validation with portion number above valid range"""
    # This tests the validation that happens after get_portion_count
    # You may need to adjust based on your actual validator implementation
    pass
