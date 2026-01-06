from fastapi import APIRouter, Depends, Query

from src.database.connection import get_db
from src.models.recitation import ContentTypeCreate
from src.services.admin_service import AdminService
from src.utils.security import security, verify_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/content-types")
async def create_content_type(
    content_type: ContentTypeCreate,
    conn=Depends(get_db),
    user_id: int = Depends(lambda c=Depends(get_db): verify_admin(Depends(security), c)),
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
    user_id: int = Depends(lambda c=Depends(get_db): verify_admin(Depends(security), c)),
):
    """Update a content type (Admin only)"""
    return AdminService.update_content_type(content_type_id, updates, conn)


@router.post("/content-types/{content_type_id}/toggle")
async def toggle_content_type(
    content_type_id: int,
    conn=Depends(get_db),
    user_id: int = Depends(lambda c=Depends(get_db): verify_admin(Depends(security), c)),
):
    """Activate or deactivate a content type (Admin only)"""
    return AdminService.toggle_content_type(content_type_id, conn)
