import sqlite3

from src.config import settings


def init_database():
    conn = sqlite3.connect(settings.database_url)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        preferred_language TEXT DEFAULT 'en',
        is_admin BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Content types table - allows dynamic addition of new types
    c.execute("""CREATE TABLE IF NOT EXISTS content_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        description TEXT,
        default_portion_types TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )""")

    # Seed default content types
    default_types = [
        (
            "quran",
            "Holy Quran",
            "The Holy Quran",
            '{"juz":30,"hezb":60,"quarter":240,"surah":114,"page":604}',
        ),
        ("sahifa_sajjadiya", "Al-Sahifa al-Sajjadiyya", "Psalms of Islam", '{"dua":54}'),
        ("mafatih", "Mafatih al-Jinan", "Keys to the Gardens", "{}"),
        (
            "nahj_balagha",
            "Nahjul Balagha",
            "Peak of Eloquence",
            '{"sermon":241,"letter":79,"saying":480}',
        ),
        ("al_kafi", "Al-Kafi", "The Sufficient", '{"volume":8}'),
        (
            "man_la_yahduruhu",
            "Man La Yahduruhu al-Faqih",
            "For One Not in the Presence of a Jurist",
            '{"volume":4}',
        ),
        ("ziyarat_ashura", "Ziyarat Ashura", "Ziyarat of Imam Hussain (AS)", '{"day":40}'),
        ("custom", "Custom", "Custom content type", "{}"),
    ]

    for name, display, desc, portions in default_types:
        c.execute(
            """INSERT OR IGNORE INTO content_types 
               (name, display_name, description, default_portion_types) 
               VALUES (?, ?, ?, ?)""",
            (name, display, desc, portions),
        )

    c.execute("""CREATE TABLE IF NOT EXISTS recitations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        creator_id INTEGER NOT NULL,
        content_type_id INTEGER NOT NULL,
        portion_type TEXT NOT NULL,
        total_portions INTEGER NOT NULL,
        status TEXT DEFAULT 'active',
        language TEXT DEFAULT 'en',
        deadline TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (creator_id) REFERENCES users(id),
        FOREIGN KEY (content_type_id) REFERENCES content_types(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recitation_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recitation_id) REFERENCES recitations(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(recitation_id, user_id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS portions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recitation_id INTEGER NOT NULL,
        user_id INTEGER,
        portion_number INTEGER NOT NULL,
        progress_percentage INTEGER DEFAULT 0,
        is_completed BOOLEAN DEFAULT 0,
        assigned_at TIMESTAMP,
        completed_at TIMESTAMP,
        last_progress_update TIMESTAMP,
        FOREIGN KEY (recitation_id) REFERENCES recitations(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(recitation_id, portion_number)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS progress_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        portion_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        progress_percentage INTEGER NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (portion_id) REFERENCES portions(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")

    conn.commit()
    conn.close()
