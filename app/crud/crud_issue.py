import uuid
from sqlalchemy.orm import Session, joinedload
from ..schemas import issue as issue_schema

# --- FIX: Import Enums from the db.models file to avoid conflicts ---
from ..db.models import Issue, User
from ..db.models import IssueStatus as DB_IssueStatus
from ..db.models import IssuePriority as DB_IssuePriority
from ..db.models import IssueType as DB_IssueType

def get_issue(db: Session, issue_id: uuid.UUID) -> Issue | None:
    """
    Get a single issue by its ID, eagerly loading related user objects.
    """
    return db.query(Issue).options(
        joinedload(Issue.assignee),
        joinedload(Issue.reporter),
        joinedload(Issue.requester)
    ).filter(Issue.id == issue_id).first()

def get_issues_by_project(db: Session, project_id: uuid.UUID) -> list[Issue]:
    """
    Get all issues for a project, eagerly loading related user objects.
    """
    return db.query(Issue).options(
        joinedload(Issue.assignee),
        joinedload(Issue.reporter),
        joinedload(Issue.requester)
    ).filter(Issue.project_id == project_id).all()

def create_issue(db: Session, issue_in: issue_schema.IssueCreate, reporter_id: uuid.UUID) -> Issue:
    """
    Create a new issue.
    """
    db_issue = Issue(
        title=issue_in.title,
        description=issue_in.description,
        status=DB_IssueStatus(issue_in.status.value),
        priority=DB_IssuePriority(issue_in.priority.value),
        issue_type=DB_IssueType(issue_in.issue_type.value),
        project_id=issue_in.project_id,
        reporter_id=reporter_id,
        assignee_id=issue_in.assignee_id,
        start_date=issue_in.start_date,
        due_date=issue_in.due_date,
        phase_id=issue_in.phase_id # <-- ADDED
    )
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    return db_issue

def update_issue(db: Session, db_obj: Issue, obj_in: issue_schema.IssueUpdate) -> Issue:
    """
    Update an existing issue.
    """
    update_data = obj_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        # ... (enum conversion logic remains the same) ...
        
        # --- ADDED: Explicitly handle phase_id ---
        if field == 'phase_id':
            setattr(db_obj, 'phase_id', value)
        elif field == 'status' and value is not None:
            value = DB_IssueStatus(value.value)
            setattr(db_obj, field, value)
        elif field == 'priority' and value is not None:
            value = DB_IssuePriority(value.value)
            setattr(db_obj, field, value)
        elif field == 'issue_type' and value is not None:
            value = DB_IssueType(value.value)
            setattr(db_obj, field, value)
        else:
             setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_issue(db: Session, issue_id: uuid.UUID) -> Issue | None:
    """
    Delete an issue by its ID.
    """
    db_issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if db_issue:
        db.delete(db_issue)
        db.commit()
    return db_issue

# --- New functions for request workflow ---

def request_issue(db: Session, issue: Issue, user: User) -> Issue:
    """Set the user as the requester for an issue."""
    issue.assignee_request_id = user.id
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue

def approve_request(db: Session, issue: Issue) -> Issue:
    """Approve a request, making the requester the assignee."""
    if issue.assignee_request_id:
        issue.assignee_id = issue.assignee_request_id
        issue.assignee_request_id = None
        db.add(issue)
        db.commit()
        db.refresh(issue)
    return issue

def reject_request(db: Session, issue: Issue) -> Issue:
    """Reject a request, clearing the requester field."""
    issue.assignee_request_id = None
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue

