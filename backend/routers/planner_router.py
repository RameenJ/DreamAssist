# backend/routers/planner_router.py
"""
Study Planner & Scheduler API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import date, datetime, timedelta, time
from typing import List, Optional
from bson import ObjectId


from motor.motor_asyncio import AsyncIOMotorDatabase
from core.db import get_database 
from core.security import get_current_user
from models.user_schemas import UserPublic, PyObjectId
from models.planner_schemas import (
    GenerateStudyPlanRequest,
    StudyPlanResponse,
    StudySessionResponse,
    PlanAnalyticsResponse,
    SessionCompletionRequest,
    SessionCompletionResponse,
    RescheduleRequest,
    StudyPlan,
    StudySession,
    CreateDeadlineRequest,
    UserDeadlineResponse,
)
from services.study_planner import StudyPlanner, auto_generate_initial_plan
from services.study_scheduler import DailyScheduler, schedule_week
from services.progress_tracker import PlanAnalytics, AdaptiveTracker
from services.mood_adapter import MoodAdapter

router = APIRouter()


@router.post("/plans/generate", response_model=StudyPlanResponse, status_code=201)
async def generate_study_plan(
    request: GenerateStudyPlanRequest,
    current_user: UserPublic = Depends(get_current_user),
    db = Depends(get_database),
):
    """
    Generate a new study plan.

    Args:
        request: Plan generation parameters (subjects, deadline, mode, hours/week)
        current_user: Current authenticated user
        db: Database instance

    Returns:
        StudyPlanResponse with plan details
    """
    import logging
    from datetime import timedelta   # ensure timedelta is available
    logger = logging.getLogger(__name__)
    
    try:
        # Convert user ID to ObjectId once
        user_id_oid = ObjectId(current_user.id)
        logger.info(f"Generating plan for user {user_id_oid}")

        # Validate deadline is in future
        if request.deadline <= date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deadline must be in the future",
            )

        # Validate subjects not empty
        if not request.subjects or len(request.subjects) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one subject is required",
            )

        # Get user's study pace preference
        user_doc = await db.users.find_one({"_id": user_id_oid})
        study_pace = "moderate"
        if user_doc and user_doc.get("subject_profiles"):
            study_pace = user_doc["subject_profiles"][0].get("study_pace", "moderate")

        # Generate plan - convert ObjectId to PyObjectId for type compatibility
        planner = StudyPlanner(db)
        plan = await planner.generate_study_plan(
            user_id=PyObjectId(user_id_oid),
            subjects=request.subjects,
            deadline=request.deadline,
            mode=request.mode,
            total_study_hours_per_week=request.total_study_hours_per_week,
            plan_name=request.plan_name,
            study_pace=study_pace,
        )

        logger.info(f"Plan created successfully. ID: {plan.id} (type: {type(plan.id).__name__}), User: {plan.user_id} (type: {type(plan.user_id).__name__})")
        
        # Verify plan can be retrieved before responding
        user_id_str = str(user_id_oid)
        user_verify_query = {"$or": [{"user_id": user_id_oid}, {"user_id": user_id_str}]}
        plan_verify = await db.study_plans.find_one({"_id": plan.id, **user_verify_query})
        if not plan_verify:
            logger.error(f"CRITICAL: Plan {plan.id} not found immediately after creation!")
        else:
            logger.info(f"✓ Plan verified in database")

        # ========== NEW: Pre-generate daily sessions for this plan ==========
        from services.study_scheduler import DailyScheduler
        scheduler = DailyScheduler(db)
        
        # Generate sessions for each day between start_date and end_date
        current_day = plan.start_date
        while current_day <= plan.end_date:
            try:
                await scheduler.schedule_day(
                    user_id=PyObjectId(user_id_oid),
                    target_date=current_day,
                    plan_ids=[plan.id],  # Pass the new plan ID
                    current_mood=None,
                )
                logger.info(f"  ✅ Session generated for {current_day}")
            except Exception as e:
                logger.warning(f"  ⚠️ Failed to generate session for {current_day}: {e}")
            current_day += timedelta(days=1)
        # ========== END NEW CODE ==========

        return StudyPlanResponse.from_db_model(plan)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error generating plan: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating plan: {str(e)}",
        )
    
@router.get("/plans/{plan_id}", response_model=StudyPlanResponse)
async def get_study_plan(
    plan_id: str,
    current_user: UserPublic = Depends(get_current_user),
    db = Depends(get_database),
):
    """Retrieve a study plan by ID."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # STEP 1: Validate plan_id format
        if not plan_id or not plan_id.strip():
            logger.error(f"❌ Empty plan_id received")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plan ID cannot be empty",
            )
        
        # Validate ObjectId format
        if not ObjectId.is_valid(plan_id):
            logger.error(f"❌ Invalid plan_id format: {plan_id} (must be 24-char hex)")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan ID format: {plan_id}. Must be a valid MongoDB ObjectId (24 hexadecimal characters)",
            )
        
        try:
            plan_oid = ObjectId(plan_id)
        except Exception as e:
            logger.error(f"❌ Failed to convert plan_id to ObjectId: {plan_id}. Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan ID format",
            )
        
        # STEP 2: Get current user info
        user_id = ObjectId(current_user.id)
        user_id_str = current_user.id
        logger.info(f"🔍 Fetching plan {plan_id} for user {user_id_str}")
        logger.debug(f"   Type check - plan_oid: {type(plan_oid).__name__}, user_id: {type(user_id).__name__}")

        # STEP 3: Query with both ID filters - handle both ObjectId and string formats
        user_query = {"$or": [{"user_id": user_id}, {"user_id": user_id_str}]}
        
        logger.debug(f"   Query: {{'_id': {plan_oid}, '$or': [...]}} with user_id in [{user_id}, {user_id_str}]")
        
        plan_doc = await db.study_plans.find_one(
            {"_id": plan_oid, **user_query}
        )

        if not plan_doc:
            logger.warning(f"❌ Plan {plan_id} not found for user {user_id_str}")
            
            # Debug: Check if plan exists but belongs to different user
            any_plan = await db.study_plans.find_one({"_id": plan_oid})
            if any_plan:
                logger.warning(f"   ⚠️ Plan exists but owned by user: {any_plan.get('user_id', 'UNKNOWN')} (current user: {user_id_str})")
            else:
                logger.warning(f"   ⚠️ Plan ID {plan_id} does not exist in database")
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plan not found: {plan_id}",
            )

        logger.info(f"✓ Plan found. Fields: {list(plan_doc.keys())}")
        logger.debug(f"   plan_doc['_id']: {plan_doc.get('_id')} (type: {type(plan_doc.get('_id')).__name__})")
        logger.debug(f"   plan_doc['user_id']: {plan_doc.get('user_id')} (type: {type(plan_doc.get('user_id')).__name__})")

        # STEP 4: Convert datetime objects back to date objects for model compatibility
        from core.datetime_utils import convert_datetime_to_date
        plan_doc = convert_datetime_to_date(plan_doc)

        try:
            plan = StudyPlan(**plan_doc)
        except Exception as model_error:
            logger.error(f"❌ Error creating StudyPlan model from doc: {model_error}")
            logger.error(f"   Doc fields: {list(plan_doc.keys())}")
            logger.error(f"   Doc: {plan_doc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error parsing plan data: {str(model_error)}",
            )
        
        response = StudyPlanResponse.from_db_model(plan)
        logger.info(f"✅ Successfully returning plan {plan_id}")
        logger.debug(f"   Response plan_id: {response.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"❌ Unexpected error retrieving plan: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving plan: {str(e)}",
        )


@router.get("/plans", response_model=List[StudyPlanResponse])
async def list_user_plans(
    status_filter: Optional[str] = None,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """List all plans for current user."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        user_id_str = current_user.id
        user_id = ObjectId(user_id_str)
        
        logger.info(f"📋 Listing plans for user: {user_id_str}")

        # Build query to handle both ObjectId and string storage formats
        user_query = {"$or": [{"user_id": user_id}, {"user_id": user_id_str}]}
        
        # Add status filter if provided
        if status_filter and status_filter in ["active", "paused", "completed", "archived"]:
            query: dict = {"$and": [user_query, {"status": status_filter}]}  # type: ignore
            logger.info(f"   Filter: status = {status_filter}")
        else:
            query: dict = user_query  # type: ignore

        cursor = db.study_plans.find(query).sort("created_at", -1)
        plans = await cursor.to_list(length=50)
        
        logger.info(f"✓ Found {len(plans)} plans for user {user_id_str}")
        
        if plans:
            logger.debug(f"   Plan IDs returned:")
            for i, plan in enumerate(plans):
                plan_id = plan.get('_id')
                plan_status = plan.get('status', 'UNKNOWN')
                logger.debug(f"     [{i+1}] ID: {plan_id}, Status: {plan_status}")

        # ✅ CRITICAL FIX: Verify all returned plans actually exist and belong to user
        # This prevents stale plan IDs from being returned in list but not found in get
        verified_plans = []
        for i, plan in enumerate(plans):
            plan_id = plan.get('_id')
            # Double-check plan ownership and existence
            verification_query = {"_id": plan_id, **user_query}
            logger.info(f"   Verifying plan [{i+1}/3]: {plan_id}")
            verified = await db.study_plans.find_one(verification_query)
            if verified:
                logger.info(f"     ✅ PASS - Plan exists and user owns it")
                verified_plans.append(verified)
            else:
                logger.warning(f"     ❌ FAIL - Plan {plan_id} failed verification - excluding from list")
                # Double-check if plan exists at all (different owner?)
                # Ensure plan_id is ObjectId for comparison
                plan_oid = ObjectId(plan_id) if isinstance(plan_id, str) else plan_id
                exists_anywhere = await db.study_plans.find_one({"_id": plan_oid})
                if exists_anywhere:
                    logger.warning(f"        ⚠️ Plan exists but owned by: {exists_anywhere.get('user_id')}")
                else:
                    logger.warning(f"        ⚠️ Plan does not exist in database at all")
        
        logger.info(f"✅ After verification: {len(verified_plans)} plans verified for user {user_id_str}")
        if verified_plans:
            logger.info(f"   Returning plan IDs: {[str(p.get('_id')) for p in verified_plans]}")

        # Convert datetime objects back to date objects for model compatibility
        from core.datetime_utils import convert_datetime_to_date
        verified_plans = [convert_datetime_to_date(plan) for plan in verified_plans]

        responses = [StudyPlanResponse.from_db_model(StudyPlan(**plan)) for plan in verified_plans]
        
        logger.debug(f"   Response IDs:")
        for i, resp in enumerate(responses):
            logger.debug(f"     [{i+1}] id: {resp.id}")
        
        return responses

    except Exception as e:
        import traceback
        logger.error(f"❌ Error listing plans: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing plans: {str(e)}",
        )


@router.get("/plans/{plan_id}/sessions/today", response_model=StudySessionResponse)
async def get_today_session(
    plan_id: str,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Get today's scheduled session for a specific plan (or aggregated if no plan_id provided)."""
    try:
        plan_oid = ObjectId(plan_id)
        user_id = ObjectId(current_user.id)
        user_id_str = current_user.id
        today = date.today()

        # Check plan ownership
        user_query = {"$or": [{"user_id": user_id}, {"user_id": user_id_str}]}
        plan_doc = await db.study_plans.find_one(
            {"_id": plan_oid, **user_query}
        )
        if not plan_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        # Get today's session for this specific plan
        # Use the new scheduler method with plan_ids list (single plan)
        scheduler = DailyScheduler(db)
        session = await scheduler.schedule_day(
            user_id=PyObjectId(user_id),
            target_date=today,
            plan_ids=[PyObjectId(plan_oid)],   # Only this plan
            current_mood=None,                 # Optionally fetch from mood service
        )
        return StudySessionResponse.from_db_model(session)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session: {str(e)}",
        )

