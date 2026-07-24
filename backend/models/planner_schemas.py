# backend/models/planner_schemas.py
"""
Study Planner & Scheduler Data Models
Implements task generation, study planning, and scheduling schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from datetime import datetime, date, time
from bson import ObjectId
from .user_schemas import PyObjectId

# ============================================================================
# CORE ENTITIES: Study Tasks, Plans, Goals, Sessions
# ============================================================================
class MoodStrategyResponse(BaseModel):
    emotion: str
    recommendation: str
    suggested_task_types: List[str]
    break_reminder: str
    adjustments: List[str]
    
class StudyTask(BaseModel):
    """Individual learning/revision/practice task"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    plan_id: PyObjectId = Field(..., description="Parent study plan ID")
    subject: str = Field(..., description="Subject name (e.g., 'DSA', 'Physics')")
    topic: str = Field(..., description="Topic name (e.g., 'Sorting Algorithms')")
    task_type: Literal["learn", "revise", "practice"] = Field(
        ..., description="Task type based on quiz performance"
    )
    difficulty: Literal["easy", "medium", "hard"] = Field(..., description="Task difficulty")
    estimated_time_mins: int = Field(..., ge=15, le=300, description="Estimated duration in minutes")
    quiz_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Last quiz score for this topic")
    priority_score: float = Field(..., ge=0.0, le=1.0, description="Computed priority (0=low, 1=urgent)")
    deadline: date = Field(..., description="Target completion date")
    status: Literal["pending", "scheduled", "completed", "missed", "skipped"] = Field(
        default="pending", description="Task status"
    )
    scheduled_date: Optional[date] = Field(None, description="Date task is scheduled for")
    scheduled_time_start: Optional[time] = Field(None, description="Scheduled start time")
    scheduled_time_end: Optional[time] = Field(None, description="Scheduled end time")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    actual_duration_mins: Optional[int] = Field(None, description="Actual time spent")
    notes: Optional[str] = Field(None, description="User or system notes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str, time: str, datetime: str}


class StudyGoal(BaseModel):
    """Explicit or implicit learning goal for a subject"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User ID")
    subject: str = Field(..., description="Subject name")
    goal_type: Literal["performance", "completion", "weakness_recovery"] = Field(
        ..., description="Type of goal"
    )
    target_score: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Target score for performance goals"
    )
    current_score: float = Field(default=0.0, ge=0.0, le=100.0)
    deadline: date = Field(..., description="Goal deadline")
    description: str = Field(..., description="Goal description")
    auto_generated: bool = Field(default=True, description="True if auto-generated from weak topics")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str, datetime: str}


class StudyPlan(BaseModel):
    """Long-term study roadmap spanning multiple days/weeks"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User ID")
    plan_name: str = Field(..., description="Human-readable plan name")
    subjects: List[str] = Field(..., description="List of subjects covered")
    start_date: date = Field(..., description="Plan start date")
    end_date: date = Field(..., description="Plan end date (exam/deadline)")
    mode: Literal["unified", "per_subject"] = Field(
        default="unified", description="Plan mode: unified (all subjects) or per_subject"
    )
    status: Literal["active", "paused", "completed", "archived"] = Field(
        default="active", description="Plan status"
    )
    tasks: List[PyObjectId] = Field(default_factory=list, description="List of task IDs in plan")
    
    # Planning strategy
    total_available_hours: float = Field(..., ge=1, le=1000, description="Total hours to allocate")
    study_pace: Literal["slow", "moderate", "fast"] = Field(
        ..., description="User's preferred study pace"
    )
    
    # Analytics
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    scheduled_sessions: int = Field(default=0, description="Number of sessions scheduled")
    completed_sessions: int = Field(default=0, description="Number of sessions completed")
    missed_sessions: int = Field(default=0, description="Number of sessions missed")
    productivity_score: float = Field(default=0.0, description="Productivity metric (0-1)")
    
    # Control flags
    auto_reschedule_enabled: bool = Field(default=True)
    aggressive_adaptation: bool = Field(default=False, description="Auto-pull future tasks forward")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_adapted_at: Optional[datetime] = Field(None, description="Last adaptive update")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str, datetime: str}


