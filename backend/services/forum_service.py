from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Literal, Dict, Any
from bson import ObjectId
from fastapi import HTTPException, status
from datetime import datetime

# Import models
from models.forum_schemas import (
    ForumThreadCreate, ForumThreadInDB, ForumThreadPublic,
    ForumPostCreate, ForumPostInDB, ForumPostPublic,
    AuthorPublic, PyObjectId
)
from models.user_schemas import UserInDB, UserPublic
from models.study_groups_schemas import StudyGroupInDB 

# Import user_service to get user details
from . import user_service

# --- Collection Constants ---
FORUM_THREADS_COLLECTION = "forum_threads"
FORUM_POSTS_COLLECTION = "forum_posts"
USERS_COLLECTION = "users"
STUDY_GROUPS_COLLECTION = "study_groups" 

VoteType = Literal["upvote", "downvote", "none"]

# --- Helper Functions ---

async def _get_author_public_from_id(db: AsyncIOMotorDatabase, user_id: PyObjectId) -> AuthorPublic:
    user_in_db = await user_service.get_user_by_id(db, ObjectId(user_id))  # type: ignore
    if not user_in_db:
        return AuthorPublic(id=str(user_id), firstname="[Deleted]", lastname="User", image=None)
    
    return AuthorPublic(
        id=str(user_in_db.id),
        firstname=user_in_db.firstname,
        lastname=user_in_db.lastname,
        image=user_in_db.image
    )

async def _populate_thread_public(db: AsyncIOMotorDatabase, thread_in_db: ForumThreadInDB) -> ForumThreadPublic:
    author_details = await _get_author_public_from_id(db, thread_in_db.author_id)
    reply_count = await db[FORUM_POSTS_COLLECTION].count_documents({"thread_id": thread_in_db.id})
    
    return ForumThreadPublic(
        id=str(thread_in_db.id),
        author=author_details,
        title=thread_in_db.title,
        content=thread_in_db.content,
        book_id=str(thread_in_db.book_id) if thread_in_db.book_id else None,
        tags=thread_in_db.tags,
        created_at=thread_in_db.created_at,
        upvote_count=len(thread_in_db.upvotes),
        downvote_count=len(thread_in_db.downvotes),
        reply_count=reply_count,
        is_group=thread_in_db.is_group
    )

async def _populate_post_public(db: AsyncIOMotorDatabase, post_in_db: ForumPostInDB) -> ForumPostPublic:
    author_details = await _get_author_public_from_id(db, post_in_db.author_id)
    
    return ForumPostPublic(
        id=str(post_in_db.id),
        thread_id=str(post_in_db.thread_id),
        parent_id=str(post_in_db.parent_id) if post_in_db.parent_id else None,
        author=author_details,
        content=post_in_db.content,
        created_at=post_in_db.created_at,
        upvote_count=len(post_in_db.upvotes),
        downvote_count=len(post_in_db.downvotes)
    )

async def _check_group_access(db: AsyncIOMotorDatabase, thread: ForumThreadInDB, user_id: PyObjectId):
    if not thread.is_group:
        return True 
    
    group_doc = await db[STUDY_GROUPS_COLLECTION].find_one({"forum_thread_id": thread.id})
    if not group_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent group for this thread not found")
        
    group = StudyGroupInDB(**group_doc)
    
    if user_id not in group.members:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group")
        
    return True

# --- Thread Service Functions ---

async def create_thread(db: AsyncIOMotorDatabase, thread_create: ForumThreadCreate, user_id: PyObjectId) -> ForumThreadPublic:
    thread_data = thread_create.dict(exclude_unset=True) 
    thread_data["author_id"] = user_id
    thread_in_db = ForumThreadInDB(**thread_data)
    
    # Use mode='python' to preserve ObjectIds
    doc_to_insert = thread_in_db.model_dump(by_alias=True, mode='python')
    # Ensure ObjectIds are not converted to strings
    if "author_id" in doc_to_insert and isinstance(doc_to_insert["author_id"], str):
        doc_to_insert["author_id"] = ObjectId(doc_to_insert["author_id"])
    if "book_id" in doc_to_insert and doc_to_insert["book_id"] and isinstance(doc_to_insert["book_id"], str):
        doc_to_insert["book_id"] = ObjectId(doc_to_insert["book_id"])
    
    result = await db[FORUM_THREADS_COLLECTION].insert_one(doc_to_insert)
    
    created_thread_doc = await db[FORUM_THREADS_COLLECTION].find_one({"_id": result.inserted_id})
    created_thread = ForumThreadInDB(**created_thread_doc)  # type: ignore
    return await _populate_thread_public(db, created_thread)

async def get_all_threads(db: AsyncIOMotorDatabase, search_query: Optional[str] = None) -> List[ForumThreadPublic]:
    filter_query: Dict[str, Any] = {"is_group": False}

    if search_query:
        regex_pattern = {"$regex": search_query, "$options": "i"}
        filter_query["$or"] = [
            {"title": regex_pattern},
            {"content": regex_pattern},
            {"tags": regex_pattern}
        ]

    threads_cursor = db[FORUM_THREADS_COLLECTION].find(filter_query).sort("created_at", -1)
    
    populated_threads = []
    async for thread_doc in threads_cursor:
        thread_in_db = ForumThreadInDB(**thread_doc)  # type: ignore
        populated_thread = await _populate_thread_public(db, thread_in_db)
        populated_threads.append(populated_thread)
        
    return populated_threads

