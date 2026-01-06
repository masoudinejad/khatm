import json
from typing import Optional

from fastapi import HTTPException


def get_portion_count(
    content_type: str, portion_type: str, custom_total: Optional[int], conn
) -> int:
    """Returns total number of portions based on content type and portion type.
    Checks database for dynamic content types first, falls back to hardcoded defaults."""

    # Custom content types always require explicit total
    if content_type == "custom" or custom_total is not None:
        if custom_total is None:
            raise HTTPException(
                status_code=400, detail="total_portions required for custom content"
            )
        return custom_total

    # Check database for content type
    cursor = conn.execute(
        "SELECT default_portion_types FROM content_types WHERE name = ? AND is_active = 1",
        (content_type,),
    )
    result = cursor.fetchone()

    if result and result[0]:
        try:
            portion_types = json.loads(result[0])
            if portion_type in portion_types:
                return portion_types[portion_type]
        except json.JSONDecodeError:
            pass

    # If no match in database or JSON, require custom total
    if custom_total is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported combination: {content_type}/{portion_type}. Please provide total_portions or contact admin to add this configuration.",
        )

    return custom_total
