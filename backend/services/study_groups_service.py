from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from datetime import datetime

# Import models
from models.user_schemas import UserInDB, PyObjectId
from models.study_groups_schemas import (
    StudyGroupCreate, StudyGroupInDB, StudyGroupPublic, GroupMemberPublic
)
from models.forum_schemas import ForumThreadCreate
# Import services
from . import user_service
from . import forum_service

# --- Collection Constant ---
STUDY_GROUPS_COLLECTION = "study_groups"

# --- Internal Helper Functions ---

async def _get_group_by_id_internal(db: AsyncIOMotorDatabase, group_id: PyObjectId) -> Optional[StudyGroupInDB]:
    """
    Internal helper to fetch a group by ID.
    """
    group_doc = await db[STUDY_GROUPS_COLLECTION].find_one({"_id": group_id})
    if group_doc:
        return StudyGroupInDB(**group_doc)
    return None

async def _populate_group_public(db: AsyncIOMotorDatabase, group_in_db: StudyGroupInDB) -> StudyGroupPublic:
    """
    Converts a StudyGroupInDB to a StudyGroupPublic, calculating counts.
    """
    return StudyGroupPublic(
        id=str(group_in_db.id),
        name=group_in_db.name,
        description=group_in_db.description,
        admin_id=str(group_in_db.admin_id),
        member_count=len(group_in_db.members),
        created_at=group_in_db.created_at,
        forum_thread_id=str(group_in_db.forum_thread_id)
    )

# --- Public Service Functions ---

async def create_group(db: AsyncIOMotorDatabase, group_create: StudyGroupCreate, user: UserInDB) -> StudyGroupPublic:
    """
    Creates a new study group using your new flow.
    1. Creates the main chat thread.
    2. Creates the group, linking the thread.
    (FR 19.1)
    """
    
    # --- Step 1: Create the Forum Thread ---
    # This thread is the "chat room" for the group.
    thread_create_data = ForumThreadCreate(
        title=f"Chat: {group_create.name}",
        content=f"Welcome to the {group_create.name} study group!",
        is_group=True # This marks it as a group chat
    )
    
    try:
        # We call the forum_service to create the thread, passing the user's ID
        # (This uses .dict() as defined in your working forum_service)
        created_thread = await forum_service.create_thread(db, thread_create_data, user.id)
        main_thread_id = PyObjectId(created_thread.id) # Get the new thread's ID
    except Exception as e:
        # If thread creation fails, we can't create the group.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create the group's chat thread: {e}"
        )

    # --- Step 2: Create the Study Group ---
    group_data = group_create.dict(exclude_unset=True) # Pydantic v1 style
    group_data["admin_id"] = user.id
    group_data["members"] = [user.id] # Creator is the first member
    group_data["forum_thread_id"] = main_thread_id # Add the link
    
    group_in_db = StudyGroupInDB(**group_data)
    
    # Use mode='python' to preserve ObjectIds
    doc_to_insert = group_in_db.model_dump(by_alias=True, mode='python')
    # Ensure ObjectIds are not converted to strings
    if "admin_id" in doc_to_insert and isinstance(doc_to_insert["admin_id"], str):
        doc_to_insert["admin_id"] = ObjectId(doc_to_insert["admin_id"])
    if "forum_thread_id" in doc_to_insert and isinstance(doc_to_insert["forum_thread_id"], str):
        doc_to_insert["forum_thread_id"] = ObjectId(doc_to_insert["forum_thread_id"])
    if "members" in doc_to_insert:
        doc_to_insert["members"] = [ObjectId(m) if isinstance(m, str) else m for m in doc_to_insert["members"]]
    
    result = await db[STUDY_GROUPS_COLLECTION].insert_one(doc_to_insert)
    
    created_group_doc = await db[STUDY_GROUPS_COLLECTION].find_one({"_id": result.inserted_id})
    if not created_group_doc:
        # If this fails, we should ideally delete the thread we just made (orphaned)
        await db[forum_service.FORUM_THREADS_COLLECTION].delete_one({"_id": main_thread_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create group")
        
    created_group = StudyGroupInDB(**created_group_doc)
    
    # --- Step 3: (Optional but good) Link the group_id back to the thread ---
    await db[forum_service.FORUM_THREADS_COLLECTION].update_one(
        {"_id": main_thread_id},
        {"$set": {"group_id": created_group.id}}
    )

    return await _populate_group_public(db, created_group)

async def get_user_groups(db: AsyncIOMotorDatabase, user_id: PyObjectId) -> List[StudyGroupPublic]:
    """
    Gets all groups a user is a member of.
    (FR 20.3)
    """
    groups_cursor = db[STUDY_GROUPS_COLLECTION].find({"members": user_id}).sort("name", 1) # Sort A-Z
    
    populated_groups = []
    async for group_doc in groups_cursor:
        group_in_db = StudyGroupInDB(**group_doc)
        populated_group = await _populate_group_public(db, group_in_db)
        populated_groups.append(populated_group)
        
    return populated_groups

async def join_group(db: AsyncIOMotorDatabase, group_id: PyObjectId, user_id: PyObjectId) -> StudyGroupPublic:
    """
    Adds the current user to a group's member list.
    (FR 20.1, 20.2)
    """
    group = await _get_group_by_id_internal(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    
    if user_id in group.members:
        return await _populate_group_public(db, group) # User is already a member

    await db[STUDY_GROUPS_COLLECTION].update_one(
        {"_id": group_id},
        {"$addToSet": {"members": user_id}} # $addToSet prevents duplicates
    )
    
    updated_group_doc = await db[STUDY_GROUPS_COLLECTION].find_one({"_id": group_id})
    return await _populate_group_public(db, StudyGroupInDB(**updated_group_doc))  # type: ignore

async def leave_group(db: AsyncIOMotorDatabase, group_id: PyObjectId, user_id: PyObjectId) -> bool:
    """
    Removes the current user from a group's member list.
    """
    group = await _get_group_by_id_internal(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if user_id == group.admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Admin cannot leave the group. You must transfer ownership first."
        )
        
    result = await db[STUDY_GROUPS_COLLECTION].update_one(
        {"_id": group_id},
        {"$pull": {"members": user_id}}
    )
    
    return result.modified_count == 1

async def kick_member(db: AsyncIOMotorDatabase, group_id: PyObjectId, user_to_kick_id: PyObjectId, admin_user: UserInDB) -> bool:
    """
    Removes a member from a group (Admin only).
    (FR 19.3)
    """
    group = await _get_group_by_id_internal(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    
    if admin_user.id != group.admin_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the group admin can kick members")
        
    if user_to_kick_id == admin_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin cannot kick themselves")
        
    result = await db[STUDY_GROUPS_COLLECTION].update_one(
        {"_id": group_id},
        {"$pull": {"members": user_to_kick_id}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Group not found during update")
        
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User was not a member of this group")

    return True

async def transfer_ownership(db: AsyncIOMotorDatabase, group_id: PyObjectId, new_admin_id: PyObjectId, admin_user: UserInDB) -> StudyGroupPublic:
    """
    Transfers the admin role to another member of the group (Admin only).
    """
    group = await _get_group_by_id_internal(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    
    if admin_user.id != group.admin_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the group admin can transfer ownership")
        
    if new_admin_id not in group.members:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New admin must be a member of the group")
        
    await db[STUDY_GROUPS_COLLECTION].update_one(
        {"_id": group_id},
        {"$set": {"admin_id": new_admin_id}}
    )
    
    updated_group_doc = await db[STUDY_GROUPS_COLLECTION].find_one({"_id": group_id})
    return await _populate_group_public(db, StudyGroupInDB(**updated_group_doc))  # type: ignore

# ... (all your existing imports and functions like transfer_ownership) ...

# --- (NEW FUNCTION 1: Invite Member) ---
async def invite_member(db: AsyncIOMotorDatabase, group_id: PyObjectId, email_to_invite: str, admin_user: UserInDB):
    """
    Invites a user to a group by their email (Admin only).
    (FR 19.2)
    """
    group = await _get_group_by_id_internal(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    
    # Check for admin permission
    if admin_user.id != group.admin_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the group admin can invite members")
        
    # Find the user to invite
    user_to_invite = await user_service.get_user_by_email(db, email_to_invite)
    if not user_to_invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with email '{email_to_invite}' not found")
        
    # Check if user is already a member
    if user_to_invite.id in group.members:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this group")
        
    # Add the user to the members list
    result = await db[STUDY_GROUPS_COLLECTION].update_one(
        {"_id": group_id},
        {"$addToSet": {"members": user_to_invite.id}} # $addToSet prevents duplicates
    )
    
    if result.modified_count == 0:
        # This shouldn't happen if the user wasn't a member, but good to check
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add user to the group")
    
    return True # Return success

# --- (NEW FUNCTION 2: Get Member List) ---
async def get_group_members(db: AsyncIOMotorDatabase, group_id: PyObjectId, user_id: PyObjectId) -> List[GroupMemberPublic]:
    """
    Gets the list of all members in a group.
    Only a member of the group can view the list.
    (FR 19.3)
    """
    group = await _get_group_by_id_internal(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        
    # Check for membership permission (any member can see the list)
    if user_id not in group.members:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group")
        
    # Fetch all user documents from the 'members' list
    member_ids = group.members
    members_cursor = db[user_service.USERS_COLLECTION].find({"_id": {"$in": member_ids}})
    
    member_list: List[GroupMemberPublic] = []
    async for member_doc in members_cursor:
        member_in_db = UserInDB(**member_doc)
        member_list.append(GroupMemberPublic(
            id=str(member_in_db.id),
            firstname=member_in_db.firstname,
            lastname=member_in_db.lastname,
            image=member_in_db.image
        ))
        
    return member_list