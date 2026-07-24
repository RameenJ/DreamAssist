from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated 

from models.user_schemas import UserPublic # Assuming this is your user model
from models.progress_schemas import BookProgressResponse, GlobalProgressResponse
from services import progress_service
from core.db import get_database 
from core.security import get_current_user # (This is a placeholder path)

router = APIRouter(
    prefix="/progress",
    tags=["Progress & Stats"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/global", response_model=GlobalProgressResponse)
async def get_global_progress(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserPublic, Depends(get_current_user)] # Secure route
):
    """
    Get all global progress stats, chart data, and grades for the
    currently authenticated user.
    """
    if not user.id:
         raise HTTPException(status_code=401, detail="Could not identify user")
         
    return await progress_service.get_global_progress(db=db, user_id=user.id)


@router.get("/book/{book_id}", response_model=BookProgressResponse)
async def get_book_progress(
    book_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserPublic, Depends(get_current_user)] # Secure route
):
    """
    Get all progress stats and topic completion for a single book
    for the currently authenticated user.
    """
    if not user.id:
         raise HTTPException(status_code=401, detail="Could not identify user")

    return await progress_service.get_book_progress(db=db, book_id=book_id, user_id=user.id)