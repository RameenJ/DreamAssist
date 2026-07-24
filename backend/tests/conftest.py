"""
Test Fixtures and Mock Data for Study Planner Services

This module provides reusable test data and fixtures for unit testing
the study planner services (TaskGenerator, DailyScheduler, AdaptiveTracker).
"""

import pytest
from datetime import datetime, date, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
from mongomock_motor import AsyncMongoMockClient
from typing import Dict, List, Any


@pytest.fixture
def mock_db():
    """
    Fixture providing a mock AsyncIOMotorDatabase using mongomock_motor.
    
    This allows tests to run without a real MongoDB instance.
    """
    client = AsyncMongoMockClient()
    return client.dreamassist_test


@pytest.fixture
def sample_user_id():
    """Sample user ObjectId"""
    return ObjectId()


@pytest.fixture
def sample_plan_id():
    """Sample plan ObjectId"""
    return ObjectId()


@pytest.fixture
def sample_subject_profile(sample_user_id) -> Dict[str, Any]:
    """Sample subject profile with learning preferences"""
    return {
        "user_id": str(sample_user_id),
        "subjects": ["DSA", "Web Development"],
        "topics": {
            "DSA": ["Arrays", "Linked Lists", "Trees", "Graphs"],
            "Web Development": ["HTML", "CSS", "JavaScript", "React"],
        },
        "study_pace": "moderate",  # slow, moderate, fast
        "preferred_study_time": {
            "start_hour": 6,
            "end_hour": 22,
            "peak_hours": [9, 14, 19],
        },
        "break_preference": "25min after 45min",
        "learning_style": "visual",
    }


@pytest.fixture
def sample_quiz_results(sample_user_id) -> Dict[str, Any]:
    """Sample quiz results for performance data"""
    return {
        "user_id": str(sample_user_id),
        "quizzes": {
            "DSA": {
                "Arrays": [70, 75, 80],  # improving
                "Linked Lists": [45, 50, 55],  # weak
                "Trees": [60, 60, 60],  # stable
                "Graphs": [0, 0, 0],  # never attempted
            },
            "Web Development": {
                "HTML": [90, 92, 95],  # strong
                "CSS": [75, 78, 82],  # improving
                "JavaScript": [50, 55, 60],  # weak
                "React": [65, 68, 70],  # moderate
            },
        },
    }


@pytest.fixture
def sample_user_mood_logs(sample_user_id) -> List[Dict[str, Any]]:
    """Sample mood logs for the last 7 days"""
    base_date = datetime.utcnow()
    moods = []
    
    mood_sequence = [
        "motivated", "engaged", "neutral", "tired",
        "stressed", "focused", "motivated"
    ]
    
    for i in range(7):
        moods.append({
            "user_id": str(sample_user_id),
            "timestamp": (base_date - timedelta(days=6-i)).isoformat(),
            "emotion": mood_sequence[i],
            "intensity": 0.5 + (i % 3) * 0.2,  # 0.5 - 0.9
        })
    
    return moods


