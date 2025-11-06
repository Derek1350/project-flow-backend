import uuid
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
from .base import IssueStatus, IssuePriority, IssueType
from .user import User as UserSchema

# Properties to receive on issue creation - fields are required here
class IssueCreate(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: uuid.UUID
    status: IssueStatus = IssueStatus.PROPOSED
    priority: IssuePriority = IssuePriority.MEDIUM
    issue_type: IssueType = IssueType.TASK
    assignee_id: Optional[uuid.UUID] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    phase_id: Optional[uuid.UUID] = None # <-- ADDED


# Properties to receive on issue update - all fields are explicitly optional
class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    issue_type: Optional[IssueType] = None
    assignee_id: Optional[uuid.UUID] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    phase_id: Optional[uuid.UUID] = None # <-- ADDED


# Properties shared by models stored in DB
class IssueInDBBase(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: IssueStatus
    priority: IssuePriority
    issue_type: IssueType
    project_id: uuid.UUID
    reporter_id: uuid.UUID
    assignee_id: Optional[uuid.UUID] = None
    assignee_request_id: Optional[uuid.UUID] = None 
    created_at: datetime
    updated_at: datetime
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    phase_id: Optional[uuid.UUID] = None # <-- ADDED

    class Config:
        from_attributes = True

# Properties to return to client
class Issue(IssueInDBBase):
    reporter: Optional[UserSchema] = None 
    assignee: Optional[UserSchema] = None 
    requester: Optional[UserSchema] = None
    # We can add 'phase: Optional[Phase] = None' here later