from enum import Enum

class IssueStatus(str, Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"

class IssuePriority(str, Enum):
    LOWEST = "Lowest"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    HIGHEST = "Highest"

class IssueType(str, Enum):
    TASK = "Task"
    BUG = "Bug"
    STORY = "Story"
    EPIC = "Epic"

class ProjectRole(str, Enum):
    ADMIN = "Admin"
    PROJECT_LEAD = "Project Lead"
    MEMBER = "Member"

