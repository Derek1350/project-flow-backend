import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum,
    Boolean, Table, Date  # Added Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base

# --- Enums ---
class IssueStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    TO_DO = "TO_DO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"

class IssuePriority(str, enum.Enum):
    LOWEST = "LOWEST"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    HIGHEST = "HIGHEST"

class IssueType(str, enum.Enum):
    TASK = "TASK"
    BUG = "BUG"
    STORY = "STORY"
    EPIC = "EPIC"

class ProjectRole(str, enum.Enum):
    ADMIN = "ADMIN"
    PROJECT_LEAD = "PROJECT_LEAD"
    MEMBER = "MEMBER"

# --- Association Model ---

class ProjectMember(Base):
    __tablename__ = 'project_members'
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete="CASCADE"), primary_key=True)
    role = Column(SQLAlchemyEnum(ProjectRole), nullable=False, default=ProjectRole.MEMBER)

    user = relationship("User", back_populates="memberships")
    project = relationship("Project", back_populates="memberships")

# --- Main Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")
    
    reported_issues = relationship("Issue", back_populates="reporter", foreign_keys="[Issue.reporter_id]")
    assigned_issues = relationship("Issue", back_populates="assignee", foreign_keys="[Issue.assignee_id]")
    # New relationship for requested issues
    requested_issues = relationship("Issue", back_populates="requester", foreign_keys="[Issue.assignee_request_id]")


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    key = Column(String(4), nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    memberships = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="project", cascade="all, delete-orphan")


class Issue(Base):
    __tablename__ = "issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(SQLAlchemyEnum(IssueStatus, name="issue_status_enum"), nullable=False, default=IssueStatus.PROPOSED)
    priority = Column(SQLAlchemyEnum(IssuePriority, name="issue_priority_enum"), nullable=False, default=IssuePriority.MEDIUM)
    issue_type = Column(SQLAlchemyEnum(IssueType, name="issue_type_enum"), nullable=False, default=IssueType.TASK)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # New column to track who requested the issue
    assignee_request_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # --- NEW DATE COLUMNS ---
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    # --- END NEW DATE COLUMNS ---

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="issues")
    reporter = relationship("User", back_populates="reported_issues", foreign_keys=[reporter_id])
    assignee = relationship("User", back_populates="assigned_issues", foreign_keys=[assignee_id])
    requester = relationship("User", back_populates="requested_issues", foreign_keys=[assignee_request_id])
