from fastapi import HTTPException
from typing import List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import your database connection getter
from core.db import get_database

# Import the response models
from models.progress_schemas import (
    BookProgressResponse,
    GlobalProgressResponse,
    TopicStatus,
    ChartDataPoint,
    PieChartDataPoint,
    GlobalStats
)

# Import activity service for tracking AI feature usage
from services import activity_service

# Define the pass/fail threshold for topic completion
COMPLETION_THRESHOLD = 0.6

async def get_book_progress(db: AsyncIOMotorDatabase, book_id: str, user_id: str) -> BookProgressResponse:
    """
    Calculates all progress metrics for a single book.
    """
    user_obj_id = ObjectId(user_id)
    book_obj_id = ObjectId(book_id)

    # 1. Get Topic Completion Status
    completion_status = await _get_topic_completion(db, book_obj_id, user_obj_id)

    # 2. Get Performance by Topic (Bar Chart)
    performance_by_topic = await _get_performance_by_topic(db, book_obj_id, user_obj_id)

    return BookProgressResponse(
        completion_status=completion_status,
        performance_by_topic=performance_by_topic
    )

async def get_global_progress(db: AsyncIOMotorDatabase, user_id: str) -> GlobalProgressResponse:
    """
    Calculates all progress metrics across all books for a user.
    """
    user_obj_id = ObjectId(user_id)

    # 1. Get Global Stats (Cards)
    stats = await _get_global_stats(db, user_obj_id)

    # 2. Get Score Over Time (Line Chart)
    score_over_time = await _get_score_over_time(db, user_obj_id)

    # 3. Get Performance by Subject (Bar Chart)
    performance_by_subject = await _get_performance_by_subject(db, user_obj_id)
    
    # 4. Get Grade Distribution (Pie Chart)
    grade_distribution = await _get_grade_distribution(db, user_obj_id)

    return GlobalProgressResponse(
        stats=stats,
        score_over_time=score_over_time,
        performance_by_subject=performance_by_subject,
        grade_distribution=grade_distribution
    )

# --- Private Helper Methods ---

async def _get_topic_completion(db: AsyncIOMotorDatabase, book_obj_id: ObjectId, user_obj_id: ObjectId) -> List[TopicStatus]:
    """
    Compares all book topics against all quiz results to generate the
    Topic Completion Checklist (✅ ⚠️ ⬜).
    """
    topics_cursor = db.book_topics.find({"book_id": book_obj_id}, {"topic_title": 1})
    all_topics = await topics_cursor.to_list(length=None)
    
    if not all_topics:
        return []

    results_cursor = db.quiz_results.find(
        {"user_id": user_obj_id, "book_id": book_obj_id},
        {"topic_name": 1, "total_score": 1}
    )
    
    quiz_scores = {}
    async for result in results_cursor:
        topic = result["topic_name"]
        score = result["total_score"]
        if topic not in quiz_scores or score > quiz_scores[topic]:
            quiz_scores[topic] = score

    completion_status: List[TopicStatus] = []
    for topic in all_topics:
        topic_title = topic["topic_title"]
        if topic_title in quiz_scores:
            score = quiz_scores[topic_title]
            status = "completed" if score >= COMPLETION_THRESHOLD else "failed"
            completion_status.append(TopicStatus(topic_title=topic_title, status=status, score=score))
        else:
            completion_status.append(TopicStatus(topic_title=topic_title, status="not_attempted", score=None))
            
    return completion_status

async def _get_performance_by_topic(db: AsyncIOMotorDatabase, book_obj_id: ObjectId, user_obj_id: ObjectId) -> List[ChartDataPoint]:
    """
    Runs an aggregation to get the average score for each topic in a book.
    """
    pipeline = [
        {"$match": {"user_id": user_obj_id, "book_id": book_obj_id}},
        {"$group": {
            "_id": "$topic_name",
            "avg_score": {"$avg": "$total_score"}
        }},
        {"$project": {
            "_id": 0,
            "label": "$_id",
            "value": {"$multiply": ["$avg_score", 100]}
        }},
        {"$sort": {"value": -1}}
    ]
    results_cursor = db.quiz_results.aggregate(pipeline)
    return [ChartDataPoint(**doc) async for doc in results_cursor]

