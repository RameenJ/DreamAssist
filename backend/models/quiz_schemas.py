# backend/models/quiz_schemas.py

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from bson import ObjectId

# Import the PyObjectId helper from your existing book schemas
from .book_schemas import PyObjectId
from .ai_schemas import EvaluatedQuestionResult # Reuse this schema

# This is the schema for the document that will be stored in MongoDB
class QuizResultInDB(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(...)
    book_id: PyObjectId = Field(...)
    topic_name: str = Field(..., min_length=1)
    total_score: float = Field(...)
    total_grade: str = Field(...)
    results: List[EvaluatedQuestionResult] # Embed the detailed results
    attempted_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}