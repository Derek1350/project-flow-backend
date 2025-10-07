from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas import project as project_schema
from api.deps import get_db, get_current_user
from db.models import User
import crud.crud_project as crud_project

router = APIRouter()

@router.get("", response_model=List[project_schema.Project])
def get_user_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all projects for the current user.
    """
    projects = crud_project.get_projects_by_owner(db, owner_id=current_user.id)
    return projects

@router.post("", response_model=project_schema.Project, status_code=status.HTTP_201_CREATED)
def create_new_project(
    project_in: project_schema.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new project owned by the current user.
    """
    project = crud_project.create_project(db, project_in=project_in, owner_id=current_user.id)
    return project

@router.get("/{project_id}", response_model=project_schema.Project)
def get_single_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a single project by its ID.
    """
    project = crud_project.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
    return project

