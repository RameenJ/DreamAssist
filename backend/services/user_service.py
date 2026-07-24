# learn-ease-fyp/backend/services/user_service.py
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
from models.user_schemas import UserCreate, UserInDB, UserPublic, UserUpdate, PyObjectId, UserPasswordChange, SubjectProfile, MoodLog
from core.security import get_password_hash, verify_password
from fastapi import HTTPException, status
from datetime import datetime, date, time
import re
import logging

logger = logging.getLogger(__name__)

USERS_COLLECTION = "users" 

async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[UserInDB]:
    user_data = await db[USERS_COLLECTION].find_one({"email": email})
    if user_data:
        return UserInDB(**user_data)
    return None

async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: PyObjectId) -> Optional[UserInDB]:
    user_data = await db[USERS_COLLECTION].find_one({"_id": user_id})
    if user_data:
        return UserInDB(**user_data)
    return None

async def create_user(db: AsyncIOMotorDatabase, user_create: UserCreate) -> UserPublic:
    existing_user = await get_user_by_email(db, email=user_create.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user_create.password)
    
    user_in_db_data = {
        "firstname": user_create.firstname,
        "lastname": user_create.lastname,
        "email": user_create.email,
        "hashed_password": hashed_password,
        "age": user_create.age,
        "university_name": user_create.university_name,
        "image": None,       
        "verified": False,
        "subject_profiles": [],  # Initialize empty subject profiles list
        "mood_logs": []  # Initialize empty mood logs list
    }
    
    result = await db[USERS_COLLECTION].insert_one(user_in_db_data)
    created_user_data = await db[USERS_COLLECTION].find_one({"_id": result.inserted_id})
    if not created_user_data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create user")
        
    user_in_db_obj = UserInDB(**created_user_data)
    return UserPublic.from_user_in_db(user_in_db_obj)

async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> Optional[UserInDB]:
    user = await get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def update_user_profile(
    db: AsyncIOMotorDatabase, 
    user_id: PyObjectId, 
    user_update_data: UserUpdate
) -> Optional[UserInDB]:
    update_data = user_update_data.model_dump(exclude_unset=True)

    if not update_data: 
        current_user_doc = await db[USERS_COLLECTION].find_one({"_id": user_id})
        if current_user_doc:
            return UserInDB(**current_user_doc)
        return None

    result = await db[USERS_COLLECTION].update_one(
        {"_id": user_id},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return None 

    updated_user_doc = await db[USERS_COLLECTION].find_one({"_id": user_id})
    if updated_user_doc:
        return UserInDB(**updated_user_doc)
    return None

# --- Updated Function to Change User Password ---
async def change_user_password(
    db: AsyncIOMotorDatabase,
    user: UserInDB, # Pass the authenticated UserInDB object
    password_data: UserPasswordChange # This model now handles new_password == confirm_new_password
) -> bool:
    """
    Changes the password for a given user.
    The check for new_password matching confirm_new_password is now handled by the UserPasswordChange Pydantic model.
    """
    # 1. Verify the current password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password."
        )

    # 2. Check if new password and confirmation match (This check is GONE - handled by Pydantic model)
    # if password_data.new_password != password_data.confirm_new_password:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="New password and confirmation password do not match."
    #     )
    
    # 3. (Optional but good) Check if the new password is the same as the old one
    if verify_password(password_data.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the old password."
        )

    # 4. Hash the new password
    new_hashed_password = get_password_hash(password_data.new_password)

    # 5. Update the password in the database
    result = await db[USERS_COLLECTION].update_one(
        {"_id": user.id}, 
        {"$set": {"hashed_password": new_hashed_password}}
    )

    if result.modified_count == 1:
        return True
    
    print(f"WARN: Password change for user {user.id} - update_one reported 0 modifications.")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not update password due to an unexpected issue."
    )

# ... (at the end of the file) ...
async def search_users(db: AsyncIOMotorDatabase, name_query: str, current_user_id: PyObjectId) -> List[UserPublic]:
    """
    Searches for users by first or last name, excluding the current user.
    """
    if not name_query:
        return []

    # Case-insensitive regex search
    query_regex = re.compile(f".*{re.escape(name_query)}.*", re.IGNORECASE)
    
    # Search in both firstname and lastname
    search_filter = {
        "_id": {"$ne": current_user_id}, # Exclude self
        "$or": [
            {"firstname": {"$regex": query_regex}},
            {"lastname": {"$regex": query_regex}}
        ]
    }
    
    users_cursor = db[USERS_COLLECTION].find(search_filter).limit(10) # Limit to 10 results
    
    users = []
    async for user_doc in users_cursor:
        users.append(UserPublic.from_user_in_db(UserInDB(**user_doc)))
        
    return users


# === Subject Profile Management ===

