from sqlalchemy.orm import Session
from db.models import Project
from schemas import project as project_schema
import uuid

def get_project(db: Session, project_id: uuid.UUID):
    """
    Get a single project by its ID.
    """
    return db.query(Project).filter(Project.id == project_id).first()

def get_projects_by_owner(db: Session, owner_id: uuid.UUID):
    """
    Get all projects owned by a specific user.
    """
    return db.query(Project).filter(Project.owner_id == owner_id).all()

def create_project(db: Session, project_in: project_schema.ProjectCreate, owner_id: uuid.UUID):
    """
    Create a new project.
    """
    db_project = Project(
        name=project_in.name,
        key=project_in.key,
        description=project_in.description,
        owner_id=owner_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: uuid.UUID):
    """
    Delete a project by its ID.
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project:
        db.delete(db_project)
        db.commit()
    return db_project
