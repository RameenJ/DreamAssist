#learn-ease-fyp\backend\models\user_schemas.py
from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator
from pydantic_core import core_schema
from typing import Optional, Any, List, Literal
from bson import ObjectId
from datetime import datetime, date
import re

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v): 
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler): 
        return {"type": "string", "example": "507f1f77bcf86cd799439011"}

# --- Password Validation Logic ---
def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one number.")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~`]", password): # Common special characters
        raise ValueError("Password must contain at least one special character.")
    return password
# --- End Password Validation Logic ---

# --- Mood Logging Classes ---
class MoodLog(BaseModel):
    """Daily mood log entry"""
    mood: str = Field(..., description="Emotion label: confused, frustrated, stressed, motivated, engaged, bored, neutral, confident")
    logged_at: datetime = Field(default_factory=datetime.utcnow)
    date: str = Field(..., description="Date in YYYY-MM-DD format")

class MoodLogCreate(BaseModel):
    """Request to create a mood log"""
    mood: str = Field(..., description="Emotion label")
    
    @field_validator('mood')
    @classmethod
    def validate_mood(cls, value: str) -> str:
        valid_moods = ["confused", "frustrated", "stressed", "motivated", "engaged", "bored", "neutral", "confident"]
        if value.lower() not in valid_moods:
            raise ValueError(f"Mood must be one of: {', '.join(valid_moods)}")
        return value.lower()

class MoodLogResponse(BaseModel):
    """Response after logging mood"""
    success: bool
    message: str
    mood: str
    date: str
    session: Optional[dict] = Field(None, description="Updated aggregated session after mood adjustment")

