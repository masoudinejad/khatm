from typing import Optional

from pydantic import BaseModel


class RecitationCreate(BaseModel):
    title: str
    description: Optional[str] = None
    content_type: str = "quran"
    portion_type: str = "juz"
    total_portions: Optional[int] = None
    deadline: Optional[str] = None
    language: str = "en"


class ContentTypeCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    default_portion_types: dict[str, int] = {}
