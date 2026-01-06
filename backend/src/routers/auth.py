from fastapi import APIRouter, Depends
from src.models.user import UserRegister, UserLogin
from src.services.auth_service import AuthService
from src.database.connection import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
async def register(user: UserRegister, conn=Depends(get_db)):
    return AuthService.register_user(user, conn)


@router.post("/login")
async def login(credentials: UserLogin, conn=Depends(get_db)):
    return AuthService.login_user(credentials, conn)