@router.get("/plans/{plan_id}/sessions/{session_date}", response_model=StudySessionResponse)
async def get_plan_session_by_date(
    plan_id: str,
    session_date: str,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get the study session for a specific plan on a specific date.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Parse date
        try:
            target_date = datetime.strptime(session_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )
        
        # Verify plan exists and belongs to user
        plan_oid = ObjectId(plan_id)
        user_id = ObjectId(current_user.id)
        user_id_str = current_user.id
        
        user_query = {"$or": [{"user_id": user_id}, {"user_id": user_id_str}]}
        plan_doc = await db.study_plans.find_one({"_id": plan_oid, **user_query})
        if not plan_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )
        
        # Convert start_date and end_date to date objects (they might be datetime from DB)
        start_date = plan_doc["start_date"]
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        end_date = plan_doc["end_date"]
        if isinstance(end_date, datetime):
            end_date = end_date.date()
        
        # Check if date is within plan's range
        if target_date < start_date or target_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Date {session_date} is outside plan range {start_date} to {end_date}",
            )
        
        # Use scheduler to generate (or retrieve) the session
        scheduler = DailyScheduler(db)
        session = await scheduler.schedule_day(
            user_id=PyObjectId(user_id),
            target_date=target_date,
            plan_ids=[PyObjectId(plan_oid)],
            current_mood=None,
        )
        
        return StudySessionResponse.from_db_model(session)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plan session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session: {str(e)}",
        )
    

    
