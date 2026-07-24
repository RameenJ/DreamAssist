# backend/routers/subject_profile_router.py
"""
Router for subject profile management and diagnostic quiz functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

from models.user_schemas import UserInDB, SubjectProfile
from models.subject_profile_schemas import (
    DiagnosticQuizRequest,
    DiagnosticQuizResponse,
    DiagnosticQuestion,
    DiagnosticQuizAnswer,
    DiagnosticQuizResult,
    SubjectProfileCreate,
    SubjectProfileUpdate,
    SubjectProfileResponse
)
from services import diagnostic_service
from core.db import get_database
from core.security import get_current_user
from bson import ObjectId

router = APIRouter(
    prefix="/subject-profiles",
    tags=["Subject Profiles"],
    dependencies=[Depends(get_current_user)]
)

# Shared quiz storage with diagnostic_router
# Key: f"{user_id}_{subject}", Value: List of questions with correct answers
quiz_storage: Dict[str, List[dict]] = {}


@router.post("/diagnostic-quiz/generate", response_model=DiagnosticQuizResponse)
async def generate_diagnostic_quiz(
    request: DiagnosticQuizRequest,
    current_user: Annotated[UserInDB, Depends(get_current_user)]
):
    """
    Generate a diagnostic quiz with 5 subject-specific questions using AI.
    """
    # Generate questions with Groq + fallback
    questions_data = await diagnostic_service.generate_diagnostic_quiz(request.subject)
    
    # Store quiz with correct answers for later evaluation
    storage_key = f"{current_user.id}_{request.subject}"
    quiz_storage[storage_key] = questions_data
    print(f"INFO: Stored quiz for user {current_user.id}, subject {request.subject}")
    
    questions = [
        DiagnosticQuestion(
            question=q["question"],
            options=q["options"]
        ) for q in questions_data
    ]
    
    return DiagnosticQuizResponse(
        subject=request.subject,
        questions=questions
    )


@router.post("/diagnostic-quiz/evaluate", response_model=SubjectProfileResponse)
async def evaluate_diagnostic_quiz(
    quiz_answer: DiagnosticQuizAnswer,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Evaluate diagnostic quiz answers and save the subject profile to user's account.
    Uses simple scoring: compare user answers to correct answers.
    """
    # Retrieve stored quiz with correct answers
    storage_key = f"{current_user.id}_{quiz_answer.subject}"
    stored_quiz = quiz_storage.get(storage_key)
    
    if not stored_quiz:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz not found. Please generate a new quiz first."
        )
    
    # Validate number of answers
    if len(quiz_answer.answers) != len(stored_quiz):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected {len(stored_quiz)} answers, got {len(quiz_answer.answers)}"
        )
    
    # Score the quiz by comparing answers
    correct_count = 0
    total_questions = len(stored_quiz)
    
    for i, user_answer in enumerate(quiz_answer.answers):
        stored_question = stored_quiz[i]
        # Compare user's answer with correct answer
        if user_answer.strip() == stored_question["correct_answer"].strip():
            correct_count += 1
    
    # Calculate percentage
    score_percentage = (correct_count / total_questions) * 100
    
    print(f"INFO: User {current_user.id} scored {correct_count}/{total_questions} ({score_percentage:.1f}%) on {quiz_answer.subject}")
    
    # Determine level based on score
    if score_percentage < 40:  # 0-1 correct out of 5
        level = "beginner"
        study_pace = "slow"
        study_style = "theory-focused"
        break_preference = "10 min after 30 min"
    elif score_percentage < 70:  # 2-3 correct out of 5
        level = "intermediate"
        study_pace = "moderate"
        study_style = "mixed"
        break_preference = "10 min after 45 min"
    else:  # 4-5 correct out of 5
        level = "advanced"
        study_pace = "fast"
        study_style = "problem-solving based"
        break_preference = "15 min after 60 min"
    
    # Clean up stored quiz
    del quiz_storage[storage_key]
    print(f"INFO: Cleaned up stored quiz for {storage_key}")
    
    # Create subject profile
    subject_profile = SubjectProfile(
        subject=quiz_answer.subject,
        level=level,
        study_pace=study_pace,
        study_style=study_style,
        break_preference=break_preference,
        assessed_at=datetime.utcnow(),
        assessment_method="quiz"
    )
    
    # Check if subject already exists in user's profile
    users_collection = db["users"]
    existing_user = await users_collection.find_one({"_id": ObjectId(current_user.id)})
    
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    subject_profiles = existing_user.get("subject_profiles", [])
    
    # Remove existing profile for this subject if any
    subject_profiles = [
        sp for sp in subject_profiles 
        if sp.get("subject") != quiz_answer.subject
    ]
    
    # Add new profile
    subject_profiles.append(subject_profile.model_dump())
    
    # Update user document
    await users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"subject_profiles": subject_profiles}}
    )
    
    return SubjectProfileResponse(**subject_profile.model_dump())