class MoodHistoryEntry(BaseModel):
    """Single mood history entry"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    mood: str = Field(..., description="Emotion label")
    logged_at: Optional[str] = Field(None, description="Timestamp when mood was logged")

class MoodHistoryResponse(BaseModel):
    """Response with mood history for a date range"""
    mood_logs: List[MoodHistoryEntry] = Field(..., description="List of mood logs for the requested period")
# --- End Mood Logging Classes ---


class UserCreate(BaseModel):
    email: EmailStr
    password: str # We will add a validator for this
    firstname: str = Field(..., min_length=1)
    lastname: str = Field(..., min_length=1)
    age: int = Field(..., gt=0) 
    university_name: str = Field(...)

    # Pydantic V2 validator for password field
    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserLogin(BaseModel):
    email: EmailStr 
    password: str

class UserUpdate(BaseModel):
    firstname: Optional[str] = Field(None, min_length=1)
    lastname: Optional[str] = Field(None, min_length=1)
    age: Optional[int] = Field(None, gt=0)
    university_name: Optional[str] = Field(None)
    image: Optional[str] = None 

    class Config:
        pass


class UserInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    firstname: str
    lastname: str
    email: EmailStr 
    hashed_password: str
    age: Optional[int] = None 
    university_name: Optional[str] = None
    image: Optional[str] = None  
    verified: bool = False
    subject_profiles: List['SubjectProfile'] = Field(default_factory=list)  # NEW: Subject profiles
    mood_logs: List[MoodLog] = Field(default_factory=list)  # NEW: Daily mood logs
    
    # Study Planner & Scheduler fields
    active_plans: List[PyObjectId] = Field(default_factory=list, description="IDs of active study plans")
    study_goal_ids: List[PyObjectId] = Field(default_factory=list, description="IDs of user's study goals")
    plan_mode_preference: str = Field(default="unified", description="Default plan mode: unified or per_subject")
    auto_reschedule_enabled: bool = Field(default=True, description="Auto-adapt schedule based on performance")
    aggressive_adaptation: bool = Field(default=False, description="Aggressively pull future tasks forward on early completion")
    unlocked_personas: List[str] = Field(default_factory=list)  # NEW: Unlocked AI personas
    selected_persona: str = Field(default="newton")  # NEW: Currently selected persona

    class Config:
        populate_by_name = True 
        arbitrary_types_allowed = True 
        json_encoders = {
            ObjectId: str,
            PyObjectId: str 
        }

class UserPublic(BaseModel):
    id: str
    firstname: str
    lastname: str
    email: EmailStr
    age: Optional[int] = None
    university_name: Optional[str] = None
    image: Optional[str] = None  
    verified: bool
    subject_profiles: List['SubjectProfile'] = Field(default_factory=list)  # NEW: Subject profiles
    plan_mode_preference: str = Field(default="unified")
    auto_reschedule_enabled: bool = Field(default=True)
    unlocked_personas: List[str] = Field(default_factory=list)  # NEW: Unlocked AI personas
    selected_persona: str = Field(default="newton")  # NEW: Currently selected persona

    @classmethod
    def from_user_in_db(cls, user_in_db: UserInDB):
        return cls(
            id=str(user_in_db.id),
            firstname=user_in_db.firstname,
            lastname=user_in_db.lastname,
            email=user_in_db.email,
            age=user_in_db.age,
            university_name=user_in_db.university_name,
            image=user_in_db.image,         
            verified=user_in_db.verified,
            subject_profiles=user_in_db.subject_profiles, # Include subject profiles
            plan_mode_preference=user_in_db.plan_mode_preference,
            auto_reschedule_enabled=user_in_db.auto_reschedule_enabled,
            unlocked_personas=user_in_db.unlocked_personas or [],  # Handle missing field
            selected_persona=user_in_db.selected_persona or "newton"  # Handle missing field with default
        )

class UserPasswordChange(BaseModel):
    current_password: str = Field(..., description="The user's current password")
    new_password: str = Field(..., description="The new desired password") # min_length removed here, will be handled by validator
    confirm_new_password: str = Field(..., description="Confirmation of the new password")

    # Pydantic V2 validator for new_password field
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @model_validator(mode='after') 
    def passwords_match(self) -> 'UserPasswordChange':
        pw1 = self.new_password
        pw2 = self.confirm_new_password
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('New password and confirmation password do not match')
        return self

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# === Subject Profile ===
class SubjectProfile(BaseModel):
    """User's learning profile for a specific subject"""
    subject: str
    level: str  # beginner, intermediate, advanced
    study_pace: str  # slow, moderate, fast
    study_style: str  # theory-focused, practice-focused, mixed, visual, problem-solving based
    break_preference: str  # e.g., "10 min after 45 min"
    assessed_at: datetime = Field(default_factory=datetime.utcnow)
    assessment_method: str  # quiz or manual
    weak_topics: list[str] = Field(default_factory=list, description="Topics the user struggled with in recent quiz evaluations.")
    
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


# === User Deadlines (Assignment/Quiz/Exam Dates) ===
class UserDeadline(BaseModel):
    """User-entered deadline for assignments, quizzes, exams, or other tasks"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    title: str = Field(..., description="e.g., 'Math Assignment 3', 'Chemistry Midterm'")
    due_date: date = Field(..., description="Date of deadline (stored as date, not datetime)")
    deadline_type: Literal["assignment", "quiz", "exam", "other"] = Field(..., description="Type of deadline")
    description: Optional[str] = Field(None, description="Optional additional details")
    completed: bool = Field(default=False, description="Whether the deadline has been marked as completed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            PyObjectId: str,
            date: lambda d: d.isoformat() if d else None,
            datetime: lambda dt: dt.isoformat() if dt else None,
        }


class UserDeadlineCreate(BaseModel):
    """Request body for creating a new deadline"""
    title: str = Field(..., min_length=1, max_length=255)
    due_date: date = Field(...)
    deadline_type: Literal["assignment", "quiz", "exam", "other"] = Field(...)
    description: Optional[str] = Field(None, max_length=1000)


class UserDeadlineUpdate(BaseModel):
    """Request body for updating a deadline"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    due_date: Optional[date] = None
    deadline_type: Optional[Literal["assignment", "quiz", "exam", "other"]] = None
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None