@pytest.fixture
def sample_study_plan(sample_user_id, sample_plan_id) -> Dict[str, Any]:
    """Sample study plan document"""
    return {
        "_id": sample_plan_id,
        "user_id": str(sample_user_id),
        "subjects": ["DSA", "Web Development"],
        "start_date": datetime.utcnow().date().isoformat(),
        "end_date": (datetime.utcnow().date() + timedelta(days=30)).isoformat(),
        "mode": "unified",  # unified or per_subject
        "status": "active",  # active, paused, completed
        "total_available_hours": 20,
        "study_pace": "moderate",
        "tasks": [],
        "missed_sessions": 0,
        "completion_rate": 0.0,
        "productivity_score": 0.0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_study_session(sample_plan_id, sample_user_id) -> Dict[str, Any]:
    """Sample study session document"""
    session_date = datetime.utcnow().date()
    return {
        "_id": ObjectId(),
        "plan_id": sample_plan_id,
        "user_id": str(sample_user_id),
        "session_date": session_date.isoformat(),
        "time_blocks": [
            {
                "block_id": str(ObjectId()),
                "task_id": str(ObjectId()),
                "subject": "DSA",
                "topic": "Arrays",
                "task_type": "learn",
                "difficulty": 0.6,
                "estimated_time_mins": 45,
                "start_time": "06:00",
                "end_time": "07:00",
                "status": "pending",
                "completed": False,
                "mood_adjustment_applied": False,
            },
            {
                "block_id": str(ObjectId()),
                "task_id": str(ObjectId()),
                "subject": "Web Development",
                "topic": "JavaScript",
                "task_type": "practice",
                "difficulty": 0.5,
                "estimated_time_mins": 60,
                "start_time": "14:00",
                "end_time": "15:15",
                "status": "pending",
                "completed": False,
                "mood_adjustment_applied": False,
            },
        ],
        "mood_at_start": "neutral",
        "mood_at_end": None,
        "completed_blocks": 0,
        "status": "pending",  # pending, in_progress, completed, missed, skipped
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_study_task(sample_user_id) -> Dict[str, Any]:
    """Sample study task document"""
    return {
        "_id": ObjectId(),
        "user_id": str(sample_user_id),
        "subject": "DSA",
        "topic": "Arrays",
        "task_type": "learn",  # learn, revise, practice
        "difficulty": 0.6,
        "estimated_time_mins": 45,
        "priority_score": 0.85,
        "deadline": (datetime.utcnow().date() + timedelta(days=5)).isoformat(),
        "status": "pending",  # pending, scheduled, completed, missed, skipped
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_study_goal(sample_user_id) -> Dict[str, Any]:
    """Sample study goal document"""
    return {
        "_id": ObjectId(),
        "user_id": str(sample_user_id),
        "title": "Master DSA Arrays",
        "description": "Understand and practice array algorithms",
        "subjects": ["DSA"],
        "topics": ["Arrays"],
        "target_completion_date": (datetime.utcnow().date() + timedelta(days=30)).isoformat(),
        "priority": "high",  # low, medium, high
        "status": "in_progress",  # not_started, in_progress, completed
        "progress_percentage": 0,
        "created_at": datetime.utcnow().isoformat(),
    }


class MockQuizService:
    """Mock implementation of QuizService for testing"""
    
    def __init__(self, quiz_results: Dict[str, Any]):
        self.quiz_results = quiz_results
    
    async def get_latest_quiz_score(self, user_id: str, subject: str, topic: str) -> float:
        """Get latest quiz score for a topic (0-100)"""
        try:
            scores = self.quiz_results["quizzes"][subject][topic]
            return scores[-1] if scores else 0
        except (KeyError, IndexError):
            return 0
    
    async def get_average_score(self, user_id: str, subject: str, topic: str) -> float:
        """Get average score for a topic"""
        try:
            scores = self.quiz_results["quizzes"][subject][topic]
            return sum(scores) / len(scores) if scores else 0
        except (KeyError, IndexError):
            return 0


class MockUserService:
    """Mock implementation of UserService for testing"""
    
    def __init__(self, user_profile: Dict[str, Any]):
        self.user_profile = user_profile
    
    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get user profile"""
        return self.user_profile
    
    async def get_subject_profiles(self, user_id: str) -> Dict[str, Any]:
        """Get subject profiles"""
        return {"study_pace": self.user_profile.get("study_pace", "moderate")}


class MockActivityService:
    """Mock implementation of ActivityService for testing"""
    
    async def log_activity(self, user_id: str, activity_type: str, details: Dict) -> None:
        """Log an activity"""
        pass


@pytest.fixture
def mock_services(sample_quiz_results, sample_user_profile):
    """Fixture providing all mock services"""
    return {
        "quiz_service": MockQuizService(sample_quiz_results),
        "user_service": MockUserService(sample_user_profile),
        "activity_service": MockActivityService(),
    }
