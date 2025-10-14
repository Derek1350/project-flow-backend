from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas import issue as issue_schema
from api.deps import get_db, get_current_user, require_role
from db.models import User, ProjectRole
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
    # Any member of a project should be able to create an issue.
    # We can add a dependency here to check if the user is a member of the project_id in issue_in
    issue = crud_issue.create_issue(db, issue_in=issue_in, reporter_id=current_user.id)
    return issue

@router.get("/project/{project_id}", response_model=List[issue_schema.Issue])
def get_issues_for_project(
    project_id: str,
    db: Session = Depends(get_db),
    # Any member of the project can view the issues
    current_user: User = Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD, ProjectRole.MEMBER])),
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
    current_user: User = Depends(get_current_user), # Keep this for user context
):
    """
    Update an issue. Only accessible by Admins or Project Leads.
    """
    issue = crud_issue.get_issue(db, issue_id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Use the require_role dependency to check permissions for the issue's project
    # We create a temporary checker function. This is a bit advanced, but powerful.
    project_permission_checker = require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD])
    project_permission_checker(project_id=issue.project_id, current_user=current_user, db=db)
    
    updated_issue = crud_issue.update_issue(db, db_obj=issue, obj_in=issue_in)
    return updated_issue

@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_issue(
    issue_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), # Keep this for user context
):
    """
    Delete an issue. Only accessible by Admins or Project Leads.
    """
    issue = crud_issue.get_issue(db, issue_id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Use the require_role dependency similarly to the update endpoint
    project_permission_checker = require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD])
    project_permission_checker(project_id=issue.project_id, current_user=current_user, db=db)

    crud_issue.delete_issue(db, issue_id=issue_id)
    return
