from pydantic import BaseModel
from typing import List
from enum import Enum
from datetime import date

# Stat Card
class StatCard(BaseModel):
    title: str
    value: str
    description: str

# Strategic Theme Progress
class ThemeProgress(BaseModel):
    id: str
    name: str
    progress: int

# Upcoming Deadline
class DeadlinePriority(str, Enum):
    CRITICAL = "Critical"
    MEDIUM = "Medium"
    LOW = "Low"

class Deadline(BaseModel):
    id: str
    title: str
    description: str
    priority: DeadlinePriority

# Recent Activity
class ActivityType(str, Enum):
    COMPLETION = "completion"
    ASSIGNMENT = "assignment"
    DELAY = "delay"

class Activity(BaseModel):
    id: str
    type: ActivityType
    description: str
    time: str

# Main Dashboard Response Model
class ExecutiveDashboardResponse(BaseModel):
    stats: List[StatCard]
    themes: List[ThemeProgress]
    deadlines: List[Deadline]
    activities: List[Activity]