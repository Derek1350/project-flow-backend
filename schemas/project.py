import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Annotated

# Shared properties
class ProjectBase(BaseModel):
    name: str
    key: Annotated[str, Field(max_length=4)]
    description: Optional[str] = None

# Properties to receive on project creation
class ProjectCreate(ProjectBase):
    pass

# Properties to receive on project update
class ProjectUpdate(ProjectBase):
    pass

# Properties shared by models stored in DB
class ProjectInDBBase(ProjectBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Properties to return to client
class Project(ProjectInDBBase):
    pass

