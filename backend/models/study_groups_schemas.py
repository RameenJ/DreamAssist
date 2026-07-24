from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

# --- (This is the v1-style class from your user_schemas.py) ---
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field): 
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler): 
        json_schema = handler(core_schema)
        json_schema.update(type="string", example="507f1f77bcf86cd799439011")
        return json_schema
# --- (End PyObjectId) ---


class StudyGroupBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    admin_id: PyObjectId
    members: List[PyObjectId] = []
    forum_thread_id: PyObjectId # The one-way link

# --- (THIS IS THE FIX) ---
# This class was missing
class StudyGroupCreate(BaseModel):
    # What the user sends
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
# --- (END FIX) ---

class StudyGroupInDB(StudyGroupBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, PyObjectId: str}

# --- Public-facing models (what the API returns) ---
class GroupMemberPublic(BaseModel):
    id: str
    firstname: str
    lastname: str
    image: Optional[str] = None
    
    class Config:
        from_attributes = True

class StudyGroupPublic(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    admin_id: str
    member_count: int
    created_at: datetime
    forum_thread_id: str
    
    class Config:
        from_attributes = True