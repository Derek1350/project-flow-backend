from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...schemas import issue as issue_schema
from ...schemas.base import IssueStatus, IssueType
from ...api.deps import get_db, get_current_user, require_role, require_issue_role
from ...db.models import User, ProjectRole, ProjectMember
from ...crud import crud_issue, crud_member

router = APIRouter()


def check_admin_assignment(current_user: User, issue_in_assignee_id: UUID | None):
    """Prevents superusers from being assigned to any issue."""
    if current_user.is_superuser and issue_in_assignee_id is not None and issue_in_assignee_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Administrators cannot be assigned to issues."
        )


@router.post("", response_model=issue_schema.Issue, status_code=status.HTTP_201_CREATED)
def create_new_issue(
    issue_in: issue_schema.IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new issue.
    - Members can only propose Tasks or Bugs.
    - Project Leads/Admins can create all types and set status.
    """
    # ENFORCEMENT POINT 1: Check assignment on creation
    check_admin_assignment(current_user, issue_in.assignee_id)
    
    # Check if the user is a member of the project
    member = crud_member.get_project_member(db, project_id=issue_in.project_id, user_id=current_user.id)
    
    # Allow Superusers to create issues, even if they aren't a formal member
    if not current_user.is_superuser and not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this project")

    role = ProjectRole.ADMIN if current_user.is_superuser else member.role

    # Logic for Members
    if role == ProjectRole.MEMBER:
        # Members can only propose Tasks or Bugs
        if issue_in.issue_type in [IssueType.STORY, IssueType.EPIC]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Members can only propose Tasks or Bugs.")
        
        # Force status to PROPOSED and clear assignee
        issue_in.status = IssueStatus.PROPOSED
        issue_in.assignee_id = None
        
    # Logic for Leads/Admins
    elif role in [ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]:
        # If a lead creates an issue and leaves status as default 'PROPOSED',
        # automatically move it to 'TODO'
        if issue_in.status == IssueStatus.PROPOSED:
            issue_in.status = IssueStatus.TODO

    issue = crud_issue.create_issue(db, issue_in=issue_in, reporter_id=current_user.id)
    return issue

@router.get("/project/{project_id}", response_model=List[issue_schema.Issue])
def get_issues_for_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    # This dependency returns a ProjectMember object (or mock admin)
    current_member: ProjectMember = Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD, ProjectRole.MEMBER])),
):
    """
    Retrieve all issues for a given project.
    - Admins/Leads see all issues.
    - Members see all active issues + only their own proposals.
    """
    issues = crud_issue.get_issues_by_project(db, project_id=project_id)
    
    if current_member.role == ProjectRole.MEMBER:
        # Filter list: show all non-proposed issues OR proposed issues they reported
        return [
            i for i in issues 
            if i.status != IssueStatus.PROPOSED or i.reporter_id == current_member.user_id
        ]
    
    # Admins and Project Leads see all issues
    return issues

@router.put("/{issue_id}", response_model=issue_schema.Issue)
def update_existing_issue(
    issue_id: UUID,
    issue_in: issue_schema.IssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), # Keep this for user context
):
    """
    Update an issue.
    Accessible by Admins, Project Leads, or the issue's Assignee.
    """
    issue = crud_issue.get_issue(db, issue_id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # ENFORCEMENT POINT 2: Check assignment on update
    # Check against the proposed new assignee_id
    check_admin_assignment(current_user, issue_in.assignee_id)

    # Check permissions
    member = crud_member.get_project_member(db, project_id=issue.project_id, user_id=current_user.id)
    
    is_admin = current_user.is_superuser
    is_lead = member and member.role == ProjectRole.PROJECT_LEAD
    is_assignee = issue.assignee_id == current_user.id

    if not (is_admin or is_lead or is_assignee):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this issue")
    
    # Prevent a member from changing issue type or assignee
    if not (is_admin or is_lead):
        if issue_in.issue_type is not None or issue_in.assignee_id is not None:
            raise HTTPException(status_code=403, detail="Only Admins or Project Leads can change issue type or assignee")

    updated_issue = crud_issue.update_issue(db, db_obj=issue, obj_in=issue_in)
    return updated_issue

@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_issue(
    issue_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), # Keep this for user context
):
    """
    Delete an issue. Only accessible by Admins or Project Leads.
    """
    issue = crud_issue.get_issue(db, issue_id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Use the require_role dependency to check permissions for the issue's project
    # This is tricky since it's a factory. Let's use our new dependency.
    project_permission_checker = require_issue_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD])
    project_permission_checker(issue_id=issue_id, current_user=current_user, db=db)

    crud_issue.delete_issue(db, issue_id=issue_id)
    return

# --- New Endpoints for Proposal & Assignment Workflows (UNCHANGED) ---

@router.post("/issues/{issue_id}/approve-proposal", response_model=issue_schema.Issue)
def approve_proposal(
    issue_id: UUID,
    db: Session = Depends(get_db),
    # Use the new dependency
    current_member: ProjectMember = Depends(require_issue_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD])),
):
    """Approve a proposed issue, moving it to 'To Do'."""
    issue = crud_issue.get_issue(db, issue_id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if issue.status != IssueStatus.PROPOSED:
        raise HTTPException(status_code=400, detail="Issue is not in proposed state")

    update_data = issue_schema.IssueUpdate(status=IssueStatus.TODO)
    return crud_issue.update_issue(db, db_obj=issue, obj_in=update_data)

@router.post("/issues/{issue_id}/reject-proposal", status_code=status.HTTP_204_NO_CONTENT)
def reject_proposal(
    issue_id: UUID,
    db: Session = Depends(get_db),
    # Use the new dependency
    current_member: ProjectMember = Depends(require_issue_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD])),
):
    """Reject a proposed issue, deleting it."""
    issue = crud_issue.get_issue(db, issue_id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if issue.status != IssueStatus.PROPOSED:
        raise HTTPException(status_code=400, detail="Issue is not in proposed state")
    
    crud_issue.delete_issue(db, issue_id=issue_id)
    return

@router.post("/issues/{issue_id}/request-assignment", response_model=issue_schema.Issue)
def request_assignment(
    issue_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Request to be assigned to an unassigned issue."""
    issue = crud_issue.get_issue(db, issue_id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if issue.assignee_id:
        raise HTTPException(status_code=400, detail="Issue is already assigned")
    if issue.assignee_request_id:
        raise HTTPException(status_code=400, detail="An assignment request is already pending")

    return crud_issue.request_issue(db, issue=issue, user=current_user)

@router.post("/issues/{issue_id}/approve-assignment", response_model=issue_schema.Issue)
def approve_assignment(
    issue_id: UUID,
    db: Session = Depends(get_db),
    # Use the new dependency
    current_member: ProjectMember = Depends(require_issue_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD])),
):
    """Approve a pending assignment request."""
    issue = crud_issue.get_issue(db, issue_id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if not issue.assignee_request_id:
        raise HTTPException(status_code=400, detail="No pending assignment request for this issue")
    
    return crud_issue.approve_request(db, issue=issue)

@router.post("/issues/{issue_id}/reject-assignment", response_model=issue_schema.Issue)
def reject_assignment(
    issue_id: UUID,
    db: Session = Depends(get_db),
    # Use the new dependency
    current_member: ProjectMember = Depends(require_issue_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD])),
):
    """Reject a pending assignment request."""
    issue = crud_issue.get_issue(db, issue_id=issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if not issue.assignee_request_id:
        raise HTTPException(status_code=400, detail="No pending assignment request for this issue")
    
    return crud_issue.reject_request(db, issue=issue)