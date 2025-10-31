from enum import Enum

class IssueStatus(str, Enum):
    PROPOSED = "PROPOSED"
    TODO = "TO_DO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"

class IssuePriority(str, Enum):
    LOWEST = "LOWEST"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    HIGHEST = "HIGHEST"

class IssueType(str, Enum):
    TASK = "TASK"
    BUG = "BUG"
    STORY = "STORY"
    EPIC = "EPIC"

class ProjectRole(str, Enum):
    ADMIN = "ADMIN"
    PROJECT_LEAD = "PROJECT_LEAD"
    MEMBER = "MEMBER"