@router.post("/sessions/{session_id}/complete", response_model=SessionCompletionResponse)
async def complete_session(
    session_id: str,
    completion: SessionCompletionRequest,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Mark session as completed and trigger adaptive updates."""
    try:
        session_oid = ObjectId(session_id)
        user_id = ObjectId(current_user.id)

        # Verify session ownership - handle both ObjectId and string formats
        session_doc = await db.study_sessions.find_one({"_id": session_oid})
        if not session_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        
        # Compare user_id - handle both ObjectId and string formats
        session_user_id = session_doc.get("user_id")
        user_id_str = str(user_id)
        if str(session_user_id) != user_id_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Convert task IDs to PyObjectId
        completed_task_ids_py = [PyObjectId(tid) for tid in completion.completed_task_ids]

        # Log completion and trigger adaptive updates
        tracker = AdaptiveTracker(db)
        result = await tracker.log_session_completion(
            session_id=PyObjectId(session_oid),
            completed_task_ids=completed_task_ids_py,
            user_emotion_end=completion.user_mood_end,
            interrupted=completion.interrupted,
            notes=completion.notes,
        )

        # Get next session date
        current_session = await db.study_sessions.find_one({"_id": session_oid})
        if current_session is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session not found after completion",
            )
        session_date = current_session.get("session_date")
        next_session_date = (session_date + timedelta(days=1)).isoformat() if session_date else None

        return SessionCompletionResponse(
            success=result.get("success", True),
            message=result.get("message", ""),
            session_id=session_id,
            completed_blocks=current_session.get("completed_blocks", len(completed_task_ids_py)),
            total_blocks=len(current_session.get("time_blocks", [])),
            next_session_date=next_session_date,
            suggested_actions=result.get("adaptive_actions_taken", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing session: {str(e)}",
        )


@router.get("/plans/{plan_id}/analytics", response_model=PlanAnalyticsResponse)
async def get_plan_analytics(
    plan_id: str,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Get comprehensive analytics for a plan."""
    try:
        plan_oid = ObjectId(plan_id)
        user_id = ObjectId(current_user.id)
        user_id_str = current_user.id

        # Verify plan ownership - handle both ObjectId and string formats
        user_query = {"$or": [{"user_id": user_id}, {"user_id": user_id_str}]}
        plan_doc = await db.study_plans.find_one(
            {"_id": plan_oid, **user_query}
        )
        if not plan_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        # Compute analytics
        analytics_service = PlanAnalytics(db)
        try:
            analytics = await analytics_service.compute_plan_analytics(PyObjectId(plan_oid))
        except Exception as e:
            import traceback
            print("🔥 Full traceback:", traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error computing analytics: {str(e)}",
            )
        return PlanAnalyticsResponse.from_db_model(analytics)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing analytics: {str(e)}",
        )


@router.put("/plans/{plan_id}/reschedule", response_model=StudyPlanResponse)
async def manual_reschedule(
    plan_id: str,
    request: RescheduleRequest,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Manually reschedule a plan (e.g., deadline change, adjustment)."""
    try:
        plan_oid = ObjectId(plan_id)
        user_id = ObjectId(current_user.id)
        user_id_str = current_user.id

        # Verify plan ownership - handle both ObjectId and string formats
        user_query = {"$or": [{"user_id": user_id}, {"user_id": user_id_str}]}
        plan_doc = await db.study_plans.find_one(
            {"_id": plan_oid, **user_query}
        )
        if not plan_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        updates = {}

        # Update deadline if provided
        if request.new_deadline:
            if request.new_deadline <= date.today():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New deadline must be in the future",
                )
            updates["end_date"] = request.new_deadline

        # Update tasks if adjustments provided
        if request.task_adjustments:
            for task_id_str, new_status in request.task_adjustments.items():
                task_oid = ObjectId(task_id_str)
                await db.study_tasks.update_one(
                    {"_id": task_oid},
                    {"$set": {"status": new_status, "updated_at": datetime.utcnow()}},
                )

        updates["last_adapted_at"] = datetime.utcnow()

        await db.study_plans.update_one(
            {"_id": plan_oid},
            {"$set": updates},
        )

        # Fetch and return updated plan
        updated_doc = await db.study_plans.find_one({"_id": plan_oid})
        if updated_doc is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated plan",
            )
        # Convert datetime objects back to date objects for model compatibility
        from core.datetime_utils import convert_datetime_to_date
        updated_doc = convert_datetime_to_date(updated_doc)
        plan = StudyPlan(**updated_doc)
        return StudyPlanResponse.from_db_model(plan)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rescheduling plan: {str(e)}",
        )


@router.post("/plans/{plan_id}/pause", response_model=StudyPlanResponse)
async def pause_plan(
    plan_id: str,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Pause a study plan."""
    try:
        plan_oid = ObjectId(plan_id)
        user_id = ObjectId(current_user.id)
        user_id_str = current_user.id

        # Update with both ObjectId and string format support
        user_query = {"$or": [{"user_id": user_id}, {"user_id": user_id_str}]}
        result = await db.study_plans.update_one(
            {"_id": plan_oid, **user_query},
            {"$set": {"status": "paused", "updated_at": datetime.utcnow()}},
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        updated_doc = await db.study_plans.find_one({"_id": plan_oid})
        if updated_doc is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated plan",
            )
        # Convert datetime objects back to date objects for model compatibility
        from core.datetime_utils import convert_datetime_to_date
        updated_doc = convert_datetime_to_date(updated_doc)
        plan = StudyPlan(**updated_doc)
        return StudyPlanResponse.from_db_model(plan)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error pausing plan: {str(e)}",
        )