async def get_thread_by_id(db: AsyncIOMotorDatabase, thread_id: PyObjectId, user_id: PyObjectId) -> ForumThreadPublic:
    thread_doc = await db[FORUM_THREADS_COLLECTION].find_one({"_id": thread_id})
    if not thread_doc:
        raise HTTPException(status_code=404, detail="Forum thread not found")
    
    thread_in_db = ForumThreadInDB(**thread_doc)
    await _check_group_access(db, thread_in_db, user_id)
    
    return await _populate_thread_public(db, thread_in_db)

async def get_threads_for_group(db: AsyncIOMotorDatabase, group_id: PyObjectId, user_id: PyObjectId) -> List[ForumThreadPublic]:
    group_doc = await db[STUDY_GROUPS_COLLECTION].find_one({"_id": group_id})
    if not group_doc:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group = StudyGroupInDB(**group_doc)
    if user_id not in group.members:
        raise HTTPException(status_code=403, detail="You are not a member of this group")
        
    threads_cursor = db[FORUM_THREADS_COLLECTION].find({"group_id": group_id}).sort("created_at", -1)
    
    populated_threads = []
    async for thread_doc in threads_cursor:
        thread_in_db = ForumThreadInDB(**thread_doc)
        populated_thread = await _populate_thread_public(db, thread_in_db)
        populated_threads.append(populated_thread)
        
    return populated_threads

async def delete_thread(db: AsyncIOMotorDatabase, thread_id: PyObjectId, user_id: PyObjectId) -> bool:
    """
    Deletes a thread and all associated posts (replies).
    Only the author can delete their thread.
    """
    # 1. Fetch thread
    thread_doc = await db[FORUM_THREADS_COLLECTION].find_one({"_id": thread_id})
    if not thread_doc:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    thread = ForumThreadInDB(**thread_doc)

    # 2. Authorization
    if thread.author_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this thread")

    # 3. Cascade Delete: Remove all posts in this thread first
    await db[FORUM_POSTS_COLLECTION].delete_many({"thread_id": thread_id})

    # 4. Delete the thread itself
    result = await db[FORUM_THREADS_COLLECTION].delete_one({"_id": thread_id})
    
    return result.deleted_count == 1

# --- Post Service Functions ---

async def create_post(db: AsyncIOMotorDatabase, post_create: ForumPostCreate, user_id: PyObjectId) -> ForumPostPublic:
    thread_doc = await db[FORUM_THREADS_COLLECTION].find_one({"_id": post_create.thread_id})
    if not thread_doc:
        raise HTTPException(status_code=404, detail="Thread not found.")
    
    thread = ForumThreadInDB(**thread_doc)
    await _check_group_access(db, thread, user_id)

    post_data = post_create.dict(exclude_unset=True)
    post_data["author_id"] = user_id
    
    post_in_db = ForumPostInDB(**post_data)
    # Use mode='python' to preserve ObjectIds
    doc_to_insert = post_in_db.model_dump(by_alias=True, mode='python')
    # Ensure ObjectIds are not converted to strings
    if "author_id" in doc_to_insert and isinstance(doc_to_insert["author_id"], str):
        doc_to_insert["author_id"] = ObjectId(doc_to_insert["author_id"])
    if "thread_id" in doc_to_insert and isinstance(doc_to_insert["thread_id"], str):
        doc_to_insert["thread_id"] = ObjectId(doc_to_insert["thread_id"])
    if "parent_id" in doc_to_insert and doc_to_insert["parent_id"] and isinstance(doc_to_insert["parent_id"], str):
        doc_to_insert["parent_id"] = ObjectId(doc_to_insert["parent_id"])
    
    result = await db[FORUM_POSTS_COLLECTION].insert_one(doc_to_insert)
    created_post_doc = await db[FORUM_POSTS_COLLECTION].find_one({"_id": result.inserted_id})
        
    created_post = ForumPostInDB(**created_post_doc)  # type: ignore
    return await _populate_post_public(db, created_post)

async def get_posts_for_thread(db: AsyncIOMotorDatabase, thread_id: PyObjectId, user_id: PyObjectId) -> List[ForumPostPublic]:
    thread_doc = await db[FORUM_THREADS_COLLECTION].find_one({"_id": thread_id})
    if not thread_doc:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    thread = ForumThreadInDB(**thread_doc)  # type: ignore
    await _check_group_access(db, thread, user_id)
    
    posts_cursor = db[FORUM_POSTS_COLLECTION].find({"thread_id": thread_id})
    
    populated_posts = []
    async for post_doc in posts_cursor:
        post_in_db = ForumPostInDB(**post_doc)
        populated_post = await _populate_post_public(db, post_in_db)
        populated_posts.append(populated_post)
        
    # --- (FIXED) Sorting Logic ---
    # Sorts primarily by Score (Up - Down), secondarily by Newest first
    populated_posts.sort(
        key=lambda p: (p.upvote_count - p.downvote_count, -p.created_at.timestamp()), 
        reverse=True
    )

    return populated_posts

async def edit_post(db: AsyncIOMotorDatabase, post_id: PyObjectId, new_content: str, user_id: PyObjectId) -> ForumPostPublic:
    post_doc = await db[FORUM_POSTS_COLLECTION].find_one({"_id": post_id})
    if not post_doc:
        raise HTTPException(status_code=404, detail="Post not found")
    post = ForumPostInDB(**post_doc)  # type: ignore
    if post.author_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to edit this post")
    await db[FORUM_POSTS_COLLECTION].update_one(
        {"_id": post_id},
        {"$set": {"content": new_content, "created_at": datetime.utcnow()}}
    )
    updated_post_doc = await db[FORUM_POSTS_COLLECTION].find_one({"_id": post_id})
    return await _populate_post_public(db, ForumPostInDB(**updated_post_doc))  # type: ignore


async def delete_post(db: AsyncIOMotorDatabase, post_id: PyObjectId, user_id: PyObjectId) -> bool:
    post_doc = await db[FORUM_POSTS_COLLECTION].find_one({"_id": post_id})
    if not post_doc:
        raise HTTPException(status_code=404, detail="Post not found")
    post = ForumPostInDB(**post_doc)  # type: ignore
    if post.author_id != user_id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this post")
    result = await db[FORUM_POSTS_COLLECTION].delete_one({"_id": post_id})
    return result.deleted_count == 1

# --- Vote Functions (FIXED LOGIC) ---

async def _vote_on_document(db: AsyncIOMotorDatabase, collection_name: str, doc_id: PyObjectId, user_id: PyObjectId, vote_type: VoteType):
    """
    Handles strict toggling logic:
    - If voting 'up' and already upvoted -> Remove upvote (neutral).
    - If voting 'up' and neutral/downvoted -> Add upvote (and remove downvote).
    - If voting 'down' and already downvoted -> Remove downvote (neutral).
    - If voting 'down' and neutral/upvoted -> Add downvote (and remove upvote).
    """
    # 1. Get current state
    doc = await db[collection_name].find_one({"_id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    current_upvotes = doc.get("upvotes", [])
    current_downvotes = doc.get("downvotes", [])
    
    # 2. Determine Update Operations
    update_ops = {}
    
    if vote_type == "upvote":
        if user_id in current_upvotes:
            # User is clicking upvote again -> Toggle OFF
            update_ops = {"$pull": {"upvotes": user_id}}
        else:
            # User is neutral or downvoted -> Toggle ON (and clear downvote)
            update_ops = {
                "$addToSet": {"upvotes": user_id},
                "$pull": {"downvotes": user_id}
            }
            
    elif vote_type == "downvote":
        if user_id in current_downvotes:
            # User is clicking downvote again -> Toggle OFF
            update_ops = {"$pull": {"downvotes": user_id}}
        else:
            # User is neutral or upvoted -> Toggle ON (and clear upvote)
            update_ops = {
                "$addToSet": {"downvotes": user_id},
                "$pull": {"upvotes": user_id}
            }
    
    # 3. Execute Update
    if update_ops:
        await db[collection_name].update_one({"_id": doc_id}, update_ops)
        
    # 4. Return new counts
    updated_doc = await db[collection_name].find_one({"_id": doc_id})
    if not updated_doc:
        raise HTTPException(status_code=404, detail="Document not found after update")
    return len(updated_doc.get("upvotes", [])), len(updated_doc.get("downvotes", []))

async def vote_on_thread(db: AsyncIOMotorDatabase, thread_id: PyObjectId, user_id: PyObjectId, vote_type: VoteType) -> dict:
    thread_doc = await db[FORUM_THREADS_COLLECTION].find_one({"_id": thread_id})
    if not thread_doc:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    await _check_group_access(db, ForumThreadInDB(**thread_doc), user_id)
    
    upvotes, downvotes = await _vote_on_document(db, FORUM_THREADS_COLLECTION, thread_id, user_id, vote_type)
    return {"upvote_count": upvotes, "downvote_count": downvotes}

async def vote_on_post(db: AsyncIOMotorDatabase, post_id: PyObjectId, user_id: PyObjectId, vote_type: VoteType) -> dict:
    post_doc = await db[FORUM_POSTS_COLLECTION].find_one({"_id": post_id})
    if not post_doc:
        raise HTTPException(status_code=404, detail="Post not found")
    
    thread_doc = await db[FORUM_THREADS_COLLECTION].find_one({"_id": post_doc["thread_id"]})
    if not thread_doc:
        raise HTTPException(status_code=404, detail="Parent thread not found")
    
    await _check_group_access(db, ForumThreadInDB(**thread_doc), user_id)
    
    upvotes, downvotes = await _vote_on_document(db, FORUM_POSTS_COLLECTION, post_id, user_id, vote_type)
    return {"upvote_count": upvotes, "downvote_count": downvotes}