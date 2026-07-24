"""
Phase 2 Enhancements: Prerequisite System, Goal-Based Planning, Multi-Plan Conflicts
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import date, datetime
from bson import ObjectId
from .user_schemas import PyObjectId

# ============================================================================
# PREREQUISITE TRACKING SYSTEM
# ============================================================================

class TopicPrerequisite(BaseModel):
    """Prerequisite relationship between topics"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    subject: str = Field(..., description="Subject name")
    dependent_topic: str = Field(..., description="Topic that requires prerequisites")
    prerequisite_topics: List[str] = Field(..., description="Topics that must be completed first")
    difficulty_level: Literal["foundation", "intermediate", "advanced"] = Field(
        default="intermediate", description="Difficulty level of dependent topic"
    )
    is_strict: bool = Field(
        default=True, 
        description="If true, all prerequisites must be completed before scheduling"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: str}


class PrerequisiteStatus(BaseModel):
    """Tracks prerequisite completion status for a user"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User ID")
    plan_id: PyObjectId = Field(..., description="Study plan ID")
    topic: str = Field(..., description="Topic in question")
    subject: str = Field(..., description="Subject name")
    prerequisites: Dict[str, bool] = Field(
        default_factory=dict,
        description="Prerequisite topic -> completion status"
    )
    blocking_prerequisites: List[str] = Field(
        default_factory=list, 
        description="Prerequisites not yet completed"
    )
    can_start: bool = Field(
        default=True,
        description="True if all prerequisites are completed"
    )
    estimated_unblock_date: Optional[date] = Field(
        None,
        description="Estimated date when all prerequisites will be done"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str, datetime: str}


class PrerequisiteChain(BaseModel):
    """Represents a chain of prerequisites (e.g., Arrays -> Linked Lists -> Graphs -> Trees)"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    subject: str = Field(..., description="Subject name")
    chain_name: str = Field(..., description="Human-readable chain name")
    topics_ordered: List[str] = Field(..., description="Topics in order (foundation -> advanced)")
    estimated_hours_per_topic: List[float] = Field(
        ..., 
        description="Estimated hours needed for each topic"
    )
    difficulty_progression: List[Literal["foundation", "intermediate", "advanced"]] = Field(
        ..., 
        description="Difficulty progression"
    )
    description: Optional[str] = Field(None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: str}


# ============================================================================
# GOAL-BASED PLANNING SYSTEM (Phase 2)
# ============================================================================

class LearningGoal(BaseModel):
    """Structured learning goal with prerequisite tracking"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User ID")
    goal_title: str = Field(..., description="Goal title (e.g., 'Master DSA in 2 weeks')")
    goal_type: Literal["exam", "skill_acquisition", "interview_prep", "certification"] = Field(
        ..., description="Type of goal"
    )
    subject: str = Field(..., description="Primary subject")
    topics_to_cover: List[str] = Field(..., description="Topics user wants to master")
    target_score: Optional[float] = Field(None, ge=0, le=100, description="Target quiz score")
    current_score: float = Field(default=0.0, ge=0, le=100)
    deadline: date = Field(..., description="Goal deadline")
    priority: Literal["low", "medium", "high"] = Field(
        default="medium", description="Goal priority"
    )
    
    # Prerequisites handling
    prerequisite_chains: List[str] = Field(
        default_factory=list, 
        description="Prerequisite chain IDs required"
    )
    prerequisites_met: bool = Field(default=False)
    prerequisites_completion_date: Optional[date] = Field(None)
    
    # Generated plan
    auto_generated_plan_id: Optional[PyObjectId] = Field(None)
    estimated_hours_needed: float = Field(default=0.0)
    
    # Progress
    progress_percentage: float = Field(default=0.0, ge=0, le=100)
    status: Literal["not_started", "in_progress", "paused", "completed"] = Field(
        default="not_started"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str, datetime: str}


class GoalBasedPlan(BaseModel):
    """Study plan automatically generated from a goal"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User ID")
    goal_id: PyObjectId = Field(..., description="Parent goal ID")
    
    # Relationship to study plan
    study_plan_id: PyObjectId = Field(..., description="Generated study plan ID")
    
    # Prerequisite ordering
    prerequisite_phases: List[Dict] = Field(
        default_factory=list,
        description="Phases ordered by prerequisites"
    )
    current_phase: int = Field(default=0)
    phases_completed: int = Field(default=0)
    
    # Timeline
    phase_deadlines: List[date] = Field(..., description="Deadline for each phase")
    
    # Status
    status: Literal["planning", "active", "blocked_on_prerequisites", "completed"] = Field(
        default="planning"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str, datetime: str}


# ============================================================================
# MULTI-PLAN CONFLICT RESOLUTION
# ============================================================================