@router.post("/plans/{plan_id}/resume", response_model=StudyPlanResponse)
async def resume_plan(
    plan_id: str,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Resume a paused study plan."""
    try:
        plan_oid = ObjectId(plan_id)
        user_id = ObjectId(current_user.id)
        user_id_str = current_user.id

        # Update with both ObjectId and string format support
        user_query = {"$or": [{"user_id": user_id}, {"user_id": user_id_str}]}
        result = await db.study_plans.update_one(
            {"_id": plan_oid, **user_query},
            {"$set": {"status": "active", "updated_at": datetime.utcnow()}},
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        updated_doc = await db.study_plans.find_one({"_id": plan_oid})
        if updated_doc is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated plan",
            )
        # Convert datetime objects back to date objects for model compatibility
        from core.datetime_utils import convert_datetime_to_date
        updated_doc = convert_datetime_to_date(updated_doc)
        plan = StudyPlan(**updated_doc)
        return StudyPlanResponse.from_db_model(plan)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error resuming plan: {str(e)}",
        )


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: str,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Delete a study plan."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        plan_oid = ObjectId(plan_id)
        user_id = ObjectId(current_user.id)
        user_id_str = current_user.id

        # Delete with both ObjectId and string format support
        user_query = {"$or": [{"user_id": user_id}, {"user_id": user_id_str}]}
        result = await db.study_plans.delete_one(
            {"_id": plan_oid, **user_query}
        )

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        # Also delete associated tasks and sessions
        await db.study_tasks.delete_many({"plan_id": plan_oid})
        await db.study_sessions.delete_many({"plan_id": plan_oid})

        # Remove from user's active plans
        await db.users.update_one(
            {"_id": user_id},
            {"$pull": {"active_plans": plan_oid}},
        )
        
        logger.info(f"✅ Plan {plan_id} deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting plan: {str(e)}",
        )


# ==================== UTILITY ENDPOINTS ====================

@router.post("/cleanup/stale-plans")
async def cleanup_stale_plans(
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Clean up stale plan IDs from user's active_plans list.
    This removes any plan IDs that no longer exist in the database.
    Useful for fixing issues caused by old cached plan IDs.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        user_id = ObjectId(current_user.id)
        
        # Get user's current active_plans list
        user = await db.users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        active_plans = user.get("active_plans", [])
        logger.info(f"🧹 Cleaning stale plans for user {user_id}. Current active_plans: {active_plans}")
        
        if not active_plans:
            logger.info(f"✅ No active plans to clean")
            return {"message": "No active plans to clean", "removed": 0, "remaining": 0}
        
        # Verify each plan exists and belongs to user
        valid_plan_ids = []
        for plan_id in active_plans:
            # Handle both ObjectId and string formats
            plan_oid = ObjectId(plan_id) if isinstance(plan_id, str) else plan_id
            plan = await db.study_plans.find_one({"_id": plan_oid})
            
            if plan:
                valid_plan_ids.append(plan_oid)
                logger.info(f"  ✅ Plan {plan_oid} exists and is valid")
            else:
                logger.warning(f"  ❌ Plan {plan_oid} is stale - removing from active_plans")  # ← fixed
        
        # Update user's active_plans with only valid plans
        removed_count = len(active_plans) - len(valid_plan_ids)
        
        await db.users.update_one(
            {"_id": user_id},
            {"$set": {"active_plans": valid_plan_ids}}
        )
        
        logger.info(f"✅ Cleanup complete. Removed {removed_count} stale plan(s). {len(valid_plan_ids)} plan(s) remaining")  # ← fixed
        
        return {
            "message": "Stale plans cleaned successfully",
            "removed": removed_count,
            "remaining": len(valid_plan_ids),
            "remaining_plans": [str(pid) for pid in valid_plan_ids]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error cleaning stale plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning stale plans: {str(e)}",
        )

# ==================== AGGREGATED SESSION ENDPOINTS ====================
# These endpoints work across ALL active plans for a user (not plan-specific)

@router.get("/sessions/today/aggregated", response_model=StudySessionResponse)
async def get_aggregated_today_session(
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get today's aggregated schedule across ALL active plans.
    
    This endpoint combines tasks from all user's active plans into a single
    daily session, useful for viewing a consolidated schedule.
    
    Returns 200 with empty session if user has no active plans.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        user_id = ObjectId(current_user.id)
        user_id_str = current_user.id
        today = date.today()
        
        # Get all active plans for this user
        user_query = {"$or": [{"user_id": user_id}, {"user_id": user_id_str}]}
        active_plans = await db.study_plans.find(
            {**user_query, "status": "active"}
        ).to_list(None)
        
        if not active_plans:
            logger.warning(f"⚠️ No active plans found for user {user_id}")
            # Return empty session (200 OK, not 404)
            empty_session = StudySession(
                plan_id=None,
                user_id=PyObjectId(user_id),
                session_date=today,
                start_time=time(9, 0),
                end_time=time(17, 0),
                time_blocks=[],
                aggregated_plan_ids=None,
                mood_at_start=None,
                mood_at_end=None,
                started_at=None,
                completed_at=None,
                actual_duration_mins=None,
                status="scheduled",
                notes="No active study plans found for this user.",
            )
            return StudySessionResponse.from_db_model(empty_session)
        
        # Convert plan IDs to PyObjectId
        plan_ids = [PyObjectId(plan["_id"]) for plan in active_plans]
        
        logger.info(f"📅 Fetching aggregated session for {len(plan_ids)} active plan(s). User: {user_id}")
        
        # Get aggregated session for today using DailyScheduler
        scheduler = DailyScheduler(db)
        session = await scheduler.schedule_day(
            user_id=PyObjectId(user_id),
            target_date=today,
            plan_ids=plan_ids,  # All active plans
            current_mood=None,
        )
        
        logger.info(f"✅ Aggregated session retrieved for {len(plan_ids)} plans")
        return StudySessionResponse.from_db_model(session)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"❌ Error retrieving aggregated session: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving aggregated session: {str(e)}",
        )


@router.get("/sessions/{session_date}/aggregated", response_model=StudySessionResponse)
async def get_aggregated_session_by_date(
    session_date: str,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get aggregated schedule for a specific date across ALL active plans.
    
    Date format: YYYY-MM-DD
    Returns consolidated tasks from all user's active plans for that date.
    
    Returns 200 with empty session if user has no active plans.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Parse the date
        try:
            target_date = datetime.strptime(session_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )
        
        user_id = ObjectId(current_user.id)
        user_id_str = current_user.id
        
        # Get all active plans for this user
        user_query = {"$or": [{"user_id": user_id}, {"user_id": user_id_str}]}
        active_plans = await db.study_plans.find(
            {**user_query, "status": "active"}
        ).to_list(None)
        
        if not active_plans:
            logger.warning(f"⚠️ No active plans found for user {user_id}")
            # Return empty session (200 OK, not 404)
            empty_session = StudySession(
                plan_id=None,
                user_id=PyObjectId(user_id),
                session_date=target_date,
                start_time=time(9, 0),
                end_time=time(17, 0),
                time_blocks=[],
                aggregated_plan_ids=None,
                mood_at_start=None,
                mood_at_end=None,
                started_at=None,
                completed_at=None,
                actual_duration_mins=None,
                status="scheduled",
                notes="No active study plans found for this user.",
            )
            return StudySessionResponse.from_db_model(empty_session)
        
        # Convert plan IDs to PyObjectId
        plan_ids = [PyObjectId(plan["_id"]) for plan in active_plans]
        
        logger.info(f"📅 Fetching aggregated session for {session_date} ({len(plan_ids)} active plan(s))")
        
        # Get aggregated session for the specified date
        scheduler = DailyScheduler(db)
        session = await scheduler.schedule_day(
            user_id=PyObjectId(user_id),
            target_date=target_date,
            plan_ids=plan_ids,  # All active plans
            current_mood=None,
        )
        
        logger.info(f"✅ Aggregated session retrieved for {len(plan_ids)} plans on {session_date}")
        return StudySessionResponse.from_db_model(session)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"❌ Error retrieving aggregated session: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving aggregated session: {str(e)}",
        )


# ==================== DAILY PROGRESS TRACKING ENDPOINTS ====================
# These endpoints manage daily schedule persistence and progress analytics

@router.get("/progress/daily/{target_date}", response_model=dict)
async def get_daily_progress(
    target_date: str,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get daily progress analytics for a specific date.
    
    Date format: YYYY-MM-DD
    Returns daily completion rate, productivity score, subject performance, etc.
    """
    import logging
    from services.daily_progress_tracker import DailyProgressTracker
    
    logger = logging.getLogger(__name__)
    
    try:
        # Parse the date
        try:
            target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )
        
        user_id = PyObjectId(current_user.id)
        
        logger.info(f"📊 Fetching daily progress for {target_date}")
        
        # Get daily analytics
        tracker = DailyProgressTracker(db)
        analytics = await tracker.compute_daily_analytics(user_id, target_dt)
        
        from models.planner_schemas import DailyProgressAnalyticsResponse
        response = DailyProgressAnalyticsResponse.from_db_model(analytics)
        
        logger.info(f"✅ Daily progress retrieved for {target_date}")
        return response.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"❌ Error retrieving daily progress: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving daily progress: {str(e)}",
        )


