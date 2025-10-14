from uuid import UUID
from pydantic import BaseModel, EmailStr

from .base import ProjectRole
from .user import User # Import the User schema to nest it

# Properties to receive on member creation
class ProjectMemberCreate(BaseModel):
    email: EmailStr
    role: ProjectRole = ProjectRole.MEMBER

# Properties to receive on member update
class ProjectMemberUpdate(BaseModel):
    role: ProjectRole

# Properties to return to client
class ProjectMemberRead(BaseModel):
    project_id: UUID
    user_id: UUID
    role: ProjectRole
    user: User # Nest the full user object

    class Config:
        from_attributes = True

