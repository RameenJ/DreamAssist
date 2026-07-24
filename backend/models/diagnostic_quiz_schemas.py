# backend/models/diagnostic_quiz_schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from .book_schemas import PyObjectId

# === DIAGNOSTIC QUIZ GENERATION ===

class DiagnosticQuizRequest(BaseModel):
    """Request to generate diagnostic quiz for a subject"""
    subject: str = Field(..., min_length=1, description="The subject name (e.g., 'Data Structures', 'Calculus')")

class DiagnosticQuestion(BaseModel):
    """A single diagnostic question"""
    question: str
    options: List[str] = Field(..., min_items=2, max_items=6)

class DiagnosticQuestionWithAnswer(BaseModel):
    """Internal model: Question with correct answer (not sent to frontend)"""
    question: str
    options: List[str] = Field(..., min_items=2, max_items=6)
    correct_answer: str = Field(..., description="The correct answer text")
    
class DiagnosticQuizResponse(BaseModel):
    """Generated diagnostic quiz response"""
    subject: str
    questions: List[DiagnosticQuestion]

# === DIAGNOSTIC QUIZ EVALUATION ===

class DiagnosticAnswer(BaseModel):
    """User's answer to a diagnostic question"""
    question: str
    user_answer: str

class DiagnosticQuizSubmission(BaseModel):
    """User submits answers to diagnostic quiz"""
    subject: str
    answers: List[DiagnosticAnswer]

class DiagnosticQuizResult(BaseModel):
    """Result from diagnostic quiz evaluation"""
    level: str = Field(..., description="beginner, intermediate, or advanced")
    study_pace: str = Field(..., description="slow, moderate, or fast")
    study_style: str = Field(..., description="theory-focused, practice-focused, mixed, visual, or problem-solving based")
    break_preference: str = Field(..., description="e.g., '10 min after 45 min'")

# === MANUAL LEVEL SETTING ===

class ManualLevelSetting(BaseModel):
    """User manually sets their level for a subject"""
    subject: str = Field(..., min_length=1)
    level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    study_pace: Optional[str] = Field(None, pattern="^(slow|moderate|fast)$")
    study_style: Optional[str] = Field(None, pattern="^(theory-focused|practice-focused|mixed|visual|problem-solving based)$")
    break_preference: Optional[str] = None

# === SUBJECT PROFILE (stored in user document) ===

class SubjectProfile(BaseModel):
    """User's profile for a specific subject"""
    subject: str
    level: str  # beginner, intermediate, advanced
    study_pace: str  # slow, moderate, fast
    study_style: str  # theory-focused, practice-focused, mixed, visual, problem-solving based
    break_preference: str  # e.g., "10 min after 45 min"
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    assessment_method: str = Field(..., description="quiz or manual")
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Data Structures",
                "level": "intermediate",
                "study_pace": "moderate",
                "study_style": "practice-focused",
                "break_preference": "10 min after 45 min",
                "assessed_at": "2024-01-15T10:30:00",
                "assessment_method": "quiz"
            }
        }
