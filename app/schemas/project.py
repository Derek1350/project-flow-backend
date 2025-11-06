import uuid
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, Annotated, List

from .user import User as UserSchema
from .issue import Issue  
from .member import ProjectMemberRead
from .phase import Phase as PhaseSchema 

# Shared properties
class ProjectBase(BaseModel):
    name: str
    key: Annotated[str, Field(max_length=4)]
    description: Optional[str] = None

# Properties to receive on project creation
class ProjectCreate(ProjectBase):
    project_lead_email: Optional[EmailStr] = None
    members: Optional[List[EmailStr]] = []

# Properties to receive on project update
class ProjectUpdate(ProjectBase):
    pass

# Properties shared by models stored in DB
class ProjectInDBBase(ProjectBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Properties to return to client for a basic project
class Project(ProjectInDBBase):
    pass

# --- New Schemas for Detailed Project View ---

class IssueSummary(BaseModel):
    total: int
    todo: int
    in_progress: int
    in_review: int
    done: int

class ProjectWithDetails(Project):
    issue_summary: IssueSummary
    project_lead: Optional[UserSchema] = None
    progress: float
    members: List[ProjectMemberRead] = []  
    issues: List[Issue] = []
    phases: List[PhaseSchema] = []
    phase_progress: Optional[float] = None