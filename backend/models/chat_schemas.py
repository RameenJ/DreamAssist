from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

# Import the PyObjectId and UserPublic from your user_schemas
from .user_schemas import PyObjectId, UserPublic

# --- Schema for a single Message ---

class MessageBase(BaseModel):
    conversation_id: PyObjectId
    sender_id: PyObjectId
    content: str

class MessageCreate(BaseModel):
    conversation_id: PyObjectId
    content: str

class MessageInDB(MessageBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, PyObjectId: str}

# --- Schema for a Conversation ---

class ConversationBase(BaseModel):
    members: List[PyObjectId]

class ConversationInDB(ConversationBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, PyObjectId: str}

# --- Public-facing models (what the API returns) ---

class MessagePublic(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
    created_at: datetime
    
    # --- (THIS IS THE FIX) ---
    # This Config tells Pydantic how to handle 'datetime'
    class Config:
        from_attributes = True 
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}
    # --- (END FIX) ---

class ConversationPublic(BaseModel):
    id: str
    participant: UserPublic
    last_message: Optional[str] = None
    last_activity: datetime
    
    # --- (THIS IS THE FIX) ---
    # This Config tells Pydantic how to handle 'datetime'
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda dt: dt.isoformat()}
    # --- (END FIX) ---

# --- WebSocket Message Types ---
class WebSocketMessage(BaseModel):
    type: str
    payload: dict