async def _get_global_stats(db: AsyncIOMotorDatabase, user_obj_id: ObjectId) -> GlobalStats:
    """
    Runs multiple queries to get the high-level stat cards.
    """
    total_quizzes = await db.quiz_results.count_documents({"user_id": user_obj_id})

    avg_score_pipeline = [
        {"$match": {"user_id": user_obj_id}},
        {"$group": {
            "_id": None,
            "avg_score": {"$avg": "$total_score"}
        }}
    ]
    avg_result = await db.quiz_results.aggregate(avg_score_pipeline).to_list(length=1)
    average_score = (avg_result[0]["avg_score"] * 100) if avg_result else 0.0

    weakest_subject_pipeline = [
        {"$match": {"user_id": user_obj_id}},
        {"$group": {
            "_id": "$book_id",
            "avg_score": {"$avg": "$total_score"}
        }},
        {"$sort": {"avg_score": 1}},
        {"$limit": 1},
        {"$lookup": {
            "from": "books",
            "localField": "_id",
            "foreignField": "_id",
            "as": "book_details"
        }},
        {"$unwind": {"path": "$book_details", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "name": "$book_details.title"
        }}
    ]
    weakest_result = await db.quiz_results.aggregate(weakest_subject_pipeline).to_list(length=1)
    weakest_subject = weakest_result[0].get("name") if weakest_result and "name" in weakest_result[0] else "N/A"
    
    # Get activity stats for AI features
    activity_stats = await activity_service.get_activity_stats_by_type(db, user_obj_id)
    
    return GlobalStats(
        total_quizzes=total_quizzes,
        average_score=round(average_score, 2),
        weakest_subject=weakest_subject,
        total_ai_chats=activity_stats.get("chat", 0),
        total_summaries=activity_stats.get("summarize", 0),
        total_flashcards=activity_stats.get("flashcards", 0),
        total_study_notes=activity_stats.get("study_notes", 0),
        total_qna=activity_stats.get("qna", 0),
        total_quiz_generated=activity_stats.get("quiz_generate", 0)
    )

async def _get_score_over_time(db: AsyncIOMotorDatabase, user_obj_id: ObjectId) -> List[ChartDataPoint]:
    """
    Gets all quiz scores, sorted by date, for the line chart.
    """
    pipeline = [
        {"$match": {"user_id": user_obj_id}},
        {"$sort": {"attempted_at": 1}},
        {"$project": {
            "_id": 0,
            "label": {"$dateToString": {"format": "%Y-%m-%d", "date": "$attempted_at"}},
            "value": {"$multiply": ["$total_score", 100]}
        }}
    ]
    results_cursor = db.quiz_results.aggregate(pipeline)
    return [ChartDataPoint(**doc) async for doc in results_cursor]

async def _get_performance_by_subject(db: AsyncIOMotorDatabase, user_obj_id: ObjectId) -> List[ChartDataPoint]:
    """
    Gets the average score for each *book* (subject).
    """
    pipeline = [
        {"$match": {"user_id": user_obj_id}},
        {"$group": {
            "_id": "$book_id",
            "avg_score": {"$avg": "$total_score"}
        }},
        {"$lookup": {
            "from": "books",
            "localField": "_id",
            "foreignField": "_id",
            "as": "book_details"
        }},
        {"$unwind": {"path": "$book_details", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "_id": 0,
            "label": "$book_details.title",
            "value": {"$multiply": ["$avg_score", 100]}
        }}
    ]
    results_cursor = db.quiz_results.aggregate(pipeline)
    return [ChartDataPoint(**doc) async for doc in results_cursor if doc.get("label")]

async def _get_grade_distribution(db: AsyncIOMotorDatabase, user_obj_id: ObjectId) -> List[PieChartDataPoint]:
    """
    Counts the occurrences of each 'total_grade' for the pie chart.
    """
    pipeline = [
        {"$match": {"user_id": user_obj_id}},
        {"$group": {
            "_id": "$total_grade",
            "count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "name": "$_id",
            "value": "$count"
        }}
    ]
    results_cursor = db.quiz_results.aggregate(pipeline)
    return [PieChartDataPoint(**doc) async for doc in results_cursor]