class TimeBlock(BaseModel):
    """Individual study unit with optional break"""
    task_id: PyObjectId = Field(..., description="Associated task ID")
    plan_id: Optional[PyObjectId] = Field(None, description="Plan this task belongs to")
    subject: str = Field(default="", description="Subject name")
    topic: str = Field(..., description="Topic name")
    task_type: Literal["learn", "revise", "practice"] = Field(...)
    difficulty: Literal["easy", "medium", "hard"] = Field(...)
    start_time: time = Field(..., description="Block start time")
    end_time: time = Field(..., description="Block end time")
    duration_mins: int = Field(..., description="Duration in minutes")
    mood_adjustment: Optional[str] = Field(None, description="Mood-based adjustment applied")
    completed: bool = Field(default=False)
    completion_timestamp: Optional[datetime] = Field(None)
    notes: Optional[str] = Field(None)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, time: str, datetime: str}


class StudySession(BaseModel):
    """Daily scheduled session with time-blocked tasks"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    plan_id: Optional[PyObjectId] = Field(None, description="Parent plan ID (None for aggregated sessions)")
    user_id: PyObjectId = Field(..., description="User ID")
    session_date: date = Field(..., description="Session date")
    
    # Aggregation tracking
    aggregated_plan_ids: Optional[List[PyObjectId]] = Field(
        None, description="IDs of plans that were aggregated into this session"
    )

    # Schedule
    start_time: time = Field(..., description="Session start time")
    end_time: time = Field(..., description="Session end time")
    time_blocks: List[TimeBlock] = Field(default_factory=list, description="Scheduled tasks")
    
    # Execution
    mood_at_start: Optional[str] = Field(None, description="Detected emotion at start")
    mood_at_end: Optional[str] = Field(None, description="Detected emotion at end")
    mood_adjustments_applied: List[str] = Field(
        default_factory=list, description="Applied mood-based adjustments"
    )
    
    # Completion metrics
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    completed_blocks: int = Field(default=0, description="Number of blocks completed")
    total_blocks: int = Field(default=0, description="Total blocks scheduled")
    actual_duration_mins: Optional[int] = Field(None)
    interrupted: bool = Field(default=False, description="Session was interrupted")
    
    # Feedback
    status: Literal["scheduled", "in_progress", "completed", "missed", "paused"] = Field(
        default="scheduled"
    )
    notes: Optional[str] = Field(None, description="Session notes")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str, time: str, datetime: str}


class DailyRoadmapEntry(BaseModel):
    """Planner output: High-level day allocation"""
    day_number: int = Field(..., description="Day in plan (1-indexed)")
    calendar_date: date = Field(...)
    allocated_subjects: List[str] = Field(..., description="Subjects to focus on")
    focus_topics: List[str] = Field(..., description="Specific topics")
    session_type: Literal["learning", "revision", "practice", "mixed", "buffer"] = Field(...)
    planned_hours: float = Field(..., description="Hours allocated")
    notes: Optional[str] = Field(None)


class PlanRoadmap(BaseModel):
    """High-level study roadmap from planner"""
    plan_id: str = Field(...)
    roadmap: List[DailyRoadmapEntry] = Field(...)
    total_days: int = Field(...)
    summary: str = Field(..., description="Human-readable summary")


# ============================================================================
# ANALYTICS & REPORTING
# ============================================================================

class WeeklySummary(BaseModel):
    """Weekly analytics snapshot"""
    week_number: int = Field(...)
    start_date: date = Field(...)
    end_date: date = Field(...)
    sessions_scheduled: int = Field(default=0)
    sessions_completed: int = Field(default=0)
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_mood: Optional[str] = Field(None, description="Most common mood this week")
    productivity_score: float = Field(default=0.0)
    total_hours_planned: float = Field(default=0.0)
    total_hours_actual: float = Field(default=0.0)
    tasks_completed: int = Field(default=0)
    tasks_missed: int = Field(default=0)
    notes: Optional[str] = Field(None)


class StudyPlanAnalytics(BaseModel):
    """Comprehensive analytics for a study plan"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    plan_id: PyObjectId = Field(...)
    user_id: PyObjectId = Field(...)
    
    # Overall metrics
    overall_completion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_productivity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Subject-wise progress
    subject_completion: Dict[str, float] = Field(default_factory=dict, description="Per-subject completion %")
    subject_productivity: Dict[str, float] = Field(default_factory=dict, description="Per-subject productivity")
    
    # Session analytics
    total_sessions_scheduled: int = Field(default=0)
    total_sessions_completed: int = Field(default=0)
    total_sessions_missed: int = Field(default=0)
    avg_session_duration_mins: float = Field(default=0.0)
    
    # Mood trends
    mood_distribution: Dict[str, int] = Field(default_factory=dict, description="Count of each emotion")
    mood_trend: str = Field(default="stable", description="positive, stable, declining")
    
    # Weekly breakdown
    weekly_summaries: List[WeeklySummary] = Field(default_factory=list)
    
    # Weak vs Strong topics
    improved_topics: List[str] = Field(default_factory=list)
    still_weak_topics: List[str] = Field(default_factory=list)
    mastered_topics: List[str] = Field(default_factory=list)
    
    # Adaptive adjustments made
    total_reschedules: int = Field(default=0)
    recovery_days_inserted: int = Field(default=0)
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    computed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str, datetime: str}


