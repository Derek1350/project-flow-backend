from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from db.models import Project, ProjectMember, ProjectRole, IssueStatus, User
from schemas import project as project_schema
from typing import List
from . import crud_user

# Helper function to build project details
def _build_project_details(project: Project) -> project_schema.ProjectWithDetails:
    issue_summary = {
        "total": len(project.issues),
        "todo": sum(1 for i in project.issues if i.status == IssueStatus.TODO),
        "in_progress": sum(1 for i in project.issues if i.status == IssueStatus.IN_PROGRESS),
        "in_review": sum(1 for i in project.issues if i.status == IssueStatus.IN_REVIEW),
        "done": sum(1 for i in project.issues if i.status == IssueStatus.DONE),
    }

    project_lead_member = next((m for m in project.memberships if m.role == ProjectRole.PROJECT_LEAD), None)
    project_lead = project_lead_member.user if project_lead_member else None

    # Calculate progress
    progress = (issue_summary['done'] / issue_summary['total'] * 100) if issue_summary['total'] > 0 else 0


    return project_schema.ProjectWithDetails(
        **project.__dict__,
        issue_summary=issue_summary,
        project_lead=project_lead,
        progress=progress,
    )

def get_project(db: Session, project_id: str):
    """
    Get a single project by its ID.
    """
    return db.query(Project).filter(Project.id == project_id).first()

def get_projects_for_user(db: Session, user_id: str) -> List[project_schema.ProjectWithDetails]:
    """
    Get all projects a user is a member of.
    """
    projects = (
        db.query(Project)
        .options(
            joinedload(Project.memberships).joinedload(ProjectMember.user),
            joinedload(Project.issues)
        )
        .join(ProjectMember)
        .filter(ProjectMember.user_id == user_id)
        .all()
    )
    return [_build_project_details(p) for p in projects]

def get_all_projects(db: Session) -> List[project_schema.ProjectWithDetails]:
    """
    Get all projects in the database. Intended for superusers.
    """
    projects = (
        db.query(Project)
        .options(
            joinedload(Project.memberships).joinedload(ProjectMember.user),
            joinedload(Project.issues)
        )
        .all()
    )
    return [_build_project_details(p) for p in projects]

def create_project(db: Session, project_in: project_schema.ProjectCreate, admin_user_id: str) -> Project:
    """
    Create a new project, assign a project lead, and add members.
    """
    # Create the project itself
    db_project = Project(
        name=project_in.name,
        key=project_in.key,
        description=project_in.description,
    )
    db.add(db_project)
    db.flush()  # Flush to get the db_project.id for the member entries

    # Determine and assign the Project Lead
    project_lead_id = None
    if project_in.project_lead_email:
        project_lead_user = crud_user.get_user_by_email(db, email=project_in.project_lead_email)
        if not project_lead_user:
            raise HTTPException(status_code=404, detail=f"Project lead with email {project_in.project_lead_email} not found.")
        project_lead_id = project_lead_user.id
        db.add(ProjectMember(project_id=db_project.id, user_id=project_lead_id, role=ProjectRole.PROJECT_LEAD))
    else:
        # Default to the creating admin if no lead is specified
        project_lead_id = admin_user_id
        db.add(ProjectMember(project_id=db_project.id, user_id=admin_user_id, role=ProjectRole.PROJECT_LEAD))

    # Add other members
    if project_in.members:
        for member_email in set(project_in.members): # Use set to avoid duplicate entries
            member_user = crud_user.get_user_by_email(db, email=member_email)
            if member_user:
                # Add as a member only if they are not already the project lead
                if member_user.id != project_lead_id:
                    db.add(ProjectMember(project_id=db_project.id, user_id=member_user.id, role=ProjectRole.MEMBER))
            # Note: We could raise an error here if a member email is not found,
            # but for now, we'll just skip non-existent users silently.
    
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: str):
    """
    Delete a project by its ID.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        db.delete(project)
        db.commit()
    return project

