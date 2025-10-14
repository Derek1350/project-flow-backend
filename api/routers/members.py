from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from schemas import member as member_schema
from db.models import ProjectMember, ProjectRole
from api.deps import get_db, require_role, get_project_member_from_path
import crud.crud_member as crud_member
import crud.crud_user as crud_user

router = APIRouter()

@router.get(
    "/projects/{project_id}/members",
    response_model=List[member_schema.ProjectMemberRead],
    dependencies=[Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD, ProjectRole.MEMBER]))]
)
def get_project_members_for_project(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all members for a specific project.
    Accessible by any member of the project.
    """
    members = crud_member.get_project_members(db, project_id=project_id)
    return members

@router.post(
    "/projects/{project_id}/members",
    response_model=member_schema.ProjectMemberRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]))]
)
def add_member_to_project(
    project_id: UUID,
    member_in: member_schema.ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_member: ProjectMember = Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]))
):
    """
    Add a new member to a project.
    Only accessible by Admins and Project Leads.
    Project Leads can only add 'Members'.
    """
    # If the current user is a Project Lead, they cannot assign another Project Lead
    if current_member.role == ProjectRole.PROJECT_LEAD and member_in.role == ProjectRole.PROJECT_LEAD:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project Leads can only add new users as Members.")

    user_to_add = crud_user.get_user_by_email(db, email=member_in.email)
    if not user_to_add:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email not found")

    existing_member = crud_member.get_project_member(db, project_id=project_id, user_id=user_to_add.id)
    if existing_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this project")
    
    # If an Admin is adding a new Project Lead, demote the old one
    if member_in.role == ProjectRole.PROJECT_LEAD:
        current_lead = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.role == ProjectRole.PROJECT_LEAD).first()
        if current_lead:
            current_lead.role = ProjectRole.MEMBER
            db.add(current_lead)

    member = crud_member.add_project_member(db, project_id=project_id, user_id=user_to_add.id, role=member_in.role)
    return member


@router.put(
    "/projects/{project_id}/members/{user_id}",
    response_model=member_schema.ProjectMemberRead,
    dependencies=[Depends(require_role([ProjectRole.ADMIN]))] # Only Admins can edit roles
)
def update_project_member_role(
    member_update: member_schema.ProjectMemberUpdate,
    member_to_update: ProjectMember = Depends(get_project_member_from_path),
    db: Session = Depends(get_db)
):
    """
    Update a member's role in a project. Only accessible by Admins.
    Prevents demoting the last Project Lead.
    """
    # Check if we're trying to demote the last project lead
    if member_to_update.role == ProjectRole.PROJECT_LEAD and member_update.role == ProjectRole.MEMBER:
        members = crud_member.get_project_members(db, project_id=member_to_update.project_id)
        project_leads = [m for m in members if m.role == ProjectRole.PROJECT_LEAD]
        if len(project_leads) == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last Project Lead. Assign a new lead first."
            )

    updated_member = crud_member.update_member_role(
        db, 
        project_id=member_to_update.project_id, 
        user_id=member_to_update.user_id, 
        new_role=member_update.role
    )
    return updated_member

@router.delete(
    "/projects/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]))]
)
def remove_member_from_project(
    member_to_remove: ProjectMember = Depends(get_project_member_from_path),
    db: Session = Depends(get_db)
):
    """
    Remove a member from a project.
    Prevents removing the last Project Lead.
    """
    # Prevent removing the last Project Lead from a project
    if member_to_remove.role == ProjectRole.PROJECT_LEAD:
        members = crud_member.get_project_members(db, project_id=member_to_remove.project_id)
        project_leads = [m for m in members if m.role == ProjectRole.PROJECT_LEAD]
        if len(project_leads) == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last Project Lead from a project. Assign a new lead first."
            )
        
    crud_member.remove_project_member(
        db, 
        project_id=member_to_remove.project_id, 
        user_id=member_to_remove.user_id
    )
    return

