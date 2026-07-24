# backend/services/activity_service.py

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import Optional


ACTIVITY_LOG_COLLECTION = "user_activities"


async def log_activity(
    db: AsyncIOMotorDatabase,
    user_id: ObjectId,
    activity_type: str,
    book_id: Optional[ObjectId] = None,
    topic_id: Optional[ObjectId] = None,
    metadata: Optional[dict] = None
):
    """
    Log user activity for progress tracking.
    
    Args:
        db: Database connection
        user_id: User's ObjectId
        activity_type: Type of activity (e.g., 'summarize', 'flashcards', 'chat', 'quiz_generate', 'study_notes', 'qna')
        book_id: Optional book ObjectId
        topic_id: Optional topic ObjectId
        metadata: Optional additional data (e.g., question count, flashcard count)
    """
    activity_doc = {
        "user_id": user_id,
        "activity_type": activity_type,
        "timestamp": datetime.utcnow(),
    }
    
    if book_id:
        activity_doc["book_id"] = book_id
    if topic_id:
        activity_doc["topic_id"] = topic_id
    if metadata:
        activity_doc["metadata"] = metadata
    
    await db[ACTIVITY_LOG_COLLECTION].insert_one(activity_doc)
    print(f"INFO: Logged activity '{activity_type}' for user {user_id}")


async def get_user_activity_count(
    db: AsyncIOMotorDatabase,
    user_id: ObjectId,
    activity_type: Optional[str] = None
) -> int:
    """
    Get count of activities for a user, optionally filtered by type.
    """
    query = {"user_id": user_id}
    if activity_type:
        query["activity_type"] = activity_type
    
    count = await db[ACTIVITY_LOG_COLLECTION].count_documents(query)
    return count


async def get_activity_stats_by_type(
    db: AsyncIOMotorDatabase,
    user_id: ObjectId
) -> dict:
    """
    Get activity counts grouped by type for a user.
    Returns dict like: {"summarize": 5, "flashcards": 10, "chat": 15, ...}
    """
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$activity_type",
            "count": {"$sum": 1}
        }}
    ]
    
    results = {}
    cursor = db[ACTIVITY_LOG_COLLECTION].aggregate(pipeline)
    async for doc in cursor:
        results[doc["_id"]] = doc["count"]
    
    return results
