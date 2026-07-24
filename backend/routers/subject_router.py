#learn-ease-fyp\backend\routers\subject_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Annotated 

from motor.motor_asyncio import AsyncIOMotorDatabase

from models.subject_schemas import SubjectCreate, SubjectPublic, SubjectUpdate
from models.user_schemas import UserInDB # To type hint current_user
from services import subject_service
from core.db import get_database
from core.security import get_current_user

router = APIRouter(
    prefix="/subjects",
    tags=["Subjects"],
    dependencies=[Depends(get_current_user)] # Protect all routes in this router
)

@router.post("", response_model=SubjectPublic, status_code=status.HTTP_201_CREATED)
async def create_new_subject(
    subject_in: SubjectCreate,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    """
    Create a new subject for the current authenticated user.
    """
    try:
        created_subject_db = await subject_service.create_subject(
            db=db, subject_in=subject_in, user_id=current_user.id
        )
        return SubjectPublic.from_db_model(created_subject_db)
    except ValueError as ve: # Catch duplicate subject name error from service
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Log the exception e for server-side details
        print(f"Error creating subject: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create subject.")

@router.get("", response_model=List[SubjectPublic])
async def list_subjects_for_user(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    """
    List all subjects for the current authenticated user.
    """
    try:
        subjects_db = await subject_service.get_subjects_by_user(db=db, user_id=current_user.id)
        return [SubjectPublic.from_db_model(subj) for subj in subjects_db]
    except Exception as e:
        print(f"Error listing subjects: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve subjects.")

@router.put("/{subject_id}", response_model=SubjectPublic)
async def update_existing_subject(
    subject_id: str,
    subject_update_data: SubjectUpdate,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    """
    Update an existing subject's name for the current authenticated user.
    """
    try:
        updated_subject_db = await subject_service.update_subject_name(
            db=db, subject_id_str=subject_id, subject_update=subject_update_data, user_id=current_user.id
        )
        if not updated_subject_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found or you do not have permission to update it.")
        return SubjectPublic.from_db_model(updated_subject_db)
    except ValueError as ve: # Catch duplicate name error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        print(f"Error updating subject {subject_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update subject.")

@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_subject(
    subject_id: str,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    """
    Delete an existing subject for the current authenticated user.
    Books in this subject will become uncategorized.
    """
    try:
        deleted = await subject_service.delete_subject_for_user(
            db=db, subject_id_str=subject_id, user_id=current_user.id
        )
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found or you do not have permission to delete it.")
        return None # For 204 No Content
    except Exception as e:
        print(f"Error deleting subject {subject_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete subject.")
