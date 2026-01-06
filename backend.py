"""
Simple and lightweight Quran Khatm API Backend
FastAPI + SQLite for maximum simplicity
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime, timedelta
import sqlite3
import hashlib
import jwt
import os
import re

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
DATABASE = "khatm.db"

app = FastAPI(title="Quran Khatm API", version="1.0.0")
security = HTTPBearer()

# ============= Models =============

class UserRegister(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str
    preferred_language: str = "en"  # en, ar, fa, ur, etc.
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        # Remove all spaces, dashes, and parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        # Check if it matches international format: + followed by 7-15 digits
        if not re.match(r'^\+[1-9]\d{6,14}

class KhatmCreate(BaseModel):
    title: str
    description: Optional[str] = None
    content_type: str = "quran"  # quran, hadith, dua, custom
    portion_type: str = "juz"  # juz, hezb, quarter, chapter, page, custom
    total_portions: Optional[int] = None  # For custom content types
    deadline: Optional[str] = None  # ISO format date
    language: str = "en"

class PortionAssign(BaseModel):
    portion_number: int

# ============= Database Setup =============

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        preferred_language TEXT DEFAULT 'en',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Khatms table
    c.execute('''CREATE TABLE IF NOT EXISTS khatms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        creator_id INTEGER NOT NULL,
        content_type TEXT DEFAULT 'quran',
        portion_type TEXT NOT NULL,
        total_portions INTEGER NOT NULL,
        status TEXT DEFAULT 'active',
        language TEXT DEFAULT 'en',
        deadline TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (creator_id) REFERENCES users(id)
    )''')
    
    # Participants table
    c.execute('''CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        khatm_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (khatm_id) REFERENCES khatms(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(khatm_id, user_id)
    )''')
    
    # Portions table
    c.execute('''CREATE TABLE IF NOT EXISTS portions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        khatm_id INTEGER NOT NULL,
        user_id INTEGER,
        portion_number INTEGER NOT NULL,
        is_completed BOOLEAN DEFAULT 0,
        assigned_at TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (khatm_id) REFERENCES khatms(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(khatm_id, portion_number)
    )''')
    
    conn.commit()
    conn.close()

# ============= Helper Functions =============

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_portion_count(content_type: str, portion_type: str, custom_total: Optional[int] = None) -> int:
    """Returns total number of portions based on content and portion type"""
    
    # For custom content, use the provided total
    if content_type == "custom" or custom_total is not None:
        if custom_total is None:
            raise HTTPException(status_code=400, detail="total_portions required for custom content")
        return custom_total
    
    # Quran portions
    if content_type == "quran":
        quran_counts = {"juz": 30, "hezb": 60, "quarter": 240}
        if portion_type in quran_counts:
            return quran_counts[portion_type]
    
    # Sahih Bukhari (most common hadith book)
    if content_type == "hadith_bukhari":
        if portion_type == "book": return 97  # 97 books in Bukhari
        if portion_type == "chapter": return 3450  # approximate chapters
    
    # Sahih Muslim
    if content_type == "hadith_muslim":
        if portion_type == "book": return 56  # 56 books in Muslim
    
    # Riyadh as-Salihin
    if content_type == "hadith_riyadh":
        if portion_type == "chapter": return 372  # 372 chapters
    
    # If no match found, require custom total
    if custom_total is None:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported combination: {content_type}/{portion_type}. Please provide total_portions."
        )
    
    return custom_total

# ============= API Endpoints =============

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/")
async def root():
    return {"message": "Quran Khatm API", "version": "1.0.0"}

# Authentication
@app.post("/auth/register")
async def register(user: UserRegister):
    # Validate that at least one of email or phone is provided
    if not user.email and not user.phone:
        raise HTTPException(status_code=400, detail="Either email or phone number is required")
    
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, phone, password_hash, preferred_language) VALUES (?, ?, ?, ?, ?)",
            (user.name, user.email, user.phone, hash_password(user.password), user.preferred_language)
        )
        conn.commit()
        
        # Fetch the newly created user
        if user.email:
            cursor = conn.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        else:
            cursor = conn.execute("SELECT id FROM users WHERE phone = ?", (user.phone,))
        
        user_id = cursor.fetchone()[0]
        token = create_token(user_id)
        
        return {"token": token, "user_id": user_id, "message": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email or phone number already registered")
    finally:
        conn.close()

@app.post("/auth/login")
async def login(credentials: UserLogin):
    # Validate that at least one of email or phone is provided
    if not credentials.email and not credentials.phone:
        raise HTTPException(status_code=400, detail="Either email or phone number is required")
    
    conn = get_db()
    
    # Try to find user by email or phone
    if credentials.email:
        cursor = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ?",
            (credentials.email,)
        )
    else:
        cursor = conn.execute(
            "SELECT id, password_hash FROM users WHERE phone = ?",
            (credentials.phone,)
        )
    
    user = cursor.fetchone()
    conn.close()
    
    if not user or user[1] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user[0])
    return {"token": token, "user_id": user[0]}

# Khatm Management
@app.post("/khatms")
async def create_khatm(khatm: KhatmCreate, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    # Determine total portions
    total_portions = get_portion_count(khatm.content_type, khatm.portion_type, khatm.total_portions)
    
    # Create khatm
    cursor = conn.execute(
        """INSERT INTO khatms (title, description, creator_id, content_type, portion_type, 
           total_portions, language, deadline) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (khatm.title, khatm.description, user_id, khatm.content_type, khatm.portion_type, 
         total_portions, khatm.language, khatm.deadline)
    )
    khatm_id = cursor.lastrowid
    
    # Creator automatically joins
    conn.execute(
        "INSERT INTO participants (khatm_id, user_id) VALUES (?, ?)",
        (khatm_id, user_id)
    )
    
    # Initialize all portions
    for i in range(1, total_portions + 1):
        conn.execute(
            "INSERT INTO portions (khatm_id, portion_number) VALUES (?, ?)",
            (khatm_id, i)
        )
    
    conn.commit()
    conn.close()
    
    return {"khatm_id": khatm_id, "total_portions": total_portions, "message": "Khatm created successfully"}

@app.get("/khatms")
async def list_khatms(user_id: int = Depends(verify_token)):
    conn = get_db()
    cursor = conn.execute("""
        SELECT k.*, u.name as creator_name,
               COUNT(DISTINCT p.user_id) as participant_count,
               COUNT(CASE WHEN po.is_completed = 1 THEN 1 END) as completed_count,
               COUNT(po.id) as total_portions
        FROM khatms k
        JOIN users u ON k.creator_id = u.id
        LEFT JOIN participants p ON k.id = p.khatm_id
        LEFT JOIN portions po ON k.id = po.khatm_id
        WHERE k.status = 'active'
        GROUP BY k.id
        ORDER BY k.created_at DESC
    """)
    khatms = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"khatms": khatms}

@app.get("/khatms/{khatm_id}")
async def get_khatm(khatm_id: int, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    # Get khatm details
    cursor = conn.execute("""
        SELECT k.*, u.name as creator_name
        FROM khatms k
        JOIN users u ON k.creator_id = u.id
        WHERE k.id = ?
    """, (khatm_id,))
    khatm = cursor.fetchone()
    
    if not khatm:
        conn.close()
        raise HTTPException(status_code=404, detail="Khatm not found")
    
    # Get portions status
    cursor = conn.execute("""
        SELECT portion_number, user_id, u.name as user_name, 
               is_completed, assigned_at, completed_at
        FROM portions p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE p.khatm_id = ?
        ORDER BY p.portion_number
    """, (khatm_id,))
    portions = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return {"khatm": dict(khatm), "portions": portions}

@app.post("/khatms/{khatm_id}/join")
async def join_khatm(khatm_id: int, user_id: int = Depends(verify_token)):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO participants (khatm_id, user_id) VALUES (?, ?)",
            (khatm_id, user_id)
        )
        conn.commit()
        return {"message": "Joined khatm successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Already a participant")
    finally:
        conn.close()

@app.post("/khatms/{khatm_id}/assign")
async def assign_portion(khatm_id: int, portion: PortionAssign, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    # Check if user is participant
    cursor = conn.execute(
        "SELECT id FROM participants WHERE khatm_id = ? AND user_id = ?",
        (khatm_id, user_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Must join khatm first")
    
    # Try to assign portion
    try:
        result = conn.execute(
            "UPDATE portions SET user_id = ?, assigned_at = CURRENT_TIMESTAMP WHERE khatm_id = ? AND portion_number = ? AND user_id IS NULL",
            (user_id, khatm_id, portion.portion_number)
        )
        
        if result.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=400, detail="Portion already assigned")
        
        conn.commit()
        return {"message": "Portion assigned successfully"}
    finally:
        conn.close()

@app.put("/khatms/{khatm_id}/portions/{portion_number}/complete")
async def complete_portion(khatm_id: int, portion_number: int, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    result = conn.execute(
        "UPDATE portions SET is_completed = 1, completed_at = CURRENT_TIMESTAMP WHERE khatm_id = ? AND portion_number = ? AND user_id = ?",
        (khatm_id, portion_number, user_id)
    )
    
    if result.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Portion not found or not assigned to you")
    
    conn.commit()
    
    # Check if khatm is complete
    cursor = conn.execute(
        "SELECT COUNT(*) as total, SUM(is_completed) as completed FROM portions WHERE khatm_id = ?",
        (khatm_id,)
    )
    stats = cursor.fetchone()
    
    if stats[0] == stats[1]:
        conn.execute("UPDATE khatms SET status = 'completed' WHERE id = ?", (khatm_id,))
        conn.commit()
    
    conn.close()
    return {"message": "Portion marked as complete"}

@app.get("/khatms/{khatm_id}/stats")
async def get_khatm_stats(khatm_id: int, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as total_portions,
            SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed_portions,
            COUNT(DISTINCT user_id) as active_participants
        FROM portions
        WHERE khatm_id = ?
    """, (khatm_id,))
    
    stats = dict(cursor.fetchone())
    stats['completion_percentage'] = (stats['completed_portions'] / stats['total_portions'] * 100) if stats['total_portions'] > 0 else 0
    
    conn.close()
    return stats

@app.get("/users/me/stats")
async def get_user_stats(user_id: int = Depends(verify_token)):
    conn = get_db()
    
    cursor = conn.execute("""
        SELECT 
            COUNT(DISTINCT khatm_id) as khatms_joined,
            COUNT(*) as portions_assigned,
            SUM(is_completed) as portions_completed
        FROM portions
        WHERE user_id = ?
    """, (user_id,))
    
    stats = dict(cursor.fetchone())
    conn.close()
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000), cleaned):
            raise ValueError('Phone number must be in international format (e.g., +491234567890)')
        return cleaned

class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        # Remove all spaces, dashes, and parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        # Check if it matches international format: + followed by 7-15 digits
        if not re.match(r'^\+[1-9]\d{6,14}

class KhatmCreate(BaseModel):
    title: str
    description: Optional[str] = None
    portion_type: str = "juz"  # juz, hezb, or quarter
    deadline: Optional[str] = None  # ISO format date
    language: str = "en"

class PortionAssign(BaseModel):
    portion_number: int

# ============= Database Setup =============

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        preferred_language TEXT DEFAULT 'en',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Khatms table
    c.execute('''CREATE TABLE IF NOT EXISTS khatms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        creator_id INTEGER NOT NULL,
        portion_type TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        language TEXT DEFAULT 'en',
        deadline TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (creator_id) REFERENCES users(id)
    )''')
    
    # Participants table
    c.execute('''CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        khatm_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (khatm_id) REFERENCES khatms(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(khatm_id, user_id)
    )''')
    
    # Portions table
    c.execute('''CREATE TABLE IF NOT EXISTS portions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        khatm_id INTEGER NOT NULL,
        user_id INTEGER,
        portion_number INTEGER NOT NULL,
        is_completed BOOLEAN DEFAULT 0,
        assigned_at TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (khatm_id) REFERENCES khatms(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(khatm_id, portion_number)
    )''')
    
    conn.commit()
    conn.close()

# ============= Helper Functions =============

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_portion_count(portion_type: str) -> int:
    """Returns total number of portions based on type"""
    counts = {"juz": 30, "hezb": 60, "quarter": 240}
    return counts.get(portion_type, 30)

# ============= API Endpoints =============

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/")
async def root():
    return {"message": "Quran Khatm API", "version": "1.0.0"}

# Authentication
@app.post("/auth/register")
async def register(user: UserRegister):
    # Validate that at least one of email or phone is provided
    if not user.email and not user.phone:
        raise HTTPException(status_code=400, detail="Either email or phone number is required")
    
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, phone, password_hash, preferred_language) VALUES (?, ?, ?, ?, ?)",
            (user.name, user.email, user.phone, hash_password(user.password), user.preferred_language)
        )
        conn.commit()
        
        # Fetch the newly created user
        if user.email:
            cursor = conn.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        else:
            cursor = conn.execute("SELECT id FROM users WHERE phone = ?", (user.phone,))
        
        user_id = cursor.fetchone()[0]
        token = create_token(user_id)
        
        return {"token": token, "user_id": user_id, "message": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email or phone number already registered")
    finally:
        conn.close()

@app.post("/auth/login")
async def login(credentials: UserLogin):
    # Validate that at least one of email or phone is provided
    if not credentials.email and not credentials.phone:
        raise HTTPException(status_code=400, detail="Either email or phone number is required")
    
    conn = get_db()
    
    # Try to find user by email or phone
    if credentials.email:
        cursor = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ?",
            (credentials.email,)
        )
    else:
        cursor = conn.execute(
            "SELECT id, password_hash FROM users WHERE phone = ?",
            (credentials.phone,)
        )
    
    user = cursor.fetchone()
    conn.close()
    
    if not user or user[1] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user[0])
    return {"token": token, "user_id": user[0]}

# Khatm Management
@app.post("/khatms")
async def create_khatm(khatm: KhatmCreate, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    # Create khatm
    cursor = conn.execute(
        "INSERT INTO khatms (title, description, creator_id, portion_type, language, deadline) VALUES (?, ?, ?, ?, ?, ?)",
        (khatm.title, khatm.description, user_id, khatm.portion_type, khatm.language, khatm.deadline)
    )
    khatm_id = cursor.lastrowid
    
    # Creator automatically joins
    conn.execute(
        "INSERT INTO participants (khatm_id, user_id) VALUES (?, ?)",
        (khatm_id, user_id)
    )
    
    # Initialize all portions
    portion_count = get_portion_count(khatm.portion_type)
    for i in range(1, portion_count + 1):
        conn.execute(
            "INSERT INTO portions (khatm_id, portion_number) VALUES (?, ?)",
            (khatm_id, i)
        )
    
    conn.commit()
    conn.close()
    
    return {"khatm_id": khatm_id, "message": "Khatm created successfully"}

@app.get("/khatms")
async def list_khatms(user_id: int = Depends(verify_token)):
    conn = get_db()
    cursor = conn.execute("""
        SELECT k.*, u.name as creator_name,
               COUNT(DISTINCT p.user_id) as participant_count,
               COUNT(CASE WHEN po.is_completed = 1 THEN 1 END) as completed_count,
               COUNT(po.id) as total_portions
        FROM khatms k
        JOIN users u ON k.creator_id = u.id
        LEFT JOIN participants p ON k.id = p.khatm_id
        LEFT JOIN portions po ON k.id = po.khatm_id
        WHERE k.status = 'active'
        GROUP BY k.id
        ORDER BY k.created_at DESC
    """)
    khatms = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"khatms": khatms}

@app.get("/khatms/{khatm_id}")
async def get_khatm(khatm_id: int, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    # Get khatm details
    cursor = conn.execute("""
        SELECT k.*, u.name as creator_name
        FROM khatms k
        JOIN users u ON k.creator_id = u.id
        WHERE k.id = ?
    """, (khatm_id,))
    khatm = cursor.fetchone()
    
    if not khatm:
        conn.close()
        raise HTTPException(status_code=404, detail="Khatm not found")
    
    # Get portions status
    cursor = conn.execute("""
        SELECT portion_number, user_id, u.name as user_name, 
               is_completed, assigned_at, completed_at
        FROM portions p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE p.khatm_id = ?
        ORDER BY p.portion_number
    """, (khatm_id,))
    portions = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return {"khatm": dict(khatm), "portions": portions}

@app.post("/khatms/{khatm_id}/join")
async def join_khatm(khatm_id: int, user_id: int = Depends(verify_token)):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO participants (khatm_id, user_id) VALUES (?, ?)",
            (khatm_id, user_id)
        )
        conn.commit()
        return {"message": "Joined khatm successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Already a participant")
    finally:
        conn.close()

@app.post("/khatms/{khatm_id}/assign")
async def assign_portion(khatm_id: int, portion: PortionAssign, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    # Check if user is participant
    cursor = conn.execute(
        "SELECT id FROM participants WHERE khatm_id = ? AND user_id = ?",
        (khatm_id, user_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Must join khatm first")
    
    # Try to assign portion
    try:
        result = conn.execute(
            "UPDATE portions SET user_id = ?, assigned_at = CURRENT_TIMESTAMP WHERE khatm_id = ? AND portion_number = ? AND user_id IS NULL",
            (user_id, khatm_id, portion.portion_number)
        )
        
        if result.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=400, detail="Portion already assigned")
        
        conn.commit()
        return {"message": "Portion assigned successfully"}
    finally:
        conn.close()

@app.put("/khatms/{khatm_id}/portions/{portion_number}/complete")
async def complete_portion(khatm_id: int, portion_number: int, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    result = conn.execute(
        "UPDATE portions SET is_completed = 1, completed_at = CURRENT_TIMESTAMP WHERE khatm_id = ? AND portion_number = ? AND user_id = ?",
        (khatm_id, portion_number, user_id)
    )
    
    if result.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Portion not found or not assigned to you")
    
    conn.commit()
    
    # Check if khatm is complete
    cursor = conn.execute(
        "SELECT COUNT(*) as total, SUM(is_completed) as completed FROM portions WHERE khatm_id = ?",
        (khatm_id,)
    )
    stats = cursor.fetchone()
    
    if stats[0] == stats[1]:
        conn.execute("UPDATE khatms SET status = 'completed' WHERE id = ?", (khatm_id,))
        conn.commit()
    
    conn.close()
    return {"message": "Portion marked as complete"}

@app.get("/khatms/{khatm_id}/stats")
async def get_khatm_stats(khatm_id: int, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as total_portions,
            SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed_portions,
            COUNT(DISTINCT user_id) as active_participants
        FROM portions
        WHERE khatm_id = ?
    """, (khatm_id,))
    
    stats = dict(cursor.fetchone())
    stats['completion_percentage'] = (stats['completed_portions'] / stats['total_portions'] * 100) if stats['total_portions'] > 0 else 0
    
    conn.close()
    return stats

@app.get("/users/me/stats")
async def get_user_stats(user_id: int = Depends(verify_token)):
    conn = get_db()
    
    cursor = conn.execute("""
        SELECT 
            COUNT(DISTINCT khatm_id) as khatms_joined,
            COUNT(*) as portions_assigned,
            SUM(is_completed) as portions_completed
        FROM portions
        WHERE user_id = ?
    """, (user_id,))
    
    stats = dict(cursor.fetchone())
    conn.close()
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000), cleaned):
            raise ValueError('Phone number must be in international format (e.g., +491234567890)')
        return cleaned

class KhatmCreate(BaseModel):
    title: str
    description: Optional[str] = None
    portion_type: str = "juz"  # juz, hezb, or quarter
    deadline: Optional[str] = None  # ISO format date
    language: str = "en"

class PortionAssign(BaseModel):
    portion_number: int

# ============= Database Setup =============

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        preferred_language TEXT DEFAULT 'en',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Khatms table
    c.execute('''CREATE TABLE IF NOT EXISTS khatms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        creator_id INTEGER NOT NULL,
        portion_type TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        language TEXT DEFAULT 'en',
        deadline TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (creator_id) REFERENCES users(id)
    )''')
    
    # Participants table
    c.execute('''CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        khatm_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (khatm_id) REFERENCES khatms(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(khatm_id, user_id)
    )''')
    
    # Portions table
    c.execute('''CREATE TABLE IF NOT EXISTS portions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        khatm_id INTEGER NOT NULL,
        user_id INTEGER,
        portion_number INTEGER NOT NULL,
        is_completed BOOLEAN DEFAULT 0,
        assigned_at TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (khatm_id) REFERENCES khatms(id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(khatm_id, portion_number)
    )''')
    
    conn.commit()
    conn.close()

# ============= Helper Functions =============

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_portion_count(portion_type: str) -> int:
    """Returns total number of portions based on type"""
    counts = {"juz": 30, "hezb": 60, "quarter": 240}
    return counts.get(portion_type, 30)

# ============= API Endpoints =============

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/")
async def root():
    return {"message": "Quran Khatm API", "version": "1.0.0"}

# Authentication
@app.post("/auth/register")
async def register(user: UserRegister):
    # Validate that at least one of email or phone is provided
    if not user.email and not user.phone:
        raise HTTPException(status_code=400, detail="Either email or phone number is required")
    
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (name, email, phone, password_hash, preferred_language) VALUES (?, ?, ?, ?, ?)",
            (user.name, user.email, user.phone, hash_password(user.password), user.preferred_language)
        )
        conn.commit()
        
        # Fetch the newly created user
        if user.email:
            cursor = conn.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        else:
            cursor = conn.execute("SELECT id FROM users WHERE phone = ?", (user.phone,))
        
        user_id = cursor.fetchone()[0]
        token = create_token(user_id)
        
        return {"token": token, "user_id": user_id, "message": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email or phone number already registered")
    finally:
        conn.close()

@app.post("/auth/login")
async def login(credentials: UserLogin):
    # Validate that at least one of email or phone is provided
    if not credentials.email and not credentials.phone:
        raise HTTPException(status_code=400, detail="Either email or phone number is required")
    
    conn = get_db()
    
    # Try to find user by email or phone
    if credentials.email:
        cursor = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ?",
            (credentials.email,)
        )
    else:
        cursor = conn.execute(
            "SELECT id, password_hash FROM users WHERE phone = ?",
            (credentials.phone,)
        )
    
    user = cursor.fetchone()
    conn.close()
    
    if not user or user[1] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user[0])
    return {"token": token, "user_id": user[0]}

# Khatm Management
@app.post("/khatms")
async def create_khatm(khatm: KhatmCreate, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    # Create khatm
    cursor = conn.execute(
        "INSERT INTO khatms (title, description, creator_id, portion_type, language, deadline) VALUES (?, ?, ?, ?, ?, ?)",
        (khatm.title, khatm.description, user_id, khatm.portion_type, khatm.language, khatm.deadline)
    )
    khatm_id = cursor.lastrowid
    
    # Creator automatically joins
    conn.execute(
        "INSERT INTO participants (khatm_id, user_id) VALUES (?, ?)",
        (khatm_id, user_id)
    )
    
    # Initialize all portions
    portion_count = get_portion_count(khatm.portion_type)
    for i in range(1, portion_count + 1):
        conn.execute(
            "INSERT INTO portions (khatm_id, portion_number) VALUES (?, ?)",
            (khatm_id, i)
        )
    
    conn.commit()
    conn.close()
    
    return {"khatm_id": khatm_id, "message": "Khatm created successfully"}

@app.get("/khatms")
async def list_khatms(user_id: int = Depends(verify_token)):
    conn = get_db()
    cursor = conn.execute("""
        SELECT k.*, u.name as creator_name,
               COUNT(DISTINCT p.user_id) as participant_count,
               COUNT(CASE WHEN po.is_completed = 1 THEN 1 END) as completed_count,
               COUNT(po.id) as total_portions
        FROM khatms k
        JOIN users u ON k.creator_id = u.id
        LEFT JOIN participants p ON k.id = p.khatm_id
        LEFT JOIN portions po ON k.id = po.khatm_id
        WHERE k.status = 'active'
        GROUP BY k.id
        ORDER BY k.created_at DESC
    """)
    khatms = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"khatms": khatms}

