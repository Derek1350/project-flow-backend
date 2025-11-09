from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from ..db.models import Project, ProjectMember, ProjectRole, IssueStatus, User, Issue, Phase
from ..schemas import project as project_schema
from ..schemas import phase as phase_schema
from typing import List
from . import crud_user

def calculate_phase_progress(phase: Phase, all_project_issues: List[Issue]) -> float:
    """
    Calculates phase progress based on its associated issues.
    (Done Issues / Total Issues * 100.0)
    """
    issues_in_phase = [i for i in all_project_issues if i.phase_id == phase.id]
    
    total_issues = len(issues_in_phase)
    if total_issues == 0:
        # If no issues, the phase is considered 100% complete only if manually marked complete
        return 100.0 if phase.status == "COMPLETED" else 0.0

    done_issues = sum(1 for i in issues_in_phase if i.status == IssueStatus.DONE)
    return (done_issues / total_issues * 100.0)

def calculate_project_progress_by_phases(project_phases: List[Phase], all_project_issues: List[Issue]) -> float:
    """
    Calculates overall project progress.
    (Completed Phases / Total Phases * 100.0)
    A phase is counted as Completed if its calculated progress is 100% (rounded).
    """
    if not project_phases:
        # Fallback to issue-based progress for projects without phases
        total_active_issues = sum(1 for i in all_project_issues if i.status != IssueStatus.PROPOSED)
        done_issues = sum(1 for i in all_project_issues if i.status == IssueStatus.DONE)
        return (done_issues / total_active_issues * 100.0) if total_active_issues > 0 else 0.0

    total_phases = len(project_phases)
    completed_phases_count = 0
    
    for phase in project_phases:
        # Calculate the phase's progress based on its issues
        phase_progress = calculate_phase_progress(phase, all_project_issues)
        
        # If phase progress is 100% (or more due to float math/rounding), count it as completed
        if round(phase_progress) >= 100.0:
            completed_phases_count += 1
            
    # Project Progress is based on the count of Completed Phases / Total Phases
    return (completed_phases_count / total_phases * 100.0) if total_phases > 0 else 0.0


def _build_project_details(project: Project) -> project_schema.ProjectWithDetails:
    issue_summary = {
        "total": sum(1 for i in project.issues if i.status != IssueStatus.PROPOSED),
        "todo": sum(1 for i in project.issues if i.status == IssueStatus.TO_DO),
        "in_progress": sum(1 for i in project.issues if i.status == IssueStatus.IN_PROGRESS),
        "in_review": sum(1 for i in project.issues if i.status == IssueStatus.IN_REVIEW),
        "done": sum(1 for i in project.issues if i.status == IssueStatus.DONE),
    }

    project_lead_member = next((m for m in project.memberships if m.role == ProjectRole.PROJECT_LEAD), None)
    project_lead = project_lead_member.user if project_lead_member else None
    
    # 1. Calculate overall project progress (User Request 1 & 3)
    progress = calculate_project_progress_by_phases(project.phases, project.issues)

    # 2. Build phases list with individual progress (User Request 3)
    phases_with_progress: List[phase_schema.Phase] = []
    for phase in project.phases:
        phase_progress_value = calculate_phase_progress(phase, project.issues)
        
        # Manually create the Phase schema object to include the calculated progress
        phases_with_progress.append(
            phase_schema.Phase(
                id=phase.id,
                name=phase.name,
                start_date=phase.start_date,
                end_date=phase.end_date,
                order=phase.order,
                project_id=phase.project_id,
                status=phase.status,
                progress=phase_progress_value # <-- Set calculated progress
            )
        )

    # The progress field in ProjectWithDetails now represents the phase-based completion
    return project_schema.ProjectWithDetails(
        id=project.id,
        name=project.name,
        key=project.key,
        description=project.description,
        created_at=project.created_at,
        issue_summary=issue_summary,
        project_lead=project_lead,
        progress=progress, # <-- Phase-based Project Progress
        members=project.memberships,
        issues=project.issues,
        phases=phases_with_progress, # <-- Phases now have progress
        phase_progress=progress)

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
            joinedload(Project.issues).joinedload(Issue.assignee),
            joinedload(Project.issues).joinedload(Issue.reporter),
            joinedload(Project.issues).joinedload(Issue.requester),
            joinedload(Project.phases) # <-- 3. EAGER LOAD PHASES
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
            joinedload(Project.issues).joinedload(Issue.assignee),
            joinedload(Project.issues).joinedload(Issue.reporter),
            joinedload(Project.issues).joinedload(Issue.requester),
            joinedload(Project.phases) # <-- 4. EAGER LOAD PHASES
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