import sqlite3

from fastapi import HTTPException

from src.models.user import UserLogin, UserRegister
from src.utils.security import create_token, hash_password


class AuthService:
    @staticmethod
    def register_user(user: UserRegister, conn) -> dict:
        if not user.email and not user.phone:
            raise HTTPException(status_code=400, detail="Either email or phone number is required")

        try:
            conn.execute(
                "INSERT INTO users (name, email, phone, password_hash, preferred_language) VALUES (?, ?, ?, ?, ?)",
                (
                    user.name,
                    user.email,
                    user.phone,
                    hash_password(user.password),
                    user.preferred_language,
                ),
            )
            conn.commit()

            if user.email:
                cursor = conn.execute("SELECT id FROM users WHERE email = ?", (user.email,))
            else:
                cursor = conn.execute("SELECT id FROM users WHERE phone = ?", (user.phone,))

            user_id = cursor.fetchone()[0]
            token = create_token(user_id)

            return {"token": token, "user_id": user_id, "message": "User registered successfully"}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Email or phone number already registered")

    @staticmethod
    def login_user(credentials: UserLogin, conn) -> dict:
        if not credentials.email and not credentials.phone:
            raise HTTPException(status_code=400, detail="Either email or phone number is required")

        if credentials.email:
            cursor = conn.execute(
                "SELECT id, password_hash FROM users WHERE email = ?", (credentials.email,)
            )
        else:
            cursor = conn.execute(
                "SELECT id, password_hash FROM users WHERE phone = ?", (credentials.phone,)
            )

        user = cursor.fetchone()

        if not user or user[1] != hash_password(credentials.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_token(user[0])
        return {"token": token, "user_id": user[0]}
