#learn-ease-fyp\backend\models\book_schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

from .user_schemas import PyObjectId

class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    original_filename: Optional[str] = None
    content_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    subject: Optional[str] = None  # e.g., "Mathematics", "Physics", etc.

class BookCreateInternal(BookBase):
    user_id: PyObjectId
    stored_filename: str
    file_path_local: str
    extracted_text_path_local: Optional[str] = None
    subject_id: Optional[PyObjectId] = None

class BookInDB(BookCreateInternal):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    status: str = "processing" # This field is essential for the background task

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

class BookPublic(BaseModel): # Data returned to client
    id: str
    title: str
    filename: Optional[str] = None
    upload_date: str
    subject_id: Optional[str] = None
    status: str # <<< NEW FIELD FOR UI STATUS
    subject: Optional[str] = None  # Subject of the book

    @classmethod
    def from_db_model(cls, db_book: BookInDB):
        return cls(
            id=str(db_book.id),
            title=db_book.title,
            filename=db_book.original_filename,
            upload_date=db_book.upload_date.isoformat(),
            subject_id=str(db_book.subject_id) if db_book.subject_id else None,
            status=db_book.status, # <<< POPULATE NEW FIELD
            subject=db_book.subject  # Include subject in response
        )

# Schema for updating a book's category
class BookSubjectUpdate(BaseModel):
    subject_id: Optional[str] = Field(default=None, description="The new subject ID for the book. Null to make it uncategorized.")

# ... (all existing code from BookCategoryUpdate)

# --- New Schemas for Book Topics ---


class BookTopicBase(BaseModel):
    """Base model for a book topic, extracted from ToC."""
    book_id: PyObjectId = Field(...)
    topic_title: str = Field(..., min_length=1)
    page_start: int = Field(..., ge=0)
    page_end: Optional[int] = Field(default=None, ge=0)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }


class BookTopicCreate(BookTopicBase):
    """Schema used when first creating the topic in the service."""
    content: str = Field(..., min_length=1)

class BookTopicInDB(BookTopicCreate):
    """Full database model for a book topic."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BookTopicPublic(BaseModel):
    """Schema for topic data returned to the client (excludes full content)."""
    id: str
    book_id: str
    topic_title: str
    page_start: int

    @classmethod
    def from_db_model(cls, db_topic: BookTopicInDB):
        return cls(
            id=str(db_topic.id),
            book_id=str(db_topic.book_id),
            topic_title=db_topic.topic_title,
            page_start=db_topic.page_start
        )