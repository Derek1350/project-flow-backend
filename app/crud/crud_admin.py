from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta
from typing import List

from ..crud import crud_project
from ..db.models import Issue, IssueStatus, Issue 
from ..schemas import admin as admin_schema

# Helper function definition for phase progress calculation
def calculate_phase_progress(project):
    """Calculates project progress based on completed phases."""
    if not project.phases:
        # Fallback to issue-based progress if no phases exist
        return project.progress
    
    total_phases = len(project.phases)
    completed_phases = 0

    for phase in project.phases:
        issues_in_phase = [i for i in project.issues if i.phase_id == phase.id]
        if not issues_in_phase:
            continue
            
        total_issues_in_phase = len(issues_in_phase)
        done_issues_in_phase = sum(1 for i in issues_in_phase if i.status == IssueStatus.DONE)
        
        # Consider a phase "completed" if 100% of its issues are done
        if done_issues_in_phase == total_issues_in_phase and total_issues_in_phase > 0:
            completed_phases += 1

    return (completed_phases / total_phases * 100) if total_phases > 0 else 0

def get_dashboard_data(db: Session) -> admin_schema.ExecutiveDashboardResponse:
    """
    Gathers and processes data for the Executive Dashboard.
    """
    all_projects = crud_project.get_all_projects(db)

    # Calculate Phase-based Progress for all projects
    for project in all_projects:
        project.phase_progress = calculate_phase_progress(project) 

    # 1. --- Stats Card Data ---
    total_projects = len(all_projects)
    completed_projects = sum(1 for p in all_projects if p.progress == 100) 

    # NEW: Define status based on progress (using simple thresholds for now)
    on_track_projects = sum(1 for p in all_projects if p.progress >= 75 and p.progress < 100)
    delayed_projects = sum(1 for p in all_projects if p.progress < 75 and p.progress > 0)
    
    # Calculate percentages safely
    def get_percentage(count, total):
        return f"{int((count / total) * 100) if total > 0 else 0}% of total"

    stats_data = [
        admin_schema.StatCard(title="Total Projects", value=str(total_projects), description="All projects"),
        admin_schema.StatCard(title="On Track", value=str(on_track_projects), description=get_percentage(on_track_projects, total_projects)),
        admin_schema.StatCard(title="Delayed", value=str(delayed_projects), description=get_percentage(delayed_projects, total_projects)),
        admin_schema.StatCard(title="Completed", value=str(completed_projects), description=get_percentage(completed_projects, total_projects)),
    ]

    # 2. --- Strategic Themes Progress ---
    themes_data = sorted(all_projects, key=lambda p: p.phase_progress if p.phase_progress is not None else -1, reverse=True)[:4]
    themes_data = [
        admin_schema.ThemeProgress(
            id=str(p.id),
            name=f"{p.name} ({p.key})",
            progress=int(p.phase_progress if p.phase_progress is not None else 0)
        ) for p in themes_data
    ]

    # 3. --- Upcoming Deadlines Data (remains the same) ---
    today = datetime.utcnow().date()
    next_week = today + timedelta(days=7)
    
    upcoming_issues = db.query(Issue).filter(
        Issue.due_date != None,
        Issue.due_date >= today,
        Issue.due_date <= next_week,
        Issue.status != IssueStatus.DONE
    ).order_by(Issue.due_date.asc()).limit(5).all()

    deadlines_data = []
    for issue in upcoming_issues:
        days_left = (issue.due_date - today).days
        priority = admin_schema.DeadlinePriority.LOW
        if days_left <= 2:
            priority = admin_schema.DeadlinePriority.CRITICAL
        elif days_left <= 5:
            priority = admin_schema.DeadlinePriority.MEDIUM
            
        deadlines_data.append(admin_schema.Deadline(
            id=str(issue.id),
            title=issue.title,
            description=f"Due in {days_left} day(s)",
            priority=priority
        ))

    # 4. --- Recent Activity (Pulls real data) ---
    now = datetime.utcnow()
    
    def format_time_ago(dt: datetime):
        diff = now - dt
        seconds = diff.total_seconds()
        if seconds < 60:
            return f"{int(seconds)} seconds ago"
        elif seconds < 3600:
            return f"{int(seconds // 60)} minutes ago"
        elif seconds < 86400:
            return f"{int(seconds // 3600)} hours ago"
        else:
            return f"{int(seconds // 86400)} days ago"

    recent_issues_query = db.query(Issue).options(
        joinedload(Issue.project) 
    ).order_by(Issue.created_at.desc()).limit(5)
    recent_issues = recent_issues_query.all()
    
    activities_data = []
    for issue in recent_issues:
        activities_data.append(admin_schema.Activity(
            id=str(issue.id),
            type=admin_schema.ActivityType.ASSIGNMENT, 
            description=f"New issue '{issue.title}' created in {issue.project.key}",
            time=format_time_ago(issue.created_at)
        ))
    
    if not activities_data:
        activities_data = [admin_schema.Activity(
            id="a0", 
            type=admin_schema.ActivityType.COMPLETION, 
            description="System initialized. Ready for new projects.", 
            time="just now"
        )]
        
    return admin_schema.ExecutiveDashboardResponse(
        stats=stats_data,
        themes=themes_data,
        deadlines=deadlines_data,
        activities=activities_data,
    )