async def add_or_update_subject_profile(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    subject_profile: SubjectProfile
) -> bool:
    """
    Add or update a subject profile for a user.
    If a profile for the subject already exists, it will be updated.
    Otherwise, it will be added to the user's subject_profiles list.
    
    Args:
        db: Database connection
        user_id: User's ObjectId
        subject_profile: SubjectProfile object to add or update
    
    Returns:
        True if successful
    """
    try:
        # Check if subject profile already exists
        user = await db[USERS_COLLECTION].find_one(
            {"_id": user_id, "subject_profiles.subject": subject_profile.subject}
        )
        
        if user:
            # Update existing subject profile
            result = await db[USERS_COLLECTION].update_one(
                {
                    "_id": user_id,
                    "subject_profiles.subject": subject_profile.subject
                },
                {
                    "$set": {
                        "subject_profiles.$": subject_profile.model_dump()
                    }
                }
            )
        else:
            # Add new subject profile
            result = await db[USERS_COLLECTION].update_one(
                {"_id": user_id},
                {
                    "$push": {
                        "subject_profiles": subject_profile.model_dump()
                    }
                }
            )
        
        if result.modified_count == 1:
            return True
        
        print(f"WARN: Subject profile add/update for user {user_id} - no modifications made")
        return False
        
    except Exception as e:
        print(f"ERROR: add_or_update_subject_profile - {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subject profile"
        )


