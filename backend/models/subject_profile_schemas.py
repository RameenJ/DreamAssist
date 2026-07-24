# backend/models/subject_profile_schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# === Diagnostic Quiz Schemas ===

class DiagnosticQuestion(BaseModel):
    """A single diagnostic quiz question"""
    question: str
    options: List[str]  # List of 4 options
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the time complexity of accessing an element in an array?",
                "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"]
            }
        }

class DiagnosticQuizRequest(BaseModel):
    """Request to generate a diagnostic quiz for a subject"""
    subject: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Data Structures"
            }
        }

class DiagnosticQuizResponse(BaseModel):
    """Response containing generated quiz questions"""
    subject: str
    questions: List[DiagnosticQuestion]
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Data Structures",
                "questions": []
            }
        }

class DiagnosticQuizAnswer(BaseModel):
    """User's answer to a diagnostic quiz"""
    subject: str
    answers: List[str]  # List of 5 user answers
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Data Structures",
                "answers": ["O(1)", "O(n)", "Stack", "LIFO", "Array"]
            }
        }

class DiagnosticQuizResult(BaseModel):
    """AI evaluation result from diagnostic quiz"""
    level: str  # beginner, intermediate, advanced
    study_pace: str  # slow, moderate, fast
    study_style: str  # theory-focused, practice-focused, mixed, visual, problem-solving based
    break_preference: str  # e.g., "10 min after 45 min"
    
    class Config:
        json_schema_extra = {
            "example": {
                "level": "intermediate",
                "study_pace": "moderate",
                "study_style": "practice-focused",
                "break_preference": "10 min after 45 min"
            }
        }

# === Subject Profile Management Schemas ===

class SubjectProfileCreate(BaseModel):
    """Create a new subject profile (manual entry)"""
    subject: str
    level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    study_pace: str = Field(..., pattern="^(slow|moderate|fast)$")
    study_style: str
    break_preference: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Data Structures",
                "level": "intermediate",
                "study_pace": "moderate",
                "study_style": "practice-focused",
                "break_preference": "10 min after 45 min"
            }
        }

class SubjectProfileUpdate(BaseModel):
    """Update an existing subject profile"""
    level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    study_pace: Optional[str] = Field(None, pattern="^(slow|moderate|fast)$")
    study_style: Optional[str] = None
    break_preference: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "level": "advanced",
                "study_pace": "fast"
            }
        }

class SubjectProfileResponse(BaseModel):
    """Response for subject profile"""
    subject: str
    level: str
    study_pace: str
    study_style: str
    break_preference: str
    assessed_at: datetime
    assessment_method: str  # quiz or manual
    
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