@app.get("/khatms/{khatm_id}")
async def get_khatm(khatm_id: int, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    # Get khatm details
    cursor = conn.execute("""
        SELECT k.*, u.name as creator_name
        FROM khatms k
        JOIN users u ON k.creator_id = u.id
        WHERE k.id = ?
    """, (khatm_id,))
    khatm = cursor.fetchone()
    
    if not khatm:
        conn.close()
        raise HTTPException(status_code=404, detail="Khatm not found")
    
    # Get portions status
    cursor = conn.execute("""
        SELECT portion_number, user_id, u.name as user_name, 
               is_completed, assigned_at, completed_at
        FROM portions p
        LEFT JOIN users u ON p.user_id = u.id
        WHERE p.khatm_id = ?
        ORDER BY p.portion_number
    """, (khatm_id,))
    portions = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return {"khatm": dict(khatm), "portions": portions}

@app.post("/khatms/{khatm_id}/join")
async def join_khatm(khatm_id: int, user_id: int = Depends(verify_token)):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO participants (khatm_id, user_id) VALUES (?, ?)",
            (khatm_id, user_id)
        )
        conn.commit()
        return {"message": "Joined khatm successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Already a participant")
    finally:
        conn.close()

@app.post("/khatms/{khatm_id}/assign")
async def assign_portion(khatm_id: int, portion: PortionAssign, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    # Check if user is participant
    cursor = conn.execute(
        "SELECT id FROM participants WHERE khatm_id = ? AND user_id = ?",
        (khatm_id, user_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=403, detail="Must join khatm first")
    
    # Try to assign portion
    try:
        result = conn.execute(
            "UPDATE portions SET user_id = ?, assigned_at = CURRENT_TIMESTAMP WHERE khatm_id = ? AND portion_number = ? AND user_id IS NULL",
            (user_id, khatm_id, portion.portion_number)
        )
        
        if result.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=400, detail="Portion already assigned")
        
        conn.commit()
        return {"message": "Portion assigned successfully"}
    finally:
        conn.close()

@app.put("/khatms/{khatm_id}/portions/{portion_number}/complete")
async def complete_portion(khatm_id: int, portion_number: int, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    result = conn.execute(
        "UPDATE portions SET is_completed = 1, completed_at = CURRENT_TIMESTAMP WHERE khatm_id = ? AND portion_number = ? AND user_id = ?",
        (khatm_id, portion_number, user_id)
    )
    
    if result.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Portion not found or not assigned to you")
    
    conn.commit()
    
    # Check if khatm is complete
    cursor = conn.execute(
        "SELECT COUNT(*) as total, SUM(is_completed) as completed FROM portions WHERE khatm_id = ?",
        (khatm_id,)
    )
    stats = cursor.fetchone()
    
    if stats[0] == stats[1]:
        conn.execute("UPDATE khatms SET status = 'completed' WHERE id = ?", (khatm_id,))
        conn.commit()
    
    conn.close()
    return {"message": "Portion marked as complete"}

@app.get("/khatms/{khatm_id}/stats")
async def get_khatm_stats(khatm_id: int, user_id: int = Depends(verify_token)):
    conn = get_db()
    
    cursor = conn.execute("""
        SELECT 
            COUNT(*) as total_portions,
            SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed_portions,
            COUNT(DISTINCT user_id) as active_participants
        FROM portions
        WHERE khatm_id = ?
    """, (khatm_id,))
    
    stats = dict(cursor.fetchone())
    stats['completion_percentage'] = (stats['completed_portions'] / stats['total_portions'] * 100) if stats['total_portions'] > 0 else 0
    
    conn.close()
    return stats

@app.get("/users/me/stats")
async def get_user_stats(user_id: int = Depends(verify_token)):
    conn = get_db()
    
    cursor = conn.execute("""
        SELECT 
            COUNT(DISTINCT khatm_id) as khatms_joined,
            COUNT(*) as portions_assigned,
            SUM(is_completed) as portions_completed
        FROM portions
        WHERE user_id = ?
    """, (user_id,))
    
    stats = dict(cursor.fetchone())
    conn.close()
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)