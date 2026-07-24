# backend/routers/forum_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated, List, Literal, Optional
from pydantic import BaseModel, Field

# --- Import your core dependencies ---
from core.db import get_database
from core.security import get_current_user
from models.user_schemas import UserInDB, PyObjectId

# --- Import our new forum models and service ---
from models.forum_schemas import (
    ForumThreadCreate, ForumThreadPublic,
    ForumPostCreate, ForumPostPublic
)
from services import forum_service

router = APIRouter(
    prefix="/forum",
    tags=["Forum"],
    dependencies=[Depends(get_current_user)] 
)

class VoteRequest(BaseModel):
    vote_type: Literal["upvote", "downvote", "none"]

# --- Use Case 21: Forum Threads ---

@router.post(
    "/threads", 
    response_model=ForumThreadPublic, 
    status_code=status.HTTP_201_CREATED
)
async def create_new_thread(
    thread_data: ForumThreadCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Create a new public forum thread OR a new private group thread. (FR 21.1)
    """
    return await forum_service.create_thread(db, thread_data, user.id)

@router.get("/threads", response_model=List[ForumThreadPublic])
async def get_all_public_threads(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    # (MODIFIED) Added search parameter
    search: Optional[str] = Query(None, min_length=3, description="Search threads by title or content")
):
    """
    Get a list of all *public* forum threads (is_group is False).
    Optionally filters by a search string.
    """
    # We pass the search_query to the service layer
    return await forum_service.get_all_threads(db, search_query=search)

@router.get("/threads/{thread_id}", response_model=ForumThreadPublic)
async def get_single_thread(
    thread_id: PyObjectId,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)] 
):
    """
    Get a single thread by its ID (public or private).
    Checks group membership if private.
    """
    return await forum_service.get_thread_by_id(db, thread_id, user.id)

@router.delete("/threads/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: PyObjectId,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Delete a thread. Only the author can do this.
    """
    success = await forum_service.delete_thread(db, thread_id, user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Thread deletion failed")
    return None

@router.post("/threads/{thread_id}/vote", response_model=dict)
async def vote_on_thread(
    thread_id: PyObjectId,
    vote: VoteRequest,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Vote on a thread. (FR 21.3)
    Checks group membership if private.
    """
    return await forum_service.vote_on_thread(db, thread_id, user.id, vote.vote_type)


# --- Use Case 22: Forum Posts (Replies) ---

@router.post(
    "/threads/{thread_id}/posts", 
    response_model=ForumPostPublic, 
    status_code=status.HTTP_201_CREATED
)
async def create_new_post(
    thread_id: PyObjectId,
    post_data: ForumPostCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Create a new post (reply) on a specific thread. (FR 22.1)
    Checks group membership if private.
    """
    if post_data.thread_id != thread_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thread ID in URL does not match thread ID in payload"
        )
    return await forum_service.create_post(db, post_data, user.id)

@router.get("/threads/{thread_id}/posts", response_model=List[ForumPostPublic])
async def get_posts_for_thread(
    thread_id: PyObjectId,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)] 
):
    """
    Get all posts for a single thread.
    Checks group membership if private.
    """
    # The sorting logic (most upvoted first) is handled inside the service
    return await forum_service.get_posts_for_thread(db, thread_id, user.id)

@router.put("/posts/{post_id}", response_model=ForumPostPublic)
async def edit_post(
    post_id: PyObjectId,
    content: Annotated[str, Body(embed=True, min_length=1)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Edit an existing post. (FR 22.2)
    """
    return await forum_service.edit_post(db, post_id, content, user.id)

@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: PyObjectId,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Delete an existing post. (FR 22.2)
    """
    success = await forum_service.delete_post(db, post_id, user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Post deletion failed")
    return None

@router.post("/posts/{post_id}/vote", response_model=dict)
async def vote_on_post(
    post_id: PyObjectId,
    vote: VoteRequest,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Vote on a post. (FR 22.3)
    Checks group membership if private.
    """
    return await forum_service.vote_on_post(db, post_id, user.id, vote.vote_type)