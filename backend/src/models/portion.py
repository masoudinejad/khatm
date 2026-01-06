from typing import Optional

from pydantic import BaseModel


class PortionAssign(BaseModel):
    portion_number: int


class PortionProgress(BaseModel):
    progress_percentage: int
    notes: Optional[str] = None
