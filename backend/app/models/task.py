from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum
from datetime import datetime
import enum
from app.core.database import Base


class TaskPriority(str, enum.Enum):
    """Task priority levels based on Eisenhower Matrix"""
    URGENT_IMPORTANT = "urgent_important"
    IMPORTANT_NOT_URGENT = "important_not_urgent"
    URGENT_NOT_IMPORTANT = "urgent_not_important"
    NEITHER = "neither"


class TaskStatus(str, enum.Enum):
    """Task status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(Text, nullable=True)
    
    # Priority classification
    priority = Column(Enum(TaskPriority), default=TaskPriority.NEITHER, index=True)
    
    # Status tracking
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    
    # Timing
    due_date = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # AI Analysis
    ai_analysis = Column(Text, nullable=True)  # JSON string with AI insights
    procrastination_flag = Column(Boolean, default=False)  # Flagged as procrastination pattern
    
    # Scheduling
    scheduled_for = Column(DateTime, nullable=True)  # When AI suggests to do it
    reminders_sent = Column(Integer, default=0)  # Count of reminders sent
    
    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, priority={self.priority})>"
