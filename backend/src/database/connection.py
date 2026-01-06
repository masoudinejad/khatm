import sqlite3
from typing import Generator

from src.config import settings


def get_db() -> Generator:
    # Enable check_same_thread=False for testing compatibility
    conn = sqlite3.connect(settings.database_url, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