@router.get("/progress/graph", response_model=dict)
async def get_daily_progress_graph(
    days: int = 30,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get daily progress data for the past N days for graphing/charting.
    
    Query Parameters:
    - days: Number of days to retrieve (default 30, max 365)
    
    Returns dates, completion rates, productivity scores, focus scores, study time, etc.
    """
    import logging
    from services.daily_progress_tracker import DailyProgressTracker
    
    logger = logging.getLogger(__name__)
    
    try:
        # Validate days parameter
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Days must be between 1 and 365",
            )
        
        user_id = PyObjectId(current_user.id)
        
        logger.info(f"📈 Fetching {days} days of progress graph data")
        
        # Get graph data
        tracker = DailyProgressTracker(db)
        graph_data = await tracker.get_daily_progress_graph_data(user_id, days)
        
        logger.info(f"✅ Progress graph data retrieved for {days} days")
        return graph_data
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"❌ Error retrieving progress graph: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving progress graph: {str(e)}",
        )


@router.get("/schedule/{schedule_date}", response_model=dict)
async def get_daily_schedule(
    schedule_date: str,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get daily schedule for a specific date.
    
    Date format: YYYY-MM-DD
    Returns scheduled tasks, completion status, time tracking, productivity metrics.
    """
    import logging
    from models.planner_schemas import DailyScheduleResponse
    
    logger = logging.getLogger(__name__)
    
    try:
        # Parse the date
        try:
            schedule_dt = datetime.strptime(schedule_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )
        
        user_id = PyObjectId(current_user.id)
        user_id_str = current_user.id
        
        logger.info(f"📅 Fetching schedule for {schedule_date}")
        
        # Convert date to datetime for query
        schedule_datetime = datetime.combine(schedule_dt, time.min)
        
        # Query daily schedule
        user_query = {"$or": [{"user_id": user_id}, {"user_id": user_id_str}]}
        schedule_doc = await db.daily_schedules.find_one({
            **user_query,
            "schedule_date": schedule_datetime,
        })
        
        if not schedule_doc:
            logger.warning(f"⚠️ No schedule found for {schedule_date}")
            # Return empty schedule instead of 404
            from models.planner_schemas import DailySchedule
            empty_schedule = DailySchedule(
                user_id=user_id,
                schedule_date=schedule_dt,
                status="scheduled",
                notes="No schedule for this date",
                session_id=None,
                aggregated_plan_ids=None,
                mood_at_start=None,
                mood_at_end=None,
            )
            response = DailyScheduleResponse.from_db_model(empty_schedule)
            return response.dict()
        
        from models.planner_schemas import DailySchedule, DailyScheduleResponse
        schedule = DailySchedule(**schedule_doc)
        response = DailyScheduleResponse.from_db_model(schedule)
        
        logger.info(f"✅ Schedule retrieved for {schedule_date}")
        return response.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"❌ Error retrieving schedule: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving schedule: {str(e)}",
        )


