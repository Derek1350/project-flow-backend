from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas import issue as issue_schema
from api.deps import get_db, get_current_user
from db.models import User
import crud.crud_issue as crud_issue

router = APIRouter()

@router.post("", response_model=issue_schema.Issue, status_code=status.HTTP_201_CREATED)
def create_new_issue(
    issue_in: issue_schema.IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new issue. The current user is the reporter.
    """
    issue = crud_issue.create_issue(db, issue_in=issue_in, reporter_id=current_user.id)
    return issue

@router.get("/project/{project_id}", response_model=List[issue_schema.Issue])
def get_issues_for_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all issues for a given project.
    """
    issues = crud_issue.get_issues_by_project(db, project_id=project_id)
    return issues

@router.put("/{issue_id}", response_model=issue_schema.Issue)
def update_existing_issue(
    issue_id: str,
    issue_in: issue_schema.IssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an issue.
    """
    issue = crud_issue.get_issue(db, issue_id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    # You might want to add an authorization check here to ensure the user can update this issue
    updated_issue = crud_issue.update_issue(db, db_obj=issue, obj_in=issue_in)
    return updated_issue

@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_issue(
    issue_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an issue.
    """
    issue = crud_issue.get_issue(db, issue_id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    # You might want to add an authorization check here
    crud_issue.delete_issue(db, issue_id=issue_id)
    return