# ============================================================================
# REQUEST/RESPONSE DTOS FOR API ENDPOINTS
# ============================================================================

class GenerateStudyPlanRequest(BaseModel):
    """Request to generate a new study plan"""
    subjects: List[str] = Field(..., min_length=1, description="List of subjects to plan for")
    deadline: date = Field(..., description="Exam/deadline date")
    mode: Literal["unified", "per_subject"] = Field(
        default="unified", description="Plan mode"
    )
    total_study_hours_per_week: float = Field(
        default=20.0, ge=5, le=100, description="Available study hours per week"
    )
    plan_name: Optional[str] = Field(None, description="Custom plan name")


class StudyTaskResponse(BaseModel):
    """API response for a study task"""
    task_id: str
    subject: str
    topic: str
    task_type: str
    difficulty: str
    estimated_time_mins: int
    quiz_score: Optional[float]
    priority_score: float
    deadline: str
    status: str
    scheduled_date: Optional[str]
    scheduled_time_start: Optional[str]
    scheduled_time_end: Optional[str]
    
    @classmethod
    def from_db_model(cls, task: StudyTask):
        return cls(
            task_id=str(task.id),
            subject=task.subject,
            topic=task.topic,
            task_type=task.task_type,
            difficulty=task.difficulty,
            estimated_time_mins=task.estimated_time_mins,
            quiz_score=task.quiz_score,
            priority_score=task.priority_score,
            deadline=str(task.deadline),
            status=task.status,
            scheduled_date=str(task.scheduled_date) if task.scheduled_date else None,
            scheduled_time_start=str(task.scheduled_time_start) if task.scheduled_time_start else None,
            scheduled_time_end=str(task.scheduled_time_end) if task.scheduled_time_end else None,
        )


class TimeBlockResponse(BaseModel):
    """API response for time block"""
    block_id: str          # equals task_id — used by Flutter as a stable block key
    task_id: str
    plan_id: Optional[str] = None
    subject: str
    topic: str
    task_type: str
    difficulty: str
    start_time: str
    end_time: str
    duration_mins: int
    completed: bool


