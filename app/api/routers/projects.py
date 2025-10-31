from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...schemas import project as project_schema
from ...api.deps import get_db, get_current_user, require_role, get_current_superuser
from ...db.models import User, ProjectRole
from ...crud import crud_project

router = APIRouter()


@router.get("", response_model=List[project_schema.ProjectWithDetails])
def get_user_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all projects the current user is a member of.
    Admins see all projects.
    """
    if current_user.is_superuser:
        projects = crud_project.get_all_projects(db)
    else:
        projects = crud_project.get_projects_for_user(db, user_id=current_user.id)
    return projects


@router.post("", response_model=project_schema.Project, status_code=status.HTTP_201_CREATED)
def create_new_project(
    project_in: project_schema.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """
    Create a new project. The creator becomes the Project Lead.
    Only accessible by superusers (admins).
    """
    project = crud_project.create_project(db, project_in=project_in, admin_user_id=current_user.id)
    return project


@router.get("/{project_id}", response_model=project_schema.Project, dependencies=[Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD, ProjectRole.MEMBER]))])
def get_single_project(
    project_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve a single project by its ID. User must be a member.
    """
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_superuser)])
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete a project. Only accessible by a Super Admin.
    """
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404, detail="Project not found")
    
    crud_project.delete_project(db, project_id=project_id)
    return