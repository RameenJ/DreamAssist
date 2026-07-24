#learn-ease-fyp\backend\models\subject_schemas.py
from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated
from datetime import datetime
from bson import ObjectId # For MongoDB ObjectId handling

# Assuming PyObjectId is defined in user_schemas.py or a common utility file
# If not, you might need to define or import it appropriately.
# For now, let's assume it's in user_schemas as per previous structure.
from .user_schemas import PyObjectId

class SubjectBase(BaseModel):
    name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=100
        ),
        Field(description="Name of the subject")
    ]


class SubjectCreate(SubjectBase):
    # No extra fields needed from user for simple creation, user_id will be added in service
    pass

class SubjectUpdate(BaseModel):

    name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=100
        ),
        Field(description="Name of the subject")
    ]


class SubjectInDBBase(SubjectBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId = Field(..., description="The ID of the user who owns this subject")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # updated_at: datetime = Field(default_factory=datetime.utcnow) # Optional: for tracking updates

    class Config:
        populate_by_name = True # Pydantic V2 (formerly allow_population_by_field_name)
        arbitrary_types_allowed = True 
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

# This will be the model returned by API endpoints (e.g., when listing subjects)
class SubjectPublic(BaseModel):
    id: str
    name: str
    user_id: str # Keep as str for client
    created_at: str
    # updated_at: Optional[str] = None

    @classmethod
    def from_db_model(cls, db_subject: SubjectInDBBase):
        return cls(
            id=str(db_subject.id),
            name=str(db_subject.name),  # 👈 explicit cast
            user_id=str(db_subject.user_id),
            created_at=db_subject.created_at.isoformat(),
        )
