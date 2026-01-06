import json
import sqlite3

from fastapi import HTTPException

from src.models.recitation import ContentTypeCreate


class AdminService:
    @staticmethod
    def create_content_type(content_type: ContentTypeCreate, user_id: int, conn) -> dict:
        """Create a new content type"""
        try:
            # Convert dict to JSON string for storage
            portion_types_json = json.dumps(content_type.default_portion_types)

            conn.execute(
                """INSERT INTO content_types (name, display_name, description, default_portion_types, created_by) 
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    content_type.name,
                    content_type.display_name,
                    content_type.description,
                    portion_types_json,
                    user_id,
                ),
            )
            conn.commit()

            cursor = conn.execute(
                "SELECT id FROM content_types WHERE name = ?", (content_type.name,)
            )
            content_type_id = cursor.fetchone()[0]

            return {
                "id": content_type_id,
                "name": content_type.name,
                "message": "Content type created successfully",
            }
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=400, detail="Content type with this name already exists"
            )

    @staticmethod
    def list_content_types(conn, include_inactive: bool = False) -> list:
        """List all content types"""
        if include_inactive:
            cursor = conn.execute(
                "SELECT id, name, display_name, description, default_portion_types, is_active, created_at FROM content_types"
            )
        else:
            cursor = conn.execute(
                "SELECT id, name, display_name, description, default_portion_types, is_active, created_at FROM content_types WHERE is_active = 1"
            )

        types = []
        for row in cursor.fetchall():
            type_dict = dict(row)
            # Parse JSON string back to dict
            if type_dict["default_portion_types"]:
                try:
                    type_dict["default_portion_types"] = json.loads(
                        type_dict["default_portion_types"]
                    )
                except json.JSONDecodeError:
                    type_dict["default_portion_types"] = {}
            types.append(type_dict)

        return types

    @staticmethod
    def update_content_type(content_type_id: int, updates: dict, conn) -> dict:
        """Update a content type"""
        allowed_fields = ["display_name", "description", "default_portion_types", "is_active"]
        update_parts = []
        values = []

        for field, value in updates.items():
            if field in allowed_fields:
                if field == "default_portion_types":
                    value = json.dumps(value)
                update_parts.append(f"{field} = ?")
                values.append(value)

        if not update_parts:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        values.append(content_type_id)
        query = f"UPDATE content_types SET {', '.join(update_parts)} WHERE id = ?"

        result = conn.execute(query, values)
        conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Content type not found")

        return {"message": "Content type updated successfully"}

    @staticmethod
    def toggle_content_type(content_type_id: int, conn) -> dict:
        """Activate or deactivate a content type"""
        cursor = conn.execute(
            "SELECT is_active FROM content_types WHERE id = ?", (content_type_id,)
        )
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Content type not found")

        new_status = 0 if result[0] else 1
        conn.execute(
            "UPDATE content_types SET is_active = ? WHERE id = ?", (new_status, content_type_id)
        )
        conn.commit()

        return {
            "message": f"Content type {'activated' if new_status else 'deactivated'} successfully",
            "is_active": bool(new_status),
        }
