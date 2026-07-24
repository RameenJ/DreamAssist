# backend/routers/diagnostic_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from models.diagnostic_quiz_schemas import (
    DiagnosticQuizRequest,
    DiagnosticQuizResponse,
    DiagnosticQuestion,
    DiagnosticQuizSubmission,
    DiagnosticQuizResult,
    ManualLevelSetting
)
from models.user_schemas import UserInDB, SubjectProfile
from services import diagnostic_service, user_service
from core.db import get_database
from core.security import get_current_user

router = APIRouter(
    prefix="/diagnostic",
    tags=["Diagnostic Quiz"],
    dependencies=[Depends(get_current_user)]
)

# Temporary storage for quiz answers (in production, use Redis or database)
# Key: f"{user_id}_{subject}", Value: List of questions with correct answers
quiz_storage: Dict[str, List[Dict]] = {}


@router.post("/generate-quiz", response_model=DiagnosticQuizResponse)
async def generate_diagnostic_quiz(
    request: DiagnosticQuizRequest,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Generate a diagnostic quiz for a specific subject.
    
    This is typically called after user registration to assess their skill level.
    """
    try:
        # Call diagnostic service to generate questions (Groq + fallback)
        questions_data = await diagnostic_service.generate_diagnostic_quiz(request.subject)
        
        if not questions_data or len(questions_data) != 5:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate exactly 5 questions. Please try again."
            )
        
        # Store quiz with correct answers for later evaluation
        storage_key = f"{current_user.id}_{request.subject}"
        quiz_storage[storage_key] = questions_data
        print(f"INFO: Stored quiz for user {current_user.id}, subject {request.subject}")
        
        # Convert to response model (WITHOUT correct answers for frontend)
        questions = [
            DiagnosticQuestion(
                question=q.get("question", ""),
                options=q.get("options", [])
            )
            for q in questions_data
        ]
        
        return DiagnosticQuizResponse(
            subject=request.subject,
            questions=questions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: /diagnostic/generate-quiz - {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate diagnostic quiz."
        )


@router.post("/submit-quiz", response_model=DiagnosticQuizResult)
async def submit_diagnostic_quiz(
    submission: DiagnosticQuizSubmission,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Submit diagnostic quiz answers and receive personalized learning recommendations.
    
    Evaluates answers by comparing with stored correct answers and returns:
    - Skill level (beginner, intermediate, advanced)
    - Recommended study pace
    - Recommended study style
    - Break preference
    """
    try:
        # Retrieve stored quiz with correct answers
        storage_key = f"{current_user.id}_{submission.subject}"
        stored_quiz = quiz_storage.get(storage_key)
        
        if not stored_quiz:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quiz not found. Please generate a new quiz first."
            )
        
        # Validate submission has correct number of answers
        if len(submission.answers) != len(stored_quiz):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Expected {len(stored_quiz)} answers, got {len(submission.answers)}"
            )
        
        # Score the quiz by comparing answers
        correct_count = 0
        total_questions = len(stored_quiz)
        
        for i, user_answer in enumerate(submission.answers):
            stored_question = stored_quiz[i]
            # Compare user's answer with correct answer
            if user_answer.user_answer.strip() == stored_question["correct_answer"].strip():
                correct_count += 1
        
        # Calculate percentage
        score_percentage = (correct_count / total_questions) * 100
        
        print(f"INFO: User {current_user.id} scored {correct_count}/{total_questions} ({score_percentage:.1f}%) on {submission.subject}")
        
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
        
        # Create evaluation result
        evaluation_result = {
            "level": level,
            "study_pace": study_pace,
            "study_style": study_style,
            "break_preference": break_preference
        }
        
        # Create subject profile
        subject_profile = SubjectProfile(
            subject=submission.subject,
            level=evaluation_result["level"],
            study_pace=evaluation_result["study_pace"],
            study_style=evaluation_result["study_style"],
            break_preference=evaluation_result["break_preference"],
            assessed_at=datetime.utcnow(),
            assessment_method="quiz"
        )
        
        # Update user's subject profiles in database
        await user_service.add_or_update_subject_profile(
            db=db,
            user_id=current_user.id,
            subject_profile=subject_profile
        )
        
        return DiagnosticQuizResult(**evaluation_result)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: /diagnostic/submit-quiz - {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate diagnostic quiz."
        )


@router.post("/set-manual-level", status_code=status.HTTP_200_OK)
async def set_manual_level(
    setting: ManualLevelSetting,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)]
):
    """
    Allow user to manually set their skill level for a subject without taking the quiz.
    
    Default values will be used for study_pace, study_style, and break_preference if not provided.
    """
    try:
        # Create subject profile with defaults
        subject_profile = SubjectProfile(
            subject=setting.subject,
            level=setting.level,
            study_pace=setting.study_pace or "moderate",
            study_style=setting.study_style or "mixed",
            break_preference=setting.break_preference or "10 min after 45 min",
            assessed_at=datetime.utcnow(),
            assessment_method="manual"
        )
        
        # Update user's subject profiles
        await user_service.add_or_update_subject_profile(
            db=db,
            user_id=current_user.id,
            subject_profile=subject_profile
        )
        
        return {
            "message": "Subject level set successfully",
            "subject": setting.subject,
            "level": setting.level
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: /diagnostic/set-manual-level - {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set manual level."
        )


@router.get("/my-profiles")
async def get_my_subject_profiles(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
):
    """
    Get all subject profiles for the current user.
    """
    return {
        "subject_profiles": current_user.subject_profiles
    }