class StudySessionResponse(BaseModel):
    """API response for a study session"""
    session_id: str
    plan_id: Optional[str] = None
    session_date: str
    start_time: str
    end_time: str
    time_blocks: List[TimeBlockResponse]
    mood_at_start: Optional[str]
    mood_at_end: Optional[str]
    mood_adjustments_applied: List[str]
    completed_blocks: int
    total_blocks: int
    status: str
    notes: Optional[str]
    
    @classmethod
    def from_db_model(cls, session: StudySession):
        return cls(
            session_id=str(session.id),
            plan_id=str(session.plan_id) if session.plan_id else None,
            session_date=str(session.session_date),
            start_time=str(session.start_time),
            end_time=str(session.end_time),
            time_blocks=[
                TimeBlockResponse(
                    block_id=str(tb.task_id),  # stable key for Flutter
                    task_id=str(tb.task_id),
                    plan_id=str(tb.plan_id) if tb.plan_id else None,
                    subject=tb.subject,
                    topic=tb.topic,
                    task_type=tb.task_type,
                    difficulty=tb.difficulty,
                    start_time=str(tb.start_time),
                    end_time=str(tb.end_time),
                    duration_mins=tb.duration_mins,
                    completed=tb.completed,
                )
                for tb in session.time_blocks
            ],
            mood_at_start=session.mood_at_start,
            mood_at_end=session.mood_at_end,
            mood_adjustments_applied=session.mood_adjustments_applied,
            completed_blocks=session.completed_blocks,
            total_blocks=session.total_blocks,
            status=session.status,
            notes=session.notes,
        )


class StudyPlanResponse(BaseModel):
    """API response for a study plan"""
    id: str = Field(..., alias="_id", description="MongoDB plan ID - use this in subsequent API calls")
    plan_name: str
    subjects: List[str]
    start_date: str
    end_date: str
    mode: str
    status: str
    total_available_hours: float
    study_pace: str
    completion_rate: float
    scheduled_sessions: int
    completed_sessions: int
    missed_sessions: int
    productivity_score: float
    auto_reschedule_enabled: bool
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "description": "Use the '_id' field value in all subsequent API calls like GET /plans/{_id}"
        }
    
    @classmethod
    def from_db_model(cls, plan: StudyPlan):
        plan_id_str = str(plan.id)
        return cls(
            _id=plan_id_str,
            plan_name=plan.plan_name,
            subjects=plan.subjects,
            start_date=str(plan.start_date),
            end_date=str(plan.end_date),
            mode=plan.mode,
            status=plan.status,
            total_available_hours=plan.total_available_hours,
            study_pace=plan.study_pace,
            completion_rate=plan.completion_rate,
            scheduled_sessions=plan.scheduled_sessions,
            completed_sessions=plan.completed_sessions,
            missed_sessions=plan.missed_sessions,
            productivity_score=plan.productivity_score,
            auto_reschedule_enabled=plan.auto_reschedule_enabled,
        )


class SessionCompletionRequest(BaseModel):
    """Request to mark session as completed"""
    completed_task_ids: List[str] = Field(..., description="List of completed task IDs")
    user_mood_end: Optional[str] = Field(None, description="User's mood at end of session")
    interrupted: bool = Field(default=False, description="Whether session was interrupted")
    notes: Optional[str] = Field(None)


class SessionCompletionResponse(BaseModel):
    """Response after session completion"""
    success: bool
    message: str
    session_id: str
    completed_blocks: int
    total_blocks: int
    next_session_date: Optional[str] = None
    suggested_actions: List[str] = Field(default_factory=list)


class RescheduleRequest(BaseModel):
    """Request to manually reschedule a plan"""
    reason: str = Field(..., description="Reason for reschedule")
    new_deadline: Optional[date] = Field(None, description="New end date")
    task_adjustments: Optional[Dict[str, str]] = Field(
        None, description="Task ID -> new status mapping"
    )


# ============================================================================
# DAILY SCHEDULE & PROGRESS ANALYTICS
# ============================================================================

