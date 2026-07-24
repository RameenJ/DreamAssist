#learn-ease-fyp\backend\routers\user_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user_schemas import UserPublic, UserUpdate, UserInDB, UserPasswordChange, MoodLogCreate, MoodLogResponse, MoodHistoryResponse # UserInDB for current_user type
from services import user_service
from core.db import get_database
from core.security import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)] # Protect all user routes
)

@router.get("/me", response_model=UserPublic)
async def read_users_me(
    current_user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Get current logged-in user's public profile.
    """
    # get_current_user already returns UserInDB. We just convert it to UserPublic.
    return UserPublic.from_user_in_db(current_user)

@router.put("/me", response_model=UserPublic)
async def update_current_user_profile(
    user_update_data: UserUpdate,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    """
    Update current logged-in user's profile details.
    """
    updated_user_db = await user_service.update_user_profile(
        db=db, user_id=current_user.id, user_update_data=user_update_data
    )
    if not updated_user_db:
        # This might happen if the user_id from token is somehow invalid, though get_current_user should catch it
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or update failed.")
    
    return UserPublic.from_user_in_db(updated_user_db)

@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def update_current_user_password(
    password_data: UserPasswordChange,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    """
    Change current logged-in user's password.
    """
    try:
        success = await user_service.change_user_password(
            db=db, user=current_user, password_data=password_data
        )
        # If change_user_password raises an HTTPException, it will propagate.
        # If it returns True, it means success.
        if success:
            return None # For 204 No Content
        else:
            # This 'else' case should ideally not be hit if the service function
            # raises HTTPExceptions for specific failures or returns True on success.
            # However, as a fallback:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password update reported failure without a specific error."
            )

    except HTTPException as he:
        raise he # Re-raise specific HTTPExceptions from the service
    except Exception as e:
        # Log the detailed error on the server for diagnostics
        print(f"ERROR: /users/me/change-password endpoint - Unexpected error: {type(e).__name__} - {e}")
        # Return a generic error response to the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while changing the password."
        )
    
    # ... (at the end of the file) ...
@router.get("/search", response_model=List[UserPublic])
async def search_for_users(
    q: str, # The search query
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Search for users by name to start a new chat.
    """
    if len(q) < 2:
        # Don't search for just one letter
        return []
        
    return await user_service.search_users(db, q, current_user.id)

@router.post("/me/mood-log", response_model=MoodLogResponse)
async def log_daily_mood(
    mood_data: MoodLogCreate,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    """
    Log user's daily mood. Only one mood per day allowed.
    """
    result = await user_service.log_user_mood(db, current_user.id, mood_data.mood)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    return result

@router.get("/me/mood-log/today")
async def check_mood_logged_today(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    """
    Check if user has already logged mood today.
    Returns: {logged: true/false, mood: "emotion" or null}
    """
    return await user_service.get_today_mood(db, current_user.id)

@router.delete("/me/mood-log/today", status_code=status.HTTP_204_NO_CONTENT)
async def delete_today_mood(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    """
    Delete today's mood log (for testing purposes).
    """
    await user_service.delete_today_mood(db, current_user.id)
    return None

@router.get("/me/mood-log/history", response_model=MoodHistoryResponse)
async def get_mood_history(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    days: int = 7,
):
    """
    Get user's mood history for the last N days.
    Query parameter: days (default: 7, can be 7, 14, 30, etc.)
    """
    return await user_service.get_mood_history(db, current_user.id, days)