class PlanConflict(BaseModel):
    """Represents a scheduling or resource conflict between plans"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User ID")
    conflict_date: date = Field(..., description="Date when conflict occurs")
    
    # Plans involved
    plan_ids: List[PyObjectId] = Field(..., description="Study plan IDs involved")
    plan_names: List[str] = Field(..., description="Human-readable plan names")
    
    # Conflict details
    conflict_type: Literal["time_overlap", "resource_exhaustion", "priority_clash"] = Field(
        ..., description="Type of conflict"
    )
    conflict_description: str = Field(..., description="Detailed description")
    severity: Literal["low", "medium", "high"] = Field(
        default="medium", description="Conflict severity"
    )
    
    # Affected sessions/tasks
    affected_sessions_count: int = Field(default=0)
    affected_total_hours: float = Field(default=0.0)
    
    # Resolution status
    is_resolved: bool = Field(default=False)
    resolution_type: Optional[Literal["merge", "reschedule", "deprioritize", "user_decision"]] = Field(None)
    resolution_details: Optional[Dict] = Field(None)
    user_resolution_suggested: Optional[List[Dict]] = Field(
        None, 
        description="Suggested resolutions for user"
    )
    
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = Field(None)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str, datetime: str}


class ConflictResolutionSuggestion(BaseModel):
    """Suggested resolution for a conflict"""
    conflict_id: PyObjectId = Field(..., description="Conflict ID")
    suggestion_type: Literal["redistribute_hours", "extend_deadline", "merge_similar", "deprioritize"] = Field(
        ..., description="Type of suggestion"
    )
    affected_plans: List[str] = Field(..., description="Plan names affected")
    
    # For redistribute_hours
    new_hours_distribution: Optional[Dict[str, float]] = Field(
        None, 
        description="Suggested hour redistribution {plan_name: hours}"
    )
    
    # For extend_deadline
    days_to_extend: Optional[int] = Field(None)
    new_deadline: Optional[date] = Field(None)
    
    # For merge_similar
    can_merge_topics: Optional[List[str]] = Field(None)
    
    # For deprioritize
    deprioritize_plan: Optional[str] = Field(None)
    
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in suggestion")
    impact_score: float = Field(default=0.0, ge=-1, le=1, description="Impact on productivity (-1 to 1)")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, date: str}


class UserPlanPreferences(BaseModel):
    """User's preferences for multi-plan management"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="User ID")
    
    # Conflict resolution preferences
    auto_resolve_conflicts: bool = Field(
        default=False, 
        description="Allow automatic conflict resolution"
    )
    resolution_priority: Literal["deadline", "priority", "minimize_changes"] = Field(
        default="deadline", 
        description="How to prioritize resolutions"
    )
    
    # Time preferences
    max_daily_study_hours: float = Field(..., ge=1, le=24, description="Maximum study hours per day")
    preferred_break_duration_mins: int = Field(default=30, ge=5, le=120)
    
    # Scheduling preferences
    study_start_time: str = Field(default="06:00", description="Preferred study start time")
    study_end_time: str = Field(default="23:00", description="Preferred study end time")
    weekend_study_enabled: bool = Field(default=True)
    
    # Notification preferences
    notify_on_conflicts: bool = Field(default=True)
    notify_on_prerequisites_blocked: bool = Field(default=True)
    notify_on_goal_progress: bool = Field(default=True)
    
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: str}


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateGoalRequest(BaseModel):
    """Request to create a learning goal"""
    goal_title: str = Field(..., min_length=3, max_length=100)
    goal_type: Literal["exam", "skill_acquisition", "interview_prep", "certification"]
    subject: str
    topics_to_cover: List[str]
    target_score: Optional[float] = Field(None, ge=0, le=100)
    deadline: date
    priority: Literal["low", "medium", "high"] = "medium"
    include_prerequisites: bool = Field(default=True, description="Auto-include prerequisite topics")


class GeneratePlanFromGoalRequest(BaseModel):
    """Request to generate a study plan from a goal"""
    goal_id: PyObjectId
    total_study_hours: float = Field(..., ge=1, le=1000)
    study_pace: Literal["slow", "moderate", "fast"]
    start_date: date


class PrerequisiteStatusResponse(BaseModel):
    """Response showing prerequisite status"""
    topic: str
    subject: str
    prerequisites: Dict[str, bool]
    blocking_prerequisites: List[str]
    can_start: bool
    estimated_unblock_date: Optional[date]
    recommended_action: Optional[str]


class ConflictDetectionResponse(BaseModel):
    """Response when conflicts are detected"""
    conflicts_found: int
    conflicts: List[PlanConflict]
    total_affected_hours: float
    suggested_resolutions: List[ConflictResolutionSuggestion]


class GoalProgressResponse(BaseModel):
    """Response showing goal progress"""
    goal_id: PyObjectId
    goal_title: str
    progress_percentage: float
    topics_completed: List[str]
    topics_remaining: List[str]
    prerequisites_met: bool
    estimated_completion_date: date
    current_phase: int
    total_phases: int


class Recommendation(BaseModel):
    """A single recommendation for staying on track"""
    type: str  # pace_warning, pace_ahead, phase_overdue, phase_deadline_soon, focus_topics
    severity: str  # high, medium, info
    message: str
    action: str


class GoalRecommendationsResponse(BaseModel):
    """Response containing recommendations for a goal"""
    goal_id: str
    recommendations: List[Recommendation]
    on_track: bool
    suggested_daily_hours: int