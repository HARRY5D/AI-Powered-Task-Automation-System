from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import List

from app.core.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import (
    TaskCreate, TaskUpdate, TaskResponse, 
    DailyPlanResponse, AIAnalysisRequest
)
from app.core.ai_service import AIProductivityAgent

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    db_task = Task(
        title=task.title,
        description=task.description,
        due_date=task.due_date
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/", response_model=List[TaskResponse])
def get_tasks(
    status: str = Query(None),
    priority: str = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all tasks with optional filtering"""
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    
    if priority:
        query = query.filter(Task.priority == priority)
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    
    # Mark as completed if status is changed to COMPLETED
    if "status" in update_data and update_data["status"] == TaskStatus.COMPLETED.value:
        update_data["completed_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted successfully"}


@router.post("/analyze/daily-plan", response_model=DailyPlanResponse)
def generate_daily_plan(db: Session = Depends(get_db)):
    """Generate AI-powered daily plan from pending tasks"""
    
    # Get all pending tasks due today or overdue
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    
    pending_tasks = db.query(Task).filter(
        and_(
            Task.status == TaskStatus.PENDING,
            Task.due_date <= datetime.combine(tomorrow, datetime.max.time())
        )
    ).all()
    
    if not pending_tasks:
        return DailyPlanResponse(
            prioritized_tasks=[],
            today_plan=[],
            insights="No pending tasks for today"
        )
    
    # Prepare task data for AI
    tasks_data = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "due_date": str(t.due_date) if t.due_date else None
        }
        for t in pending_tasks
    ]
    
    # Get AI analysis
    ai_result = AIProductivityAgent.analyze_tasks(tasks_data)
    
    # Update task priorities based on AI analysis
    for priority_task in ai_result.get("prioritized_tasks", []):
        task_id = priority_task.get("task_id")
        category = priority_task.get("category", "neither")
        
        # Map category to priority enum
        priority_map = {
            "urgent_important": TaskPriority.URGENT_IMPORTANT,
            "important_not_urgent": TaskPriority.IMPORTANT_NOT_URGENT,
            "urgent_not_important": TaskPriority.URGENT_NOT_IMPORTANT,
            "neither": TaskPriority.NEITHER
        }
        
        if task_id:
            db_task = db.query(Task).filter(Task.id == task_id).first()
            if db_task:
                db_task.priority = priority_map.get(category, TaskPriority.NEITHER)
                db_task.ai_analysis = priority_task.get("reason", "")
                db.add(db_task)
    
    # Flag procrastination tasks
    for procrastination_task in ai_result.get("procrastination_flags", []):
        # Find task by title match
        db_task = db.query(Task).filter(Task.title.ilike(f"%{procrastination_task}%")).first()
        if db_task:
            db_task.procrastination_flag = True
            db.add(db_task)
    
    db.commit()
    
    return DailyPlanResponse(
        prioritized_tasks=ai_result.get("prioritized_tasks", []),
        today_plan=ai_result.get("today_plan", []),
        insights=ai_result.get("insights", "")
    )


@router.post("/analyze/weekly-report")
def generate_weekly_report(db: Session = Depends(get_db)):
    """Generate weekly productivity report"""
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    total_tasks = db.query(Task).filter(Task.created_at >= week_ago).count()
    completed_tasks = db.query(Task).filter(
        and_(
            Task.status == TaskStatus.COMPLETED,
            Task.completed_at >= week_ago
        )
    ).count()
    pending_tasks = db.query(Task).filter(
        Task.status == TaskStatus.PENDING
    ).count()
    
    report = AIProductivityAgent.generate_weekly_report(completed_tasks, pending_tasks, total_tasks)
    
    return {
        "period": "last_7_days",
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "ai_report": report
    }


@router.post("/{task_id}/complete")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    """Mark task as completed"""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db_task.status = TaskStatus.COMPLETED
    db_task.completed_at = datetime.utcnow()
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/stats/summary")
def get_summary_stats(db: Session = Depends(get_db)):
    """Get task statistics"""
    total = db.query(Task).count()
    completed = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
    pending = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
    in_progress = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
    
    urgent = db.query(Task).filter(Task.priority == TaskPriority.URGENT_IMPORTANT).count()
    procrastination = db.query(Task).filter(Task.procrastination_flag == True).count()
    
    return {
        "total_tasks": total,
        "completed": completed,
        "pending": pending,
        "in_progress": in_progress,
        "completion_rate": (completed / total * 100) if total > 0 else 0,
        "urgent_important": urgent,
        "procrastination_flags": procrastination
    }
