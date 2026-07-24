# backend/models/forum_schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

# Import PyObjectId from user_schemas to avoid duplicate definitions
from .user_schemas import PyObjectId

# --- Schema for a Reply (a single post) ---

# (MODIFIED) Added parent_id for nested replies
class ForumPostCreate(BaseModel):
    thread_id: PyObjectId
    content: str = Field(..., min_length=1)
    parent_id: Optional[PyObjectId] = None 

# (Unchanged logic, inherits parent_id from Create)
class ForumPostInDB(ForumPostCreate): 
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    author_id: PyObjectId 
    created_at: datetime = Field(default_factory=datetime.utcnow)
    upvotes: List[PyObjectId] = []
    downvotes: List[PyObjectId] = []
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, PyObjectId: str}

# --- Schema for the Main Thread (the question) ---

# (Unchanged)
class ForumThreadCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    content: str = Field(..., min_length=10)
    book_id: Optional[PyObjectId] = None 
    tags: Optional[List[str]] = []
    is_group: bool = Field(default=False)

# (Unchanged)
class ForumThreadInDB(ForumThreadCreate): 
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    author_id: PyObjectId 
    created_at: datetime = Field(default_factory=datetime.utcnow)
    upvotes: List[PyObjectId] = []
    downvotes: List[PyObjectId] = []
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, PyObjectId: str}

# --- Public-facing models (what the API returns) ---

class AuthorPublic(BaseModel):
    id: str
    firstname: str
    lastname: str
    image: Optional[str] = None

# (MODIFIED) Added parent_id so frontend can nest threads
class ForumPostPublic(BaseModel):
    id: str
    thread_id: str
    parent_id: Optional[str] = None
    author: AuthorPublic
    content: str
    created_at: datetime
    upvote_count: int
    downvote_count: int
    
    class Config:
        from_attributes = True

class ForumThreadPublic(BaseModel):
    id: str
    author: AuthorPublic
    title: str
    content: str
    book_id: Optional[str] = None
    tags: Optional[List[str]] = []
    created_at: datetime
    upvote_count: int
    downvote_count: int
    reply_count: int = 0 
    is_group: bool
    
    class Config:
        from_attributes = True