#backend\routers\recommendation_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated 
from bson import ObjectId
from models.user_schemas import UserPublic
from models.ai_schemas import AIRecommendationResponse, AIGlobalRecommendationResponse
from services import recommendation_service
from services import progress_service  # <-- We re-use this!
from core.db import get_database 
from core.security import get_current_user

router = APIRouter(
    prefix="/ai",
    tags=["AI Features"],
    dependencies=[Depends(get_current_user)]
)

@router.get(
    "/recommendations/{book_id}", 
    response_model=AIRecommendationResponse,
    summary="Get AI Study Recommendations for a Book"
)
async def get_ai_study_recommendations(
    book_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserPublic, Depends(get_current_user)] # Secure route
):
    """
    Analyzes the user's quiz performance for a specific book and returns
    personalized, AI-generated study recommendations.
    """
    if not user.id:
        raise HTTPException(status_code=401, detail="Could not identify user")

    try:
        user_obj_id = ObjectId(user.id)
        book_obj_id = ObjectId(book_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Book ID or User ID format")

    # 1. Re-use your existing logic to get the performance data
    # We call the helper function directly
    performance_data = await progress_service._get_performance_by_topic(
        db=db, 
        book_obj_id=book_obj_id, 
        user_obj_id=user_obj_id
    )
    
    if not performance_data:
        # Return an empty/default response instead of an error
        return AIRecommendationResponse(recommendations=[], strength_message=None)

    # 2. Pass this data to the new recommendation service
    return await recommendation_service.get_study_recommendations_from_llm(
        performance_data=performance_data
    )


@router.get(
    "/global-recommendations",
    response_model=AIGlobalRecommendationResponse,
    summary="Get AI Global Study Recommendations for Dashboard"
)
async def get_ai_global_recommendations(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserPublic, Depends(get_current_user)]
):
    """
    Analyzes the user's global quiz performance and returns high-level
    AI-generated study recommendations for the main dashboard.
    """
    if not user.id:
        raise HTTPException(status_code=401, detail="Could not identify user")

    # 1. Get the user's global progress stats
    # We can't call a helper here, as get_global_progress builds the whole object
    progress_data = await progress_service.get_global_progress(db=db, user_id=user.id)
    
    if not progress_data:
        raise HTTPException(status_code=404, detail="No progress data found for user.")

    # 2. Pass this data to the new global recommendation service
    return await recommendation_service.get_global_recommendations_from_llm(
        progress_data=progress_data
    )