class DailySchedule(BaseModel):
    """Daily study schedule with completed tasks and progress"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User ID")
    schedule_date: date = Field(..., description="Date of this schedule")
    
    # Sessions for this day
    session_id: Optional[PyObjectId] = Field(None, description="Associated study session ID")
    aggregated_plan_ids: Optional[List[PyObjectId]] = Field(None, description="Plans included in this schedule")
    
    # Tasks and completion
    total_tasks: int = Field(default=0, description="Total tasks scheduled for this day")
    completed_tasks: int = Field(default=0, description="Number of completed tasks")
    skipped_tasks: int = Field(default=0, description="Number of skipped tasks")
    
    # Time tracking
    planned_duration_mins: int = Field(default=0, description="Total planned study time")
    actual_duration_mins: int = Field(default=0, description="Actual time spent studying")
    
    # Mood and performance
    mood_at_start: Optional[str] = Field(None, description="User's mood at start")
    mood_at_end: Optional[str] = Field(None, description="User's mood at end")
    
    # Productivity metrics
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Tasks completed / total tasks")
    productivity_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Daily productivity (0-1)")
    focus_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Focus quality (0-1)")
    
    # Summary
    status: Literal["scheduled", "in_progress", "completed", "incomplete"] = Field(default="scheduled")
    notes: Optional[str] = Field(None, description="Daily notes/summary")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str, datetime: str}


class DailyProgressAnalytics(BaseModel):
    """Aggregated daily progress analytics for visualization"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User ID")
    analytics_date: date = Field(..., description="Date of analysis")
    
    # Daily metrics summary
    daily_completion_rate: float = Field(default=0.0, description="% tasks completed")
    daily_productivity_score: float = Field(default=0.0, description="Daily productivity score")
    daily_focus_score: float = Field(default=0.0, description="Daily focus quality")
    
    # Aggregated data
    total_study_time_mins: int = Field(default=0, description="Total study minutes this day")
    total_tasks_completed: int = Field(default=0)
    total_tasks_attempted: int = Field(default=0)
    
    # Subject-wise breakdown
    subject_performance: Dict[str, Dict] = Field(
        default_factory=dict,
        description="Per-subject: {subject: {completed_tasks, total_tasks, score}}"
    )
    
    # Mood data
    mood_progression: List[str] = Field(default_factory=list, description="Mood changes throughout day")
    dominant_mood: Optional[str] = Field(None, description="Most frequent mood")
    
    # Comparison
    compared_to_average: float = Field(default=0.0, description="+/- vs user's average")
    streak_count: int = Field(default=0, description="Consecutive days completed at target")
    
    # Notes
    summary: Optional[str] = Field(None, description="AI-generated daily summary")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str, datetime: str}


# ============================================================================
# API RESPONSE MODELS FOR DAILY ANALYTICS
# ============================================================================

class DailyScheduleResponse(BaseModel):
    """API response for daily schedule"""
    schedule_id: str
    schedule_date: str
    total_tasks: int
    completed_tasks: int
    skipped_tasks: int
    planned_duration_mins: int
    actual_duration_mins: int
    completion_rate: float
    productivity_score: float
    focus_score: float
    mood_at_start: Optional[str]
    mood_at_end: Optional[str]
    status: str
    notes: Optional[str]
    
    @classmethod
    def from_db_model(cls, schedule: DailySchedule):
        return cls(
            schedule_id=str(schedule.id),
            schedule_date=str(schedule.schedule_date),
            total_tasks=schedule.total_tasks,
            completed_tasks=schedule.completed_tasks,
            skipped_tasks=schedule.skipped_tasks,
            planned_duration_mins=schedule.planned_duration_mins,
            actual_duration_mins=schedule.actual_duration_mins,
            completion_rate=schedule.completion_rate,
            productivity_score=schedule.productivity_score,
            focus_score=schedule.focus_score,
            mood_at_start=schedule.mood_at_start,
            mood_at_end=schedule.mood_at_end,
            status=schedule.status,
            notes=schedule.notes,
        )


