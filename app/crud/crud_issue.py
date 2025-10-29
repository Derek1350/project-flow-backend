import uuid
from sqlalchemy.orm import Session, joinedload
from ..schemas import issue as issue_schema
from ..db.models import Issue, User

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
        status=issue_in.status,
        priority=issue_in.priority,
        issue_type=issue_in.issue_type,
        project_id=issue_in.project_id,
        reporter_id=reporter_id,
        assignee_id=issue_in.assignee_id
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
    
    for field in update_data:
        setattr(db_obj, field, update_data[field])
        
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
