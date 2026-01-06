import sqlite3
from typing import Generator

from src.config import settings


def get_db() -> Generator:
    conn = sqlite3.connect(settings.database_url)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
