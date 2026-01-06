import sqlite3

import pytest
from fastapi import HTTPException

from src.config import settings
from src.utils.validators import get_portion_count


def test_get_portion_count_quran():
    """Test getting portion count for Quran"""
    conn = sqlite3.connect(settings.database_url, check_same_thread=False)

    assert get_portion_count("quran", "juz", None, conn) == 30
    assert get_portion_count("quran", "hezb", None, conn) == 60
    assert get_portion_count("quran", "quarter", None, conn) == 240
    assert get_portion_count("quran", "surah", None, conn) == 114
    assert get_portion_count("quran", "page", None, conn) == 604

    conn.close()


def test_get_portion_count_sahifa():
    """Test getting portion count for Sahifa Sajjadiya"""
    conn = sqlite3.connect(settings.database_url, check_same_thread=False)

    assert get_portion_count("sahifa_sajjadiya", "dua", None, conn) == 54

    conn.close()


def test_get_portion_count_nahj_balagha():
    """Test getting portion count for Nahjul Balagha"""
    conn = sqlite3.connect(settings.database_url, check_same_thread=False)

    assert get_portion_count("nahj_balagha", "sermon", None, conn) == 241
    assert get_portion_count("nahj_balagha", "letter", None, conn) == 79
    assert get_portion_count("nahj_balagha", "saying", None, conn) == 480

    conn.close()


def test_get_portion_count_custom():
    """Test getting portion count with custom total"""
    conn = sqlite3.connect(settings.database_url, check_same_thread=False)

    assert get_portion_count("custom", "any", 100, conn) == 100
    assert get_portion_count("unknown_type", "any", 50, conn) == 50

    conn.close()


def test_get_portion_count_custom_without_total():
    """Test that custom type without total raises error"""
    conn = sqlite3.connect(settings.database_url, check_same_thread=False)

    with pytest.raises(HTTPException) as exc_info:
        get_portion_count("custom", "any", None, conn)

    assert exc_info.value.status_code == 400
    assert "total_portions required" in str(exc_info.value.detail)

    conn.close()


def test_get_portion_count_unsupported_combination():
    """Test unsupported content type and portion type combination"""
    conn = sqlite3.connect(settings.database_url, check_same_thread=False)

    with pytest.raises(HTTPException) as exc_info:
        get_portion_count("quran", "invalid_type", None, conn)

    assert exc_info.value.status_code == 400

    conn.close()
