# backend/services/planner_engine.py
"""
Task Generation & Priority Scoring Engine
Converts topics into structured tasks and computes priority scores
"""

from typing import List, Optional, Dict, Tuple
from datetime import datetime, date, timedelta
from bson import ObjectId
from .quiz_service import QuizResultInDB
from models.planner_schemas import StudyTask
from models.user_schemas import PyObjectId
from core.db import AsyncIOMotorDatabase
from typing import Literal

class TaskGenerator:
    """
    Converts topics into structured study tasks based on:
    - Quiz performance (task type determination)
    - Topic difficulty
    - Subject weakness
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.COMPLETION_THRESHOLD = 0.6  # 60% = considered "completed"
        self.BASE_TIME_MINS = 30  # Base 30 minutes per difficulty level



    async def generate_tasks_for_subject(
        self,
        user_id: PyObjectId,
        subject: str,
        topics: List[Dict],
        weak_topics: List[str],
        deadline: date,
        plan_id: PyObjectId,
    ) -> List[StudyTask]:
        """
        Generate study tasks for a subject based on topic list and quiz history.

        Args:
            user_id: User ID
            subject: Subject name
            topics: List of topic dicts with 'name', 'difficulty', 'page_start', 'page_end'
            weak_topics: List of weak topic names (from subject profile)
            deadline: Plan deadline
            plan_id: Parent plan ID

        Returns:
            List of StudyTask objects sorted by priority
        """
        tasks = []

            


        for topic in topics:
            topic_name = topic.get("name") or topic.get("topic_title")

            # Fetch quiz history for this topic
            quiz_score = await self._get_latest_quiz_score(user_id, subject, topic_name or "")

            # Determine task type based on quiz performance
            if quiz_score is None:
                task_type = "learn"
                estimated_time = self._calculate_estimated_time(
                    topic.get("difficulty", "medium"), quiz_score=0
                )
            elif quiz_score < 60:
                task_type = "revise"
                estimated_time = self._calculate_estimated_time(
                    topic.get("difficulty", "medium"), quiz_score
                )
            else:
                task_type = "practice"
                estimated_time = self._calculate_estimated_time(
                    topic.get("difficulty", "medium"), quiz_score
                )
        
            # Create task
            task = StudyTask(
                plan_id=plan_id,
                subject=subject,
                topic=topic_name or "",
                task_type=task_type,
                difficulty=self._normalize_difficulty(topic.get("difficulty", "medium")),
                estimated_time_mins=estimated_time,
                quiz_score=quiz_score,
                priority_score=0.0,
                deadline=deadline,
                status="pending",
                scheduled_date=None,
                scheduled_time_start=None,
                scheduled_time_end=None,
                completed_at=None,
                actual_duration_mins=None,
                notes=None,
            )
            tasks.append(task)

        return tasks

    async def _get_latest_quiz_score(
        self, user_id: PyObjectId, subject: str, topic_name: str
    ) -> Optional[float]:
        """
        Fetch latest quiz score for a topic.

        Returns:
            Quiz score (0-100) or None if not attempted
        """
        try:
            quiz_result = await self.db.quiz_results.find_one(
                {
                    "user_id": user_id,
                    "topic_name": {"$regex": f"^{topic_name}$", "$options": "i"},
                },
                sort=[("attempted_at", -1)],
            )

            if quiz_result:
                return float(quiz_result.get("total_score", 0))
            return None
        except Exception as e:
            print(f"Error fetching quiz score for {topic_name}: {e}")
            return None

    def _calculate_estimated_time(
        self, difficulty: str, quiz_score: Optional[float] = None
    ) -> int:
        """
        Calculate estimated study time for a task.

        Time = Base × Difficulty_Weight × Performance_Adjustment

        Args:
            difficulty: "easy", "medium", or "hard"
            quiz_score: Last quiz score (0-100) or None

        Returns:
            Estimated time in minutes
        """
        difficulty_weight = {"easy": 1.0, "medium": 1.5, "hard": 2.0}.get(
            difficulty.lower(), 1.5
        )

        base_time = self.BASE_TIME_MINS * difficulty_weight

        # If quiz score exists, adjust based on performance
        if quiz_score is not None:
            if quiz_score == 0:
                # Never attempted: add extra time for learning
                performance_multiplier = 1.5
            elif quiz_score < 40:
                # Significant gap: double time for revision
                performance_multiplier = 2.0
            elif quiz_score < 60:
                # Minor gap: increase by 50%
                performance_multiplier = 1.5
            else:
                # Good performance: lighter review
                performance_multiplier = 0.8
        else:
            performance_multiplier = 1.0

        estimated_time = int(base_time * performance_multiplier)

        # Clamp between 15-300 minutes
        return max(15, min(300, estimated_time))

    def _normalize_difficulty(self, difficulty: str) -> Literal["easy", "medium", "hard"]:
        """Normalize difficulty to standard values."""
        difficulty_lower = difficulty.lower()
        if difficulty_lower in ["easy", "beginner", "basic", "simple"]:
            return "easy"
        elif difficulty_lower in ["hard", "advanced", "complex", "expert"]:
            return "hard"
        else:
            return "medium"


class PriorityScorer:
    """
    Computes priority scores for tasks using the formula:

    Priority = Urgency + Weakness + Difficulty + Mood_Adjustment

    Where:
    - Urgency = 1 / days_remaining (decreases as deadline approaches)
    - Weakness = (100 - quiz_score) / 100
    - Difficulty = {easy: 0.3, medium: 0.5, hard: 0.7}
    - Mood_Adjustment = emotion-based multiplier
    """

    def __init__(self):
        self.MOOD_MULTIPLIERS = {
            "stressed": 0.7,  # Reduce priority when stressed
            "bored": 0.8,
            "motivated": 1.3,  # Increase priority when motivated
            "engaged": 1.2,
            "tired": 0.6,  # Significantly reduce when tired
            "confused": 1.2,  # Increase confusion resolution
            "frustrated": 0.8,
            "confident": 1.0,  # Neutral
            "neutral": 1.0,
        }

        self.DIFFICULTY_SCORES = {"easy": 0.3, "medium": 0.5, "hard": 0.7}

    def score_task(
        self,
        task: StudyTask,
        current_date: date,
        user_mood: Optional[str] = None,
    ) -> float:
        """
        Compute priority score for a task.

        Args:
            task: StudyTask object
            current_date: Current date for urgency calculation
            user_mood: User's current mood

        Returns:
            Priority score (0-1, where 1 is most urgent)
        """
        # 1. Urgency: How close is the deadline?
        days_remaining = max(1, (task.deadline - current_date).days)
        urgency = 1.0 / (days_remaining + 1)  # +1 to avoid division issues

        # 2. Weakness: How far is the current score from target?
        if task.quiz_score is None:
            weakness = 1.0  # Not attempted = high priority
        else:
            weakness = max(0, (100 - task.quiz_score) / 100)

        # 3. Difficulty: Task difficulty level
        difficulty = self.DIFFICULTY_SCORES.get(task.difficulty, 0.5)

        # 4. Task type boost
        task_type_boost = {"revise": 1.2, "learn": 1.0, "practice": 0.7}.get(
            task.task_type, 1.0
        )

        # 5. Mood adjustment
        mood_multiplier = self.MOOD_MULTIPLIERS.get(user_mood, 1.0) if user_mood else 1.0

        # Compute score as weighted sum
        # Weights: urgency (0.3), weakness (0.3), difficulty (0.2), task_type (0.2)
        priority_score = (
            (urgency * 0.3 + weakness * 0.3 + difficulty * 0.2)
            * task_type_boost
            * mood_multiplier
        )

        # Normalize to 0-1 range
        priority_score = min(1.0, max(0.0, priority_score))

        return priority_score

    def score_all_tasks(
        self,
        tasks: List[StudyTask],
        current_date: date,
        user_mood: Optional[str] = None,
    ) -> List[Tuple[StudyTask, float]]:
        """
        Score all tasks and return with scores.

        Returns:
            List of (task, score) tuples sorted by score (descending)
        """
        scored_tasks = [
            (task, self.score_task(task, current_date, user_mood)) for task in tasks
        ]

        # Sort by score descending (highest priority first)
        scored_tasks.sort(key=lambda x: x[1], reverse=True)

        return scored_tasks


# Utility functions for task generation workflows

async def generate_all_tasks_for_plan(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    subjects: List[str],
    deadline: date,
    plan_id: PyObjectId,
) -> List[StudyTask]:
    """
    Generate tasks for all subjects in a plan.
    """
    generator = TaskGenerator(db)
    all_tasks = []

    for subject in subjects:
        # Find books for this subject belonging to the user
        books_cursor = db.books.find({"user_id": user_id, "subject": subject})
        book_ids = [book["_id"] async for book in books_cursor]
        if not book_ids:
            print(f"No books found for subject {subject}")
            continue

        # Fetch topics from those books
        topics_cursor = db.book_topics.find({"book_id": {"$in": book_ids}})
        topics = await topics_cursor.to_list(None)

        # Convert topics to the format expected by generate_tasks_for_subject
        # (each topic dict needs 'name', 'difficulty', etc.)
        # You can derive difficulty from topic title or default to "medium"
        formatted_topics = []
        for topic in topics:
            formatted_topics.append({
                "name": topic.get("topic_title"),
                "difficulty": "medium",  # or infer from content, length, etc.
                "page_start": topic.get("page_start"),
                "page_end": topic.get("page_end"),
            })

        # Get weak topics from user's subject profile (optional)
        user = await db.users.find_one({"_id": user_id})
        subject_profile = None
        if user and user.get("subject_profiles"):
            subject_profile = next(
                (sp for sp in user["subject_profiles"] if sp.get("subject") == subject),
                None,
            )
        weak_topics = subject_profile.get("weak_topics", []) if subject_profile else []

        # Generate tasks
        subject_tasks = await generator.generate_tasks_for_subject(
            user_id=user_id,
            subject=subject,
            topics=formatted_topics,
            weak_topics=weak_topics,
            deadline=deadline,
            plan_id=plan_id,
        )
        all_tasks.extend(subject_tasks)

    return all_tasks