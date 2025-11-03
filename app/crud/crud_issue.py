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
        status=issue_in.status.value,
        priority=issue_in.priority.value, # Be consistent for all enums
        issue_type=issue_in.issue_type.value, # Be consistent for all enums
        project_id=issue_in.project_id,
        reporter_id=reporter_id,
        assignee_id=issue_in.assignee_id,
        start_date=issue_in.start_date,  # Add start_date
        due_date=issue_in.due_date        # Add due_date
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
        value = update_data[field]
        # Check if the field is one of our enums and use its value
        if field == 'status' and value is not None:
            value = value.value
        elif field == 'priority' and value is not None:
            value = value.value
        elif field == 'issue_type' and value is not None:
            value = value.value
        
        # This will correctly handle date fields (as date objects) and other fields
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
