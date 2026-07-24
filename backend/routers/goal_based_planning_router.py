"""
Goal-Based Planning Router (Phase 2b)
Endpoints for creating and managing learning goals with phased study plans
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import date
from bson import ObjectId

from core.db import get_db
from core.security import get_current_user
from models.phase2_schemas import (
    LearningGoal,
    GoalBasedPlan,
    GoalProgressResponse,
    GoalRecommendationsResponse,
)
from services.goal_based_planning_service import GoalBasedPlanningService


router = APIRouter(prefix="/api/v1/goals", tags=["goals"])


# ========================================================================
# GOAL MANAGEMENT ENDPOINTS
# ========================================================================


@router.post("/create", response_model=LearningGoal)
async def create_learning_goal(
    goal_title: str,
    goal_type: str,
    subject: str,
    topics_to_cover: List[str],
    deadline: date,
    target_score: Optional[float] = None,
    priority: str = "medium",
    include_prerequisites: bool = True,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Create a new learning goal
    
    Args:
        goal_title: Human-readable goal title (e.g., "Master DSA in 2 weeks")
        goal_type: exam, skill_acquisition, interview_prep, certification
        subject: Primary subject (e.g., "DSA")
        topics_to_cover: List of topics to master
        deadline: Goal deadline date
        target_score: Target quiz score (0-100)
        priority: low, medium, high
        include_prerequisites: Auto-include prerequisite topics
    """
    service = GoalBasedPlanningService(db)
    
    try:
        goal = await service.create_goal(
            user_id=ObjectId(current_user["_id"]),
            goal_title=goal_title,
            goal_type=goal_type,
            subject=subject,
            topics_to_cover=topics_to_cover,
            target_score=target_score,
            deadline=deadline,
            priority=priority,
            include_prerequisites=include_prerequisites,
        )
        return goal
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create goal: {str(e)}"
        )


@router.get("/list", response_model=List[LearningGoal])
async def list_goals(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    List user's learning goals
    
    Args:
        status_filter: Filter by status (not_started, in_progress, completed, on_hold)
    """
    service = GoalBasedPlanningService(db)
    goals = await service.list_goals(
        user_id=ObjectId(current_user["_id"]),
        status=status_filter,
    )
    return goals


@router.get("/{goal_id}", response_model=LearningGoal)
async def get_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get a specific goal"""
    service = GoalBasedPlanningService(db)
    
    try:
        goal = await service.get_goal(ObjectId(goal_id))
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        
        # Verify ownership
        if str(goal.user_id) != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this goal"
            )
        
        return goal
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{goal_id}/status")
async def update_goal_status(
    goal_id: str,
    new_status: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update goal status (not_started, in_progress, completed, on_hold)"""
    service = GoalBasedPlanningService(db)
    
    try:
        goal = await service.get_goal(ObjectId(goal_id))
        if not goal or str(goal.user_id) != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        updated_goal = await service.update_goal_status(
            ObjectId(goal_id),
            new_status
        )
        
        return {"success": True, "goal": updated_goal}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ========================================================================
# PHASED PLAN GENERATION ENDPOINTS
# ========================================================================


@router.post("/{goal_id}/generate-plan", response_model=GoalBasedPlan)
async def generate_phased_plan(
    goal_id: str,
    study_pace: str = "moderate",
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Generate a phased study plan from a goal
    
    Generates phases that respect prerequisites:
    - Phase 1: Foundation topics
    - Phase 2: Intermediate topics
    - Phase 3: Advanced topics
    - Phase 4: Integration & practice
    
    Args:
        goal_id: Goal ID to plan from
        study_pace: slow, moderate, fast
    """
    service = GoalBasedPlanningService(db)
    
    try:
        goal = await service.get_goal(ObjectId(goal_id))
        if not goal or str(goal.user_id) != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        plan = await service.generate_phased_plan(
            goal_id=ObjectId(goal_id),
            user_id=ObjectId(current_user["_id"]),
            study_pace=study_pace,
        )
        
        return plan
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate plan: {str(e)}"
        )


# ========================================================================
# PROGRESS TRACKING ENDPOINTS
# ========================================================================


@router.get("/{goal_id}/progress", response_model=GoalProgressResponse)
async def get_goal_progress(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get detailed progress on a goal
    
    Returns:
        - Progress percentage
        - Completed vs remaining topics
        - Current phase and phase deadlines
        - On-track status
    """
    service = GoalBasedPlanningService(db)
    
    try:
        goal = await service.get_goal(ObjectId(goal_id))
        if not goal or str(goal.user_id) != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        progress = await service.get_goal_progress(ObjectId(goal_id))
        return GoalProgressResponse(**progress)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{goal_id}/update-progress")
async def update_goal_progress(
    goal_id: str,
    topics_completed: List[str],
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update progress by marking topics as completed"""
    service = GoalBasedPlanningService(db)
    
    try:
        goal = await service.get_goal(ObjectId(goal_id))
        if not goal or str(goal.user_id) != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        progress = await service.update_goal_progress(
            ObjectId(goal_id),
            topics_completed,
        )
        
        return {"success": True, "progress": progress}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ========================================================================
# RECOMMENDATIONS ENDPOINT
# ========================================================================


@router.get("/{goal_id}/recommendations", response_model=GoalRecommendationsResponse)
async def get_goal_recommendations(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get recommendations to stay on track with goal
    
    Returns recommendations for:
    - Pace adjustments
    - Phase deadlines
    - Topics to focus on
    - Suggested daily hours
    """
    service = GoalBasedPlanningService(db)
    
    try:
        goal = await service.get_goal(ObjectId(goal_id))
        if not goal or str(goal.user_id) != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        recommendations = await service.get_goal_recommendations(ObjectId(goal_id))
        return GoalRecommendationsResponse(**recommendations)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )