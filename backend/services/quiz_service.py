# backend/services/quiz_service.py

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Dict, Any

from models.quiz_schemas import QuizResultInDB
from models.ai_schemas import QuizEvaluationResponse

QUIZ_RESULTS_COLLECTION = "quiz_results"

async def create_quiz_result(
    db: AsyncIOMotorDatabase,
    user_id: ObjectId,
    book_id: ObjectId,
    topic_name: str,
    eval_response: QuizEvaluationResponse
) -> QuizResultInDB:
    """Saves a completed quiz evaluation to the database."""
    
    quiz_result_doc = QuizResultInDB(
        user_id=user_id,  # type: ignore
        book_id=book_id,  # type: ignore
        topic_name=topic_name,
        total_score=eval_response.total_score,
        total_grade=eval_response.total_grade,
        results=eval_response.results
    )

    # Convert to a dict for MongoDB insertion with mode='python' to preserve ObjectIds
    doc_to_insert = quiz_result_doc.model_dump(by_alias=True, mode='python')
    
    # Ensure ObjectId fields remain as ObjectIds, not strings
    if "_id" not in doc_to_insert:
        doc_to_insert["_id"] = ObjectId()
    if "user_id" in doc_to_insert and isinstance(doc_to_insert["user_id"], str):
        doc_to_insert["user_id"] = ObjectId(doc_to_insert["user_id"])
    if "book_id" in doc_to_insert and isinstance(doc_to_insert["book_id"], str):
        doc_to_insert["book_id"] = ObjectId(doc_to_insert["book_id"])
    
    await db[QUIZ_RESULTS_COLLECTION].insert_one(doc_to_insert)
    
    print(f"INFO: Saved quiz result for user {user_id} on book {book_id}")
    return quiz_result_doc

async def get_all_quiz_results_for_user(
    db: AsyncIOMotorDatabase,
    user_id: ObjectId
) -> List[Dict[str, Any]]:
    """Retrieves all quiz results for a specific user."""
    cursor = db[QUIZ_RESULTS_COLLECTION].find({"user_id": user_id}).sort("attempted_at", -1)
    results = []
    async for doc in cursor:
        # Convert ObjectIds to strings for JSON serialization
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        doc["book_id"] = str(doc["book_id"])
        results.append(doc)
    return results


async def get_quiz_results_by_topic(
    db: AsyncIOMotorDatabase,
    user_id: ObjectId
) -> List[Dict[str, Any]]:
    """Retrieves quiz results grouped by topic for a specific user."""
    cursor = db[QUIZ_RESULTS_COLLECTION].find({"user_id": user_id}).sort("attempted_at", -1)
    results = []
    async for doc in cursor:
        # Convert ObjectIds to strings for JSON serialization
        doc["_id"] = str(doc["_id"])
        doc["user_id"] = str(doc["user_id"])
        doc["book_id"] = str(doc["book_id"])
        results.append(doc)
    return results

