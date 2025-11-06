import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from ..db.models import Phase
from ..schemas.phase import PhaseCreate, PhaseUpdate, PhaseOrderUpdate

def get_phase(db: Session, phase_id: uuid.UUID) -> Phase | None:
    return db.query(Phase).filter(Phase.id == phase_id).first()

def get_phases_by_project(db: Session, project_id: uuid.UUID) -> List[Phase]:
    return db.query(Phase).filter(Phase.project_id == project_id).order_by(Phase.order).all()

def create_phase(db: Session, project_id: uuid.UUID, phase_in: PhaseCreate) -> Phase:
    # Get current max order for the project
    max_order = db.query(func.max(Phase.order)).filter(Phase.project_id == project_id).scalar() or 0
    
    db_phase = Phase(
        **phase_in.model_dump(),
        project_id=project_id,
        order=max_order + 1
    )
    db.add(db_phase)
    db.commit()
    db.refresh(db_phase)
    return db_phase

def update_phase(db: Session, db_phase: Phase, phase_in: PhaseUpdate) -> Phase:
    update_data = phase_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_phase, field, value)
    
    db.add(db_phase)
    db.commit()
    db.refresh(db_phase)
    return db_phase

def delete_phase(db: Session, phase_id: uuid.UUID) -> Phase | None:
    db_phase = get_phase(db, phase_id=phase_id)
    if db_phase:
        db.delete(db_phase)
        db.commit()
    return db_phase

def update_phases_order(db: Session, project_id: uuid.UUID, order_updates: List[PhaseOrderUpdate]):
    # Update orders in a bulk fashion
    for update in order_updates:
        db.query(Phase).filter(
            Phase.id == update.id,
            Phase.project_id == project_id
        ).update({"order": update.order})
    
    db.commit()
    return get_phases_by_project(db, project_id=project_id)