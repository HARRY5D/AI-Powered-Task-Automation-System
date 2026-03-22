from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class TaskPrioritySchema(str, Enum):
    URGENT_IMPORTANT = "urgent_important"
    IMPORTANT_NOT_URGENT = "important_not_urgent"
    URGENT_NOT_IMPORTANT = "urgent_not_important"
    NEITHER = "neither"


class TaskStatusSchema(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskCreate(BaseModel):
    """Schema for creating a new task"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[TaskStatusSchema] = None


class TaskResponse(BaseModel):
    """Schema for task response"""
    id: int
    title: str
    description: Optional[str]
    priority: TaskPrioritySchema
    status: TaskStatusSchema
    due_date: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]
    scheduled_for: Optional[datetime]
    procrastination_flag: bool
    ai_analysis: Optional[str]

    class Config:
        from_attributes = True


class DailyPlanResponse(BaseModel):
    """Schema for daily plan response"""
    prioritized_tasks: list[dict]
    today_plan: list[str]
    insights: str


class AIAnalysisRequest(BaseModel):
    """Schema for triggering AI analysis"""
    task_ids: Optional[list[int]] = None  # If None, analyze all pending tasks
