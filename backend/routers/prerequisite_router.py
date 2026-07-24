"""
Prerequisite Tracking API Router (Phase 2)
Endpoints for prerequisite validation, chain management, and blocking analysis
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import date
from bson import ObjectId

from core.db import get_db
from core.security import get_current_user
from models.phase2_schemas import (
    TopicPrerequisite,
    PrerequisiteChain,
    PrerequisiteStatusResponse,
)
from services.prerequisite_service import PrerequisiteService
from models.user_schemas import UserInDB

router = APIRouter(prefix="/api/prerequisites", tags=["prerequisites"])


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_prerequisite_service(db=Depends(get_db)) -> PrerequisiteService:
    """Inject PrerequisiteService"""
    return PrerequisiteService(db)


# ============================================================================
# PREREQUISITE REQUIREMENT MANAGEMENT
# ============================================================================

@router.post(
    "/requirements",
    response_model=TopicPrerequisite,
    status_code=status.HTTP_201_CREATED,
    summary="Create prerequisite requirement",
    description="Define that a topic requires other topics as prerequisites",
)
async def create_prerequisite_requirement(
    subject: str,
    dependent_topic: str,
    prerequisite_topics: List[str],
    difficulty_level: str = "intermediate",
    is_strict: bool = True,
    current_user: UserInDB = Depends(get_current_user),
    service: PrerequisiteService = Depends(get_prerequisite_service),
):
    """
    Create a prerequisite requirement
    
    **Example:**
    - Subject: DSA
    - Dependent Topic: Graphs
    - Prerequisites: [Arrays, Linked Lists]
    - This means: Can't learn Graphs until Arrays and Linked Lists are mastered
    
    **Parameters:**
    - `subject`: Subject name (DSA, WebDev, etc)
    - `dependent_topic`: Topic requiring prerequisites
    - `prerequisite_topics`: List of required prerequisite topics
    - `is_strict`: If true, ALL prerequisites must be completed
    """
    try:
        prerequisite = await service.create_prerequisite_requirement(
            subject=subject,
            dependent_topic=dependent_topic,
            prerequisite_topics=prerequisite_topics,
            difficulty_level=difficulty_level,
            is_strict=is_strict,
        )
        return prerequisite
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create prerequisite: {str(e)}",
        )


@router.get(
    "/requirements/{subject}/{topic}",
    response_model=Optional[TopicPrerequisite],
    summary="Get prerequisite requirements for a topic",
)
async def get_topic_prerequisites(
    subject: str,
    topic: str,
    current_user: UserInDB = Depends(get_current_user),
    service: PrerequisiteService = Depends(get_prerequisite_service),
):
    """Get what topics must be completed before starting this topic"""
    try:
        prerequisite = await service.get_prerequisites_for_topic(subject, topic)
        return prerequisite
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/requirements/{subject}/{topic}/dependents",
    response_model=List[TopicPrerequisite],
    summary="Get topics requiring this topic",
)
async def get_dependent_topics(
    subject: str,
    topic: str,
    current_user: UserInDB = Depends(get_current_user),
    service: PrerequisiteService = Depends(get_prerequisite_service),
):
    """Get all topics that require this topic as a prerequisite"""
    try:
        dependents = await service.get_topics_requiring_prerequisite(
            subject, topic
        )
        return dependents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================================
# PREREQUISITE CHAIN MANAGEMENT
# ============================================================================

@router.post(
    "/chains",
    response_model=PrerequisiteChain,
    status_code=status.HTTP_201_CREATED,
    summary="Create prerequisite chain",
    description="Create a learning path (foundation -> intermediate -> advanced)",
)
async def create_chain(
    subject: str,
    chain_name: str,
    topics_ordered: List[str],
    estimated_hours_per_topic: List[float],
    difficulty_progression: List[str],
    description: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user),
    service: PrerequisiteService = Depends(get_prerequisite_service),
):
    """
    Create a prerequisite chain representing a learning path
    
    **Example - DSA Foundation Chain:**
    - Topics: [Arrays, Linked Lists, Stacks, Queues, Trees]
    - Difficulties: [foundation, foundation, intermediate, intermediate, advanced]
    - Hours: [8, 10, 12, 12, 15]
    
    Each topic depends on all previous topics in the chain.
    """
    if (
        len(topics_ordered)
        != len(estimated_hours_per_topic)
        != len(difficulty_progression)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All arrays must have equal length",
        )

    try:
        chain = await service.create_prerequisite_chain(
            subject=subject,
            chain_name=chain_name,
            topics_ordered=topics_ordered,
            estimated_hours_per_topic=estimated_hours_per_topic,
            difficulty_progression=difficulty_progression,
            description=description,
        )
        return chain
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/chains/{subject}/{chain_name}",
    response_model=Optional[PrerequisiteChain],
    summary="Get prerequisite chain",
)
async def get_chain(
    subject: str,
    chain_name: str,
    current_user: UserInDB = Depends(get_current_user),
    service: PrerequisiteService = Depends(get_prerequisite_service),
):
    """Get a specific prerequisite chain"""
    try:
        chain = await service.get_prerequisite_chain(subject, chain_name)
        if not chain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chain not found",
            )
        return chain
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================================
# PREREQUISITE STATUS & VALIDATION
# ============================================================================

@router.get(
    "/plans/{plan_id}/topics/{topic}/can-start",
    response_model=PrerequisiteStatusResponse,
    summary="Check if topic can be started",
    description="Validate if all prerequisites are met for a topic",
)
async def check_can_start_topic(
    plan_id: str,
    topic: str,
    subject: str,
    current_user: UserInDB = Depends(get_current_user),
    service: PrerequisiteService = Depends(get_prerequisite_service),
):
    """
    Check if a topic can be started in the context of a plan
    
    Returns:
    - `can_start`: Boolean indicating if ready
    - `blocking_prerequisites`: List of topics blocking progress
    - `estimated_unblock_date`: When all prerequisites will be complete
    
    **Example Response:**
    ```json
    {
      "topic": "Graphs",
      "subject": "DSA",
      "prerequisites": {
        "Arrays": true,
        "Linked Lists": false
      },
      "blocking_prerequisites": ["Linked Lists"],
      "can_start": false,
      "estimated_unblock_date": "2024-04-15"
    }
    ```
    """
    try:
        plan_oid = ObjectId(plan_id)
        can_start, blocking = await service.can_start_topic(
            current_user.id, plan_oid, topic, subject
        )

        estimated_date = await service.estimate_topic_availability(
            current_user.id, plan_oid, topic, subject
        )

        status = await service.get_prerequisite_status(
            current_user.id, plan_oid, topic, subject
        )

        prerequisites_dict = status.prerequisites if status else {}

        return PrerequisiteStatusResponse(
            topic=topic,
            subject=subject,
            prerequisites=prerequisites_dict,
            blocking_prerequisites=blocking,
            can_start=can_start,
            estimated_unblock_date=estimated_date,
            recommended_action=(
                f"Complete {blocking[0]} first"
                if blocking
                else "Ready to start!"
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/plans/{plan_id}/topics/{topic}/mark-prerequisite-completed",
    status_code=status.HTTP_200_OK,
    summary="Mark prerequisite completed",
)
async def mark_prerequisite_completed(
    plan_id: str,
    topic: str,
    subject: str,
    current_user: UserInDB = Depends(get_current_user),
    service: PrerequisiteService = Depends(get_prerequisite_service),
):
    """
    Mark a topic as completed and unblock dependent topics
    
    **Returns:**
    - Number of dependent topics that are now unblocked
    - List of newly available topics
    """
    try:
        plan_oid = ObjectId(plan_id)
        unblocked_count = await service.mark_prerequisite_completed(
            current_user.id, plan_oid, topic, subject
        )

        return {
            "success": True,
            "completed_topic": topic,
            "dependent_topics_unblocked": unblocked_count,
            "message": f"{unblocked_count} topics are now available to study",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================================
# ANALYTICS & REPORTING
# ============================================================================

@router.get(
    "/plans/{plan_id}/analytics/blocking-progress",
    summary="Get prerequisite blocking analytics",
    description="Overview of prerequisites blocking progress in a plan",
)
async def get_blocking_progress(
    plan_id: str,
    subject: str,
    current_user: UserInDB = Depends(get_current_user),
    service: PrerequisiteService = Depends(get_prerequisite_service),
):
    """
    Get analytics about which prerequisites are blocking progress
    
    **Returns:**
    - `total_topics`: Total topics in subject
    - `topics_unblocked`: Topics ready to start
    - `topics_blocked`: Topics waiting on prerequisites
    - `critical_blockers`: Top 5 topics blocking most other topics
    - `unblock_percentage`: % of topics ready (0-100)
    
    **Example:**
    ```json
    {
      "total_topics": 5,
      "topics_unblocked": 2,
      "topics_blocked": 3,
      "unblock_percentage": 40,
      "critical_blockers": [
        ["Linked Lists", 3],
        ["Arrays", 2]
      ]
    }
    ```
    """
    try:
        plan_oid = ObjectId(plan_id)
        analytics = await service.get_prerequisites_blocking_progress(
            current_user.id, plan_oid, subject
        )
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/chains/{chain_id}/progress",
    summary="Get prerequisite chain progress",
    description="Detailed progress through a prerequisite chain",
)
async def get_chain_progress(
    plan_id: str,
    chain_id: str,
    current_user: UserInDB = Depends(get_current_user),
    service: PrerequisiteService = Depends(get_prerequisite_service),
):
    """
    Get detailed progress through a prerequisite chain
    
    **Returns:**
    - Chain name and subject
    - Progress for each topic (completion %, can_start status)
    - Overall chain completion percentage
    
    **Example:**
    ```json
    {
      "chain_name": "DSA Foundation",
      "subject": "DSA",
      "total_topics": 5,
      "overall_progress": 40,
      "topics_progress": {
        "Arrays": {
          "index": 0,
          "difficulty": "foundation",
          "can_start": true,
          "completion_percentage": 100
        },
        "Linked Lists": {
          "index": 1,
          "difficulty": "foundation",
          "can_start": true,
          "completion_percentage": 60
        }
      }
    }
    ```
    """
    try:
        chain_oid = ObjectId(chain_id)
        progress = await service.get_prerequisite_chain_progress(
            current_user.id, ObjectId(plan_id), chain_oid
        )
        return progress
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )