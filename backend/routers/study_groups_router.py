from fastapi import APIRouter, Depends, HTTPException, status, Body
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated, List, Optional
from pydantic import BaseModel, Field, EmailStr

# --- Import your core dependencies ---
from core.db import get_database
from core.security import get_current_user
from models.user_schemas import UserInDB, PyObjectId

# --- Import our new group models and services ---
from models.study_groups_schemas import (
    StudyGroupCreate, StudyGroupInDB, StudyGroupPublic, GroupMemberPublic
)
from models.forum_schemas import ForumThreadPublic # For the group threads endpoint
from services import study_groups_service
from services import forum_service # For the group threads endpoint

router = APIRouter(
    prefix="/groups",
    tags=["Study Groups"],
    dependencies=[Depends(get_current_user)] # Secure all routes
)

# --- Pydantic model for the transfer ownership payload ---
class TransferAdminRequest(BaseModel):
    new_admin_id: PyObjectId

class InviteMemberRequest(BaseModel):
    email: EmailStr # Use EmailStr for validation
# --- (END ADD) ---

# --- Use Case 19: Create & Manage Groups ---

@router.post(
    "/", 
    response_model=StudyGroupPublic, 
    status_code=status.HTTP_201_CREATED
)
async def create_new_group(
    group_data: StudyGroupCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Create a new study group. The creator is set as the admin. (FR 19.1)
    """
    return await study_groups_service.create_group(db, group_data, user)

@router.post("/{group_id}/transfer", response_model=StudyGroupPublic)
async def transfer_group_ownership(
    group_id: PyObjectId,
    request_body: TransferAdminRequest,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Transfer admin ownership to another member (Admin only).
    """
    return await study_groups_service.transfer_ownership(
        db, group_id, request_body.new_admin_id, user
    )

@router.delete("/{group_id}/kick/{user_to_kick_id}", status_code=status.HTTP_204_NO_CONTENT)
async def kick_group_member(
    group_id: PyObjectId,
    user_to_kick_id: PyObjectId,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Kick a member from a group (Admin only). (FR 19.3)
    """
    success = await study_groups_service.kick_member(db, group_id, user_to_kick_id, user)
    if not success:
        # Service layer raises HTTPExceptions, but as a fallback:
        raise HTTPException(status_code=500, detail="Failed to kick member")
    return None

# --- Use Case 20: Join & View Groups ---

@router.get("/me", response_model=List[StudyGroupPublic])
async def get_my_groups(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Get a list of all study groups the current user is a member of. (FR 20.3)
    """
    return await study_groups_service.get_user_groups(db, user.id)

@router.post("/{group_id}/join", response_model=StudyGroupPublic)
async def join_a_group(
    group_id: PyObjectId,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Join a study group. (FR 20.1, 20.2)
    """
    return await study_groups_service.join_group(db, group_id, user.id)

@router.delete("/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_a_group(
    group_id: PyObjectId,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Leave a study group (non-admins only).
    """
    success = await study_groups_service.leave_group(db, group_id, user.id)
    if not success:
        # Service layer raises HTTPExceptions, but as a fallback:
        raise HTTPException(status_code=500, detail="Failed to leave group")
    return None

# --- Group Chat Endpoint (FR 19.4) ---

@router.get("/{group_id}/threads", response_model=List[ForumThreadPublic])
async def get_group_threads(
    group_id: PyObjectId,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Get all threads for a specific group.
    Checks group membership. (FR 19.4)
    """
    # This now calls the correct, secure function
    return await forum_service.get_threads_for_group(db, group_id, user.id)

# ... (after your create_new_group route) ...

@router.post("/{group_id}/invite", status_code=status.HTTP_200_OK)
async def invite_member_to_group(
    group_id: PyObjectId,
    request_body: InviteMemberRequest,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Invite a new member to a group by their email (Admin only). (FR 19.2)
    """
    success = await study_groups_service.invite_member(
        db, group_id, request_body.email, user
    )
    if not success:
        # Service layer raises HTTPExceptions
        raise HTTPException(status_code=500, detail="Failed to invite member")
    
    return {"message": "User invited successfully"}

# ... (after your kick_group_member route) ...

@router.get("/{group_id}/members", response_model=List[GroupMemberPublic])
async def get_group_members_list(
    group_id: PyObjectId,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Get the list of all members in a group. (Must be a member)
    (FR 19.3)
    """
    return await study_groups_service.get_group_members(db, group_id, user.id)

# ... (rest of your file) ...