@router.post("/manual", response_model=SubjectProfileResponse)
async def create_subject_profile_manually(
    profile_data: SubjectProfileCreate,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Manually create a subject profile without taking the quiz.
    """
    # Create subject profile
    subject_profile = SubjectProfile(
        subject=profile_data.subject,
        level=profile_data.level,
        study_pace=profile_data.study_pace,
        study_style=profile_data.study_style,
        break_preference=profile_data.break_preference,
        assessed_at=datetime.utcnow(),
        assessment_method="manual"
    )
    
    # Get user and update profiles
    users_collection = db["users"]
    existing_user = await users_collection.find_one({"_id": ObjectId(current_user.id)})
    
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    subject_profiles = existing_user.get("subject_profiles", [])
    
    # Remove existing profile for this subject if any
    subject_profiles = [
        sp for sp in subject_profiles 
        if sp.get("subject") != profile_data.subject
    ]
    
    # Add new profile
    subject_profiles.append(subject_profile.model_dump())
    
    # Update user document
    await users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"subject_profiles": subject_profiles}}
    )
    
    return SubjectProfileResponse(**subject_profile.model_dump())


@router.get("/", response_model=List[SubjectProfileResponse])
async def get_all_subject_profiles(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Get all subject profiles for the current user.
    """
    users_collection = db["users"]
    user = await users_collection.find_one({"_id": ObjectId(current_user.id)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    subject_profiles = user.get("subject_profiles", [])
    
    return [
        SubjectProfileResponse(**sp) for sp in subject_profiles
    ]


@router.put("/{subject}", response_model=SubjectProfileResponse)
async def update_subject_profile(
    subject: str,
    profile_update: SubjectProfileUpdate,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Update an existing subject profile manually.
    """
    users_collection = db["users"]
    user = await users_collection.find_one({"_id": ObjectId(current_user.id)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    subject_profiles = user.get("subject_profiles", [])
    
    # Find the subject profile
    profile_found = False
    for sp in subject_profiles:
        if sp.get("subject") == subject:
            # Update fields that are provided
            if profile_update.level is not None:
                sp["level"] = profile_update.level
            if profile_update.study_pace is not None:
                sp["study_pace"] = profile_update.study_pace
            if profile_update.study_style is not None:
                sp["study_style"] = profile_update.study_style
            if profile_update.break_preference is not None:
                sp["break_preference"] = profile_update.break_preference
            
            sp["assessed_at"] = datetime.utcnow()
            sp["assessment_method"] = "manual"
            
            profile_found = True
            updated_profile = sp
            break
    
    if not profile_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject profile '{subject}' not found"
        )
    
    # Update user document
    await users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"subject_profiles": subject_profiles}}
    )
    
    return SubjectProfileResponse(**updated_profile)


@router.delete("/{subject}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject_profile(
    subject: str,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Delete a subject profile.
    """
    users_collection = db["users"]
    user = await users_collection.find_one({"_id": ObjectId(current_user.id)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    subject_profiles = user.get("subject_profiles", [])
    
    # Filter out the subject
    original_count = len(subject_profiles)
    subject_profiles = [
        sp for sp in subject_profiles 
        if sp.get("subject") != subject
    ]
    
    if len(subject_profiles) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject profile '{subject}' not found"
        )
    
    # Update user document
    await users_collection.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"subject_profiles": subject_profiles}}
    )
    
    return None
