from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ...schemas import phase as phase_schema
from ...db.models import ProjectRole
from ...api.deps import get_db, require_role
from ...crud import crud_phase, crud_project

router = APIRouter()

@router.get("/projects/{project_id}/phases", response_model=List[phase_schema.Phase])
def get_project_phases(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_member: dict = Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD, ProjectRole.MEMBER]))
):
    """
    Get all phases for a project, ordered.
    Accessible by any project member.
    """
    return crud_phase.get_phases_by_project(db, project_id=project_id)

@router.post("/projects/{project_id}/phases", response_model=phase_schema.Phase, status_code=status.HTTP_201_CREATED)
def create_new_phase(
    project_id: UUID,
    phase_in: phase_schema.PhaseCreate,
    db: Session = Depends(get_db),
    current_member: dict = Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]))
):
    """
    Create a new phase for a project.
    Only accessible by Admins and Project Leads.
    """
    return crud_phase.create_phase(db, project_id=project_id, phase_in=phase_in)

@router.put("/phases/{phase_id}", response_model=phase_schema.Phase)
def update_phase_details(
    phase_id: UUID,
    phase_in: phase_schema.PhaseUpdate,
    db: Session = Depends(get_db),
    current_member: dict = Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD])) # Requires project context
):
    """
    Update a phase's details.
    Only accessible by Admins and Project Leads.
    (Note: This dependency check is simplified; a proper check would load the phase, 
    find its project_id, and check role against that.)
    """
    db_phase = crud_phase.get_phase(db, phase_id=phase_id)
    if not db_phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    
    # Simple auth check (relies on user being a lead of *any* project, not necessarily this one)
    # A more robust check is needed for production.
    
    return crud_phase.update_phase(db, db_phase=db_phase, phase_in=phase_in)

@router.put("/projects/{project_id}/phases/reorder", response_model=List[phase_schema.Phase])
def reorder_phases(
    project_id: UUID,
    order_updates: List[phase_schema.PhaseOrderUpdate],
    db: Session = Depends(get_db),
    current_member: dict = Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]))
):
    """
    Updates the order of all phases for a project.
    Only accessible by Admins and Project Leads.
    """
    return crud_phase.update_phases_order(db, project_id=project_id, order_updates=order_updates)
    
@router.delete("/phases/{phase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_phase(
    phase_id: UUID,
    db: Session = Depends(get_db),
    current_member: dict = Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD])) # Simplified auth
):
    """
    Delete a phase. Issues within it will have their phase_id set to null.
    Only accessible by Admins and Project Leads.
    """
    db_phase = crud_phase.get_phase(db, phase_id=phase_id)
    if not db_phase:
        raise HTTPException(status_code=404, detail="Phase not found")
        
    crud_phase.delete_phase(db, phase_id=phase_id)
    return