class DailyProgressAnalyticsResponse(BaseModel):
    """API response for daily progress analytics"""
    analytics_date: str
    completion_rate: float
    productivity_score: float
    focus_score: float
    total_study_time_mins: int
    total_tasks_completed: int
    total_tasks_attempted: int
    subject_performance: Dict[str, Dict]
    dominant_mood: Optional[str]
    compared_to_average: float
    streak_count: int
    summary: Optional[str]
    
    @classmethod
    def from_db_model(cls, analytics: DailyProgressAnalytics):
        return cls(
            analytics_date=str(analytics.analytics_date),
            completion_rate=analytics.daily_completion_rate,
            productivity_score=analytics.daily_productivity_score,
            focus_score=analytics.daily_focus_score,
            total_study_time_mins=analytics.total_study_time_mins,
            total_tasks_completed=analytics.total_tasks_completed,
            total_tasks_attempted=analytics.total_tasks_attempted,
            subject_performance=analytics.subject_performance,
            dominant_mood=analytics.dominant_mood,
            compared_to_average=analytics.compared_to_average,
            streak_count=analytics.streak_count,
            summary=analytics.summary,
        )


class DailyProgressGraphResponse(BaseModel):
    """Response model for daily progress graph/chart data"""
    dates: List[str] = Field(..., description="List of dates (YYYY-MM-DD)")
    completion_rates: List[float] = Field(..., description="Completion % per day")
    productivity_scores: List[float] = Field(..., description="Productivity score per day")
    focus_scores: List[float] = Field(..., description="Focus score per day")
    study_time_mins: List[int] = Field(..., description="Study minutes per day")
    streak_count: int = Field(..., description="Current completion streak")
    average_completion_rate: float = Field(..., description="Average completion rate")
    average_productivity: float = Field(..., description="Average productivity")


# ============================================================================
# USER DEADLINES
# ============================================================================

class UserDeadlineDB(BaseModel):
    """Stored deadline document."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    title: str
    due_date: date
    deadline_type: Literal["assignment", "quiz", "exam", "other"] = "other"
    description: Optional[str] = None
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str, date: str, datetime: str}


class CreateDeadlineRequest(BaseModel):
    title: str = Field(..., min_length=1)
    due_date: date
    deadline_type: Literal["assignment", "quiz", "exam", "other"] = "other"
    description: Optional[str] = None


class UserDeadlineResponse(BaseModel):
    id: str
    title: str
    due_date: str
    deadline_type: str
    description: Optional[str]
    completed: bool
    created_at: str
    days_left: int

    @classmethod
    def from_doc(cls, doc: dict) -> "UserDeadlineResponse":
        due = doc.get("due_date")
        if isinstance(due, datetime):
            due_date = due.date()
        elif isinstance(due, date):
            due_date = due
        else:
            due_date = date.fromisoformat(str(due))
        days_left = (due_date - date.today()).days
        created = doc.get("created_at")
        created_str = created.isoformat() if isinstance(created, (datetime, date)) else str(created)
        return cls(
            id=str(doc["_id"]),
            title=doc.get("title", ""),
            due_date=str(due_date),
            deadline_type=doc.get("deadline_type", "other"),
            description=doc.get("description"),
            completed=doc.get("completed", False),
            created_at=created_str,
            days_left=days_left,
        )


class PlanAnalyticsResponse(BaseModel):
    """API response for plan analytics"""
    plan_id: str
    overall_completion_rate: float
    overall_productivity_score: float
    subject_completion: Dict[str, float]
    total_sessions_completed: int
    total_sessions_missed: int
    avg_session_duration_mins: float
    mood_trend: str
    weekly_summaries: List[Dict]
    improved_topics: List[str]
    still_weak_topics: List[str]
    mastered_topics: List[str]
    
    @classmethod
    def from_db_model(cls, analytics: StudyPlanAnalytics):
        return cls(
            plan_id=str(analytics.plan_id),
            overall_completion_rate=analytics.overall_completion_rate,
            overall_productivity_score=analytics.overall_productivity_score,
            subject_completion=analytics.subject_completion,
            total_sessions_completed=analytics.total_sessions_completed,
            total_sessions_missed=analytics.total_sessions_missed,
            avg_session_duration_mins=analytics.avg_session_duration_mins,
            mood_trend=analytics.mood_trend,
            weekly_summaries=[ws.model_dump() for ws in analytics.weekly_summaries],
            improved_topics=analytics.improved_topics,
            still_weak_topics=analytics.still_weak_topics,
            mastered_topics=analytics.mastered_topics,
        )