# ==================== DIAGNOSTIC ENDPOINTS ====================
@router.get("/debug/plan-mismatch/{plan_id}")
async def diagnose_plan_mismatch(
    plan_id: str,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Diagnostic endpoint to help identify why a plan appears in list but not in get.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        user_id_str = current_user.id
        user_id_oid = ObjectId(user_id_str)
        
        logger.info(f"🔍 DIAGNOSTIC: Checking plan {plan_id} for user {user_id_str}")
        
        if not ObjectId.is_valid(plan_id):
            return {
                "error": "Invalid ObjectId format",
                "plan_id_provided": plan_id,
            }
        
        plan_oid = ObjectId(plan_id)
        
        # Check 1: Does plan exist at all?
        plan_exists = await db.study_plans.find_one({"_id": plan_oid})
        logger.info(f"  Check 1 - Plan exists in DB: {plan_exists is not None}")
        
        # Check 2: Does user own it (ObjectId comparison)?
        user_owns_oid = await db.study_plans.find_one(
            {"_id": plan_oid, "user_id": user_id_oid}
        )
        logger.info(f"  Check 2 - User owns (ObjectId): {user_owns_oid is not None}")
        
        # Check 3: Does user own it (String comparison)?
        user_owns_str = await db.study_plans.find_one(
            {"_id": plan_oid, "user_id": user_id_str}
        )
        logger.info(f"  Check 3 - User owns (String): {user_owns_str is not None}")
        
        # Check 4: Does user own it ($or query)?
        user_query = {"$or": [{"user_id": user_id_oid}, {"user_id": user_id_str}]}
        user_owns_or = await db.study_plans.find_one(
            {"_id": plan_oid, **user_query}
        )
        logger.info(f"  Check 4 - User owns ($or): {user_owns_or is not None}")
        
        # Check 5: What's the actual user_id type in the plan?
        if plan_exists:
            actual_user_id = plan_exists.get("user_id")
            logger.info(f"  Check 5 - Actual user_id in plan: {actual_user_id} (type: {type(actual_user_id).__name__})")
            logger.info(f"           Expected ObjectId: {user_id_oid} (type: {type(user_id_oid).__name__})")
            logger.info(f"           Expected String: {user_id_str} (type: {type(user_id_str).__name__})")
        
        return {
            "plan_id": plan_id,
            "user_id": user_id_str,
            "check_1_exists": plan_exists is not None,
            "check_2_owns_objectid": user_owns_oid is not None,
            "check_3_owns_string": user_owns_str is not None,
            "check_4_owns_or": user_owns_or is not None,
            "actual_user_id": str(plan_exists.get("user_id")) if plan_exists else None,
            "plan_summary": {
                "_id": str(plan_exists.get("_id")) if plan_exists else None,
                "user_id": str(plan_exists.get("user_id")) if plan_exists else None,
                "plan_name": plan_exists.get("plan_name") if plan_exists else None,
                "status": plan_exists.get("status") if plan_exists else None,
            } if plan_exists else None,
        }
    
    except Exception as e:
        import traceback
        logger.error(f"Error in diagnostic: {e}\n{traceback.format_exc()}")
        return {"error": str(e)}


# Note: All datetime imports are at the top of the file


# ============================================================================
# USER DEADLINES
# ============================================================================

@router.get("/deadlines", response_model=List[UserDeadlineResponse])
async def list_deadlines(
    days: int = 30,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Return upcoming deadlines for the authenticated user within the next N days."""
    user_id = ObjectId(current_user.id)
    today = datetime.combine(date.today(), time.min)
    cutoff = datetime.combine(date.today() + timedelta(days=days), time.min)
    cursor = db.user_deadlines.find({
        "user_id": user_id,
        "due_date": {"$gte": today, "$lte": cutoff},
    }).sort("due_date", 1)
    docs = await cursor.to_list(None)
    return [UserDeadlineResponse.from_doc(doc) for doc in docs]


@router.post("/deadlines", response_model=UserDeadlineResponse, status_code=201)
async def create_deadline(
    request: CreateDeadlineRequest,
    current_user: UserPublic = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Create a new user deadline."""
    user_id = ObjectId(current_user.id)
    doc = {
        "user_id": user_id,
        "title": request.title,
        "due_date": datetime.combine(request.due_date, time.min),
        "deadline_type": request.deadline_type,
        "description": request.description,
        "completed": False,
        "created_at": datetime.utcnow(),
    }
    result = await db.user_deadlines.insert_one(doc)
    doc["_id"] = result.inserted_id
    return UserDeadlineResponse.from_doc(doc)