import uuid
from pydantic import BaseModel
from datetime import date
from typing import Optional, List

# Base properties for a Phase
class PhaseBase(BaseModel):
    name: str
    start_date: date
    end_date: date

# Properties to receive on creation
class PhaseCreate(PhaseBase):
    pass

# Properties to receive on update
class PhaseUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

# Properties to return to client
class Phase(PhaseBase):
    id: uuid.UUID
    project_id: uuid.UUID
    order: int

    class Config:
        from_attributes = True

# Schema for reordering
class PhaseOrderUpdate(BaseModel):
    id: uuid.UUID
    order: int