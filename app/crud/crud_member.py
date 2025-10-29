from sqlalchemy.orm import Session
from uuid import UUID
from ..db.models import ProjectMember, ProjectRole


def get_project_member(db: Session, project_id: UUID, user_id: UUID) -> ProjectMember | None:
    return db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id).first()

def get_project_members(db: Session, project_id: UUID) -> list[ProjectMember]:
    return db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()

def add_project_member(db: Session, project_id: UUID, user_id: UUID, role: ProjectRole) -> ProjectMember:
    """
    Adds a user to a project by their ID.
    Assumes the user already exists.
    """
    db_member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=role,
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

def remove_project_member(db: Session, project_id: UUID, user_id: UUID) -> ProjectMember | None:
    db_member = get_project_member(db, project_id=project_id, user_id=user_id)
    if db_member:
        db.delete(db_member)
        db.commit()
    return db_member

def update_member_role(db: Session, project_id: UUID, user_id: UUID, new_role: ProjectRole) -> ProjectMember | None:
    """
    Updates a member's role. If the new role is Project Lead, it automatically
    demotes the existing Project Lead to a Member to enforce a single Project Lead per project.
    """
    db_member = get_project_member(db, project_id=project_id, user_id=user_id)
    if db_member:
        # Enforce a single Project Lead per project
        if new_role == ProjectRole.PROJECT_LEAD:
            current_lead = (
                db.query(ProjectMember)
                .filter(
                    ProjectMember.project_id == project_id,
                    ProjectMember.role == ProjectRole.PROJECT_LEAD,
                )
                .first()
            )
            if current_lead and current_lead.user_id != user_id:
                current_lead.role = ProjectRole.MEMBER
                db.add(current_lead)

        db_member.role = new_role
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
    return db_member