async def get_user_subject_profiles(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId
) -> List[SubjectProfile]:
    """
    Get all subject profiles for a user.
    
    Args:
        db: Database connection
        user_id: User's ObjectId
    
    Returns:
        List of SubjectProfile objects
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return []
    
    return user.subject_profiles


async def log_user_mood(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    mood: str
) -> dict:
    """
    Log user's mood and recalculate today's schedule WITHOUT creating a new session.
    
    🎯 CRITICAL ARCHITECTURE CHANGE:
    - Does NOT create new sessions on mood change
    - Does NOT delete existing sessions
    - Instead: Appends mood to moodHistory
    - Then: Recalculates schedule reactively
    - Result: Session ID persists, progress is preserved
    
    Args:
        db: Database connection
        user_id: User's ObjectId
        mood: Emotion label (confused, frustrated, stressed, motivated, engaged, bored, neutral, confident)
    
    Returns:
        Dict with success status, message, mood, date, and updated session if applicable
    """
    # ✅ Validate mood format
    ALLOWED_MOODS = {
        "stressed", "frustrated", "tired", "confused",
        "motivated", "confident", "engaged",
        "bored", "neutral"
    }
    
    normalized_mood = mood.lower()
    if normalized_mood not in ALLOWED_MOODS:
        return {
            "success": False,
            "message": f"Invalid mood '{mood}'. Allowed moods: {', '.join(sorted(ALLOWED_MOODS))}",
            "mood": None,
            "date": datetime.utcnow().date().isoformat()
        }
    
    today_str = datetime.utcnow().date().isoformat()  # YYYY-MM-DD format
    today_date = datetime.utcnow().date()
    
    # Check if user exists
    user = await get_user_by_id(db, user_id)
    if not user:
        return {"success": False, "message": "User not found", "mood": None, "date": today_str}
    
    # Step 1: Add mood log to user's mood_logs (for backward compatibility and analytics)
    new_mood_log = MoodLog(
        mood=normalized_mood,
        logged_at=datetime.utcnow(),
        date=today_str
    )
    
    result = await db[USERS_COLLECTION].update_one(
        {"_id": user_id},
        {"$push": {"mood_logs": new_mood_log.model_dump()}}
    )
    
    if result.modified_count == 0:
        return {"success": False, "message": "Failed to log mood", "mood": None, "date": today_str}
    
    logger.info(f"✅ Mood '{normalized_mood}' added to user's mood_logs")
    
    # === FIX #3: Update session mood_at_start ===
    await update_session_mood_start(db, user_id, normalized_mood, today_date)
    
    # Step 2: Find today's session and recalculate schedule
    session_dict = None
    try:
        # Find existing session for today (should already exist if user accessed schedule)
        existing_session_doc = await db.study_sessions.find_one({
            "user_id": user_id,
            "session_date": datetime.combine(today_date, time.min),
            "plan_id": None,  # aggregated session
        })
        
        if existing_session_doc:
            logger.info(f"🔄 Found existing session {existing_session_doc['_id']} - updating mood_at_start")

            # Only stamp the mood onto the existing session.
            # Calling schedule_day here was the source of the bug: it could fail
            # to locate the session via its plan-id key (if the active-plan set
            # had changed) and then INSERT a brand-new session with fresh,
            # uncompleted time_blocks — silently discarding all completed flags.
            await db.study_sessions.update_one(
                {"_id": existing_session_doc["_id"]},
                {"$set": {"mood_at_start": normalized_mood}},
            )
            existing_session_doc["mood_at_start"] = normalized_mood

            # Serialize via the StudySession model so ObjectIds, dates, and
            # times are all converted to JSON-safe types (same path the
            # original schedule_day call used to follow).
            try:
                from core.datetime_utils import convert_datetime_to_date
                from models.planner_schemas import StudySession
                from services.study_scheduler import convert_times_to_str
                session_doc_clean = convert_datetime_to_date(existing_session_doc)
                session_obj = StudySession(**session_doc_clean)
                session_dict = session_obj.model_dump(by_alias=True, mode='json')
                session_dict = convert_times_to_str(session_dict)
            except Exception as _ser_err:
                logger.warning(f"Could not serialize session for mood-log response: {_ser_err}")
                session_dict = None

        else:
            logger.info(f"ℹ️ No existing session for {today_date} - will be created on next fetch")
            session_dict = None
            
    except Exception as e:
        logger.error(f"❌ Error recalculating session after mood log: {e}", exc_info=True)
        session_dict = None
    
    return {
        "success": True,
        "message": f"Mood '{normalized_mood}' logged successfully! Schedule has been recalculated.",
        "mood": normalized_mood,
        "date": today_str,
        "session": session_dict,
    }


async def get_today_mood(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId
) -> dict:
    """
    Get the latest mood logged today.
    If multiple moods logged on the same day, returns the most recent one.
    
    Args:
        db: Database connection
        user_id: User's ObjectId
    
    Returns:
        Dict with logged status and mood if exists
    """
    today_str = datetime.utcnow().date().isoformat()
    
    user = await get_user_by_id(db, user_id)
    if not user:
        return {"logged": False, "mood": None, "date": today_str}
    
    # Find all mood logs for today and sort by logged_at descending to get the latest
    today_moods = [
        mood_log for mood_log in user.mood_logs
        if mood_log.date == today_str
    ]
    
    if today_moods:
        # Sort by logged_at descending and get the most recent
        today_moods_sorted = sorted(
            today_moods,
            key=lambda x: x.logged_at,
            reverse=True
        )
        latest_mood = today_moods_sorted[0]
        return {
            "logged": True,
            "mood": latest_mood.mood,
            "date": today_str,
            "logged_at": latest_mood.logged_at.isoformat() if latest_mood.logged_at else None
        }
    
    return {"logged": False, "mood": None, "date": today_str}


async def delete_today_mood(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId
) -> bool:
    """
    Delete today's mood log (for testing purposes).
    
    Args:
        db: Database connection
        user_id: User's ObjectId
    
    Returns:
        True if mood was deleted, False otherwise
    """
    today_str = datetime.utcnow().date().isoformat()
    
    # Remove today's mood log using $pull operator
    result = await db[USERS_COLLECTION].update_one(
        {"_id": user_id},
        {"$pull": {"mood_logs": {"date": today_str}}}
    )
    
    return result.modified_count > 0


async def get_mood_history(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    days: int = 7
) -> dict:
    """
    Get user's mood history for the last N days.
    Returns one mood per day - the most recent mood logged for each day.
    
    Args:
        db: Database connection
        user_id: User's ObjectId
        days: Number of days to look back (default: 7)
    
    Returns:
        Dictionary with mood_logs list containing one entry per day (the latest)
    """
    from datetime import timedelta
    
    # Calculate the date N days ago
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    # Fetch user
    user = await db[USERS_COLLECTION].find_one({"_id": user_id})
    
    if not user or "mood_logs" not in user:
        return {"mood_logs": []}
    
    # Group mood logs by date and keep only the latest one per day
    mood_by_date = {}
    for mood_log in user.get("mood_logs", []):
        try:
            log_date = datetime.fromisoformat(mood_log.get("date", "")).date()
            if start_date <= log_date <= end_date:
                # Keep track of the latest mood for each date by comparing logged_at timestamps
                if log_date not in mood_by_date:
                    mood_by_date[log_date] = mood_log
                else:
                    # Compare logged_at timestamps
                    existing_logged_at = mood_by_date[log_date].get("logged_at")
                    new_logged_at = mood_log.get("logged_at")
                    
                    # Handle datetime objects or strings
                    if isinstance(existing_logged_at, str):
                        existing_logged_at = datetime.fromisoformat(existing_logged_at)
                    if isinstance(new_logged_at, str):
                        new_logged_at = datetime.fromisoformat(new_logged_at)
                    
                    # Keep the newer one
                    if new_logged_at and (not existing_logged_at or new_logged_at > existing_logged_at):
                        mood_by_date[log_date] = mood_log
        except (ValueError, AttributeError):
            # Skip invalid date entries
            continue
    
    # Convert to list and sort by date ascending
    mood_logs = []
    for log_date in sorted(mood_by_date.keys()):
        mood_log = mood_by_date[log_date]
        logged_at = mood_log.get("logged_at")
        logged_at_str = logged_at.isoformat() if logged_at else None
        
        mood_logs.append({
            "date": mood_log.get("date"),
            "mood": mood_log.get("mood"),
            "logged_at": logged_at_str
        })
    
    return {"mood_logs": mood_logs}


# === Study Plan Management ===

async def link_plan_to_user(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    plan_id: PyObjectId
) -> bool:
    """
    Link an active study plan to a user.
    
    Args:
        db: Database connection
        user_id: User's ObjectId
        plan_id: Plan's ObjectId
    
    Returns:
        True if successful
    """
    try:
        result = await db[USERS_COLLECTION].update_one(
            {"_id": user_id},
            {"$addToSet": {"active_plans": plan_id}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error linking plan to user: {e}")
        return False


async def unlink_plan_from_user(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    plan_id: PyObjectId
) -> bool:
    """
    Remove a study plan from user's active plans.
    
    Args:
        db: Database connection
        user_id: User's ObjectId
        plan_id: Plan's ObjectId
    
    Returns:
        True if successful
    """
    try:
        result = await db[USERS_COLLECTION].update_one(
            {"_id": user_id},
            {"$pull": {"active_plans": plan_id}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error unlinking plan from user: {e}")
        return False


async def get_user_active_plans(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId
) -> List[PyObjectId]:
    """
    Get all active study plan IDs for a user.
    
    Args:
        db: Database connection
        user_id: User's ObjectId
    
    Returns:
        List of active plan ObjectIds
    """
    try:
        user = await get_user_by_id(db, user_id)
        if user:
            return user.active_plans if user.active_plans else []
        return []
    except Exception as e:
        print(f"Error retrieving active plans: {e}")
        return []


async def add_study_goal(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    goal_id: PyObjectId
) -> bool:
    """
    Add a study goal ID to user's goals.
    
    Args:
        db: Database connection
        user_id: User's ObjectId
        goal_id: Goal's ObjectId
    
    Returns:
        True if successful
    """
    try:
        result = await db[USERS_COLLECTION].update_one(
            {"_id": user_id},
            {"$addToSet": {"study_goal_ids": goal_id}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error adding study goal: {e}")
        return False


async def remove_study_goal(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    goal_id: PyObjectId
) -> bool:
    """
    Remove a study goal from user's goals.
    
    Args:
        db: Database connection
        user_id: User's ObjectId
        goal_id: Goal's ObjectId
    
    Returns:
        True if successful
    """
    try:
        result = await db[USERS_COLLECTION].update_one(
            {"_id": user_id},
            {"$pull": {"study_goal_ids": goal_id}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error removing study goal: {e}")
        return False


async def update_session_mood_start(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    mood: str,
    target_date: Optional[date] = None
) -> dict:
    """
    === FIX #3: Update session mood_at_start from mood log ===
    
    Capture user's mood at the start of the session. Called when a mood is logged.
    This ensures that the session's mood_at_start reflects the user's mood when they begin.
    
    Args:
        db: Database connection
        user_id: User's ObjectId
        mood: Mood string (e.g., "frustrated", "motivated")
        target_date: Date for the session. Defaults to today.
    
    Returns:
        Dict with update status
    """
    if target_date is None:
        target_date = datetime.utcnow().date()
    
    # Normalize mood
    mood_normalized = mood.lower()
    
    # Find the aggregated session for this date (plan_id=None means aggregated)
    session_doc = await db.study_sessions.find_one({
        "user_id": user_id,
        "session_date": datetime.combine(target_date, time.min),
        "plan_id": None,  # aggregated session
    })
    
    if not session_doc:
        logger.info(f"ℹ️ No aggregated session found for {target_date} to update mood_at_start")
        return {"success": False, "message": "Session not found for date"}
    
    # Only update mood_at_start if it's currently null
    if session_doc.get("mood_at_start") is None:
        result = await db.study_sessions.update_one(
            {"_id": session_doc["_id"]},
            {"$set": {"mood_at_start": mood_normalized}}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Updated session mood_at_start to '{mood_normalized}' for {target_date}")
            return {
                "success": True,
                "message": f"Session mood_at_start updated to '{mood_normalized}'",
                "mood_at_start": mood_normalized,
            }
        else:
            logger.warning(f"⚠️ Failed to update mood_at_start for session {session_doc['_id']}")
            return {"success": False, "message": "Failed to update session"}
    else:
        logger.info(f"ℹ️ Session mood_at_start already set to '{session_doc.get('mood_at_start')}' - not overwriting")
        return {
            "success": False,
            "message": f"mood_at_start already set to '{session_doc.get('mood_at_start')}' - not overwriting",
            "mood_at_start": session_doc.get("mood_at_start"),
        }

