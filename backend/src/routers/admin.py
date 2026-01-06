from fastapi import APIRouter, Depends, Query

from src.database.connection import get_db
from src.models.recitation import ContentTypeCreate
from src.services.admin_service import AdminService
from src.utils.security import verify_token

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_admin_user(user_id: int = Depends(verify_token), conn=Depends(get_db)) -> int:
    """Verify user is admin"""
    from fastapi import HTTPException

    cursor = conn.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    if not result or not result[0]:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    return user_id


@router.post("/content-types")
async def create_content_type(
    content_type: ContentTypeCreate, conn=Depends(get_db), user_id: int = Depends(get_admin_user)
):
    """Create a new content type (Admin only)"""
    return AdminService.create_content_type(content_type, user_id, conn)


@router.get("/content-types")
async def list_content_types(
    include_inactive: bool = Query(False, description="Include inactive content types"),
    conn=Depends(get_db),
):
    """List all content types (Public endpoint)"""
    return {"content_types": AdminService.list_content_types(conn, include_inactive)}


@router.patch("/content-types/{content_type_id}")
async def update_content_type(
    content_type_id: int,
    updates: dict,
    conn=Depends(get_db),
    user_id: int = Depends(get_admin_user),
):
    """Update a content type (Admin only)"""
    return AdminService.update_content_type(content_type_id, updates, conn)


@router.post("/content-types/{content_type_id}/toggle")
async def toggle_content_type(
    content_type_id: int, conn=Depends(get_db), user_id: int = Depends(get_admin_user)
):
    """Activate or deactivate a content type (Admin only)"""
    return AdminService.toggle_content_type(content_type_id, conn)
