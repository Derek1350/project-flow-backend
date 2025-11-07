from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ...schemas import phase as phase_schema
from ...db.models import ProjectRole, PhaseStatus
from ...api.deps import get_db, require_role, require_phase_role # <-- Import require_phase_role
from ...crud import crud_phase, crud_project

router = APIRouter()

@router.get("/projects/{project_id}/phases", response_model=List[phase_schema.Phase], dependencies=[Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD, ProjectRole.MEMBER]))])
def get_project_phases(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get all phases for a project, ordered.
    Accessible by any project member.
    """
    return crud_phase.get_phases_by_project(db, project_id=project_id)

@router.post("/projects/{project_id}/phases", response_model=phase_schema.Phase, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]))])
def create_new_phase(
    project_id: UUID,
    phase_in: phase_schema.PhaseCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new phase for a project.
    Only accessible by Admins and Project Leads.
    """
    return crud_phase.create_phase(db, project_id=project_id, phase_in=phase_in)

@router.put("/phases/{phase_id}", response_model=phase_schema.Phase, dependencies=[Depends(require_phase_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]))]) # <-- FIXED
def update_phase_details(
    phase_id: UUID,
    phase_in: phase_schema.PhaseUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a phase's details.
    Only accessible by Admins and Project Leads.
    """
    db_phase = crud_phase.get_phase(db, phase_id=phase_id)
    if not db_phase:
        raise HTTPException(status_code=404, detail="Phase not found")
    
    return crud_phase.update_phase(db, db_phase=db_phase, phase_in=phase_in)

@router.put("/projects/{project_id}/phases/reorder", response_model=List[phase_schema.Phase], dependencies=[Depends(require_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]))])
def reorder_phases(
    project_id: UUID,
    order_updates: List[phase_schema.PhaseOrderUpdate],
    db: Session = Depends(get_db),
):
    """
    Updates the order of all phases for a project.
    Only accessible by Admins and Project Leads.
    """
    return crud_phase.update_phases_order(db, project_id=project_id, order_updates=order_updates)
    
@router.delete("/phases/{phase_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_phase_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]))]) # <-- FIXED
def delete_phase(
    phase_id: UUID,
    db: Session = Depends(get_db),
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

@router.post("/phases/{phase_id}/start", response_model=phase_schema.Phase, dependencies=[Depends(require_phase_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]))]) # <-- FIXED
def start_phase(
    phase_id: UUID,
    db: Session = Depends(get_db),
):
    """Marks a phase as IN_PROGRESS."""
    db_phase = crud_phase.get_phase(db, phase_id=phase_id)
    if not db_phase:
        raise HTTPException(status_code=404, detail="Phase not found")
        
    if db_phase.status == PhaseStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot start a phase that is already completed.")

    return crud_phase.start_phase(db, db_phase=db_phase)

@router.post("/phases/{phase_id}/complete", response_model=phase_schema.Phase, dependencies=[Depends(require_phase_role([ProjectRole.ADMIN, ProjectRole.PROJECT_LEAD]))]) # <-- FIXED
def complete_phase(
    phase_id: UUID,
    db: Session = Depends(get_db),
):
    """Marks a phase as COMPLETED."""
    db_phase = crud_phase.get_phase(db, phase_id=phase_id)
    if not db_phase:
        raise HTTPException(status_code=404, detail="Phase not found")
        
    return crud_phase.complete_phase(db, db_phase=db_phase)