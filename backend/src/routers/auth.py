from fastapi import APIRouter, Depends

from src.database.connection import get_db
from src.models.user import UserLogin, UserRegister
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
async def register(user: UserRegister, conn=Depends(get_db)):
    return AuthService.register_user(user, conn)


@router.post("/login")
async def login(credentials: UserLogin, conn=Depends(get_db)):
    return AuthService.login_user(credentials, conn)
