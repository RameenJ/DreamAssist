# backend/services/mood_adapter.py
"""
Mood Adapter - Emotion-Based Schedule Adjustments
Adapts study sessions and plans based on detected emotions and trends
"""

from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
from bson import ObjectId
from models.planner_schemas import StudySession, StudyPlan, StudyTask, MoodStrategyResponse
from models.user_schemas import MoodLog, PyObjectId
from core.db import AsyncIOMotorDatabase


class MoodAdapter:
    """
    Adapts study schedules and plans based on:
    1. Real-time emotion detection
    2. Emotion trend analysis (is mood getting worse?)
    3. Adjustment strategies per emotion
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

        # Adjustment strategies per emotion
        self.EMOTION_STRATEGIES = {
            "stressed": {
                "reduce_difficulty": True,
                "reduce_duration": 1.5,  # Multiply by 1.5 (shorter sessions)
                "add_breaks": True,
                "break_interval_mins": 15,
                "recommended_tasks": ["revise", "practice"],  # Avoid new learning
                "session_recommendation": "Take frequent short breaks. Focus on comfort items.",
            },
            "bored": {
                "add_variety": True,
                "reduce_duration": 0.8,  # Slightly longer but more interesting
                "switch_topics": True,
                "recommended_tasks": ["learn", "practice"],  # Mix it up
                "session_recommendation": "Switch between different subjects every 30 mins.",
            },
            "motivated": {
                "increase_difficulty": True,
                "increase_duration": 1.2,  # Longer, challenging sessions
                "add_advanced_tasks": True,
                "recommended_tasks": ["practice", "learn"],
                "session_recommendation": "Take advantage of your motivation! Try harder problems.",
            },
            "tired": {
                "reduce_difficulty": True,
                "reduce_duration": 2.0,  # Much shorter sessions
                "add_breaks": True,
                "break_interval_mins": 10,
                "recommended_tasks": ["practice"],  # Only easy/familiar
                "session_recommendation": "Short sessions with light material. Consider rest.",
            },
            "confused": {
                "increase_learning": True,
                "reduce_duration": 1.3,  # Shorter, focused sessions
                "add_explanation_tasks": True,
                "recommended_tasks": ["learn", "revise"],  # Focus on fundamentals
                "session_recommendation": "Review fundamentals. Use visual aids and examples.",
            },
            "frustrated": {
                "reduce_difficulty": True,
                "change_task": True,
                "reduce_duration": 1.2,
                "add_breaks": True,
                "recommended_tasks": ["revise", "practice"],
                "session_recommendation": "Switch to a different topic. Take a mental break.",
            },
            "confident": {
                "maintain_difficulty": True,
                "increase_duration": 1.1,
                "recommended_tasks": ["practice", "learn"],
                "session_recommendation": "Continue with current pace. You're on track!",
            },
            "engaged": {
                "maintain_difficulty": True,
                "recommended_tasks": ["learn", "practice"],
                "session_recommendation": "Great engagement! Keep the current pace.",
            },
        }

    async def adapt_session_to_mood(
        self,
        session_id: PyObjectId,
        detected_emotion: str,
        user_id: PyObjectId,
    ) -> StudySession:
        """
        Adapt an upcoming session based on detected emotion.

        Args:
            session_id: Session to adapt
            detected_emotion: Detected emotion label
            user_id: User ID (for mood history)

        Returns:
            Updated StudySession
        """
        # Fetch session
        session_doc = await self.db.study_sessions.find_one({"_id": session_id})
        if not session_doc:
            raise ValueError(f"Session {session_id} not found")

        from models.planner_schemas import StudySession
        from core.datetime_utils import convert_datetime_to_date
        
        session_doc = convert_datetime_to_date(session_doc)
        session = StudySession(**session_doc)

        # Get emotion trend
        emotion_trend = await self._analyze_emotion_trend(user_id)

        # Get strategy for this emotion
        strategy = self.EMOTION_STRATEGIES.get(detected_emotion, {})

        # Apply adjustments to session
        mood_adjustments = []

        # 1. Difficulty adjustment
        if strategy.get("reduce_difficulty"):
            for block in session.time_blocks:
                if block.difficulty == "hard":
                    block.difficulty = "medium"
                    mood_adjustments.append(
                        f"Reduced {block.topic} difficulty from hard to medium"
                    )

        # 2. Duration adjustment
        if "reduce_duration" in strategy:
            multiplier = strategy["reduce_duration"]
            for block in session.time_blocks:
                old_duration = block.duration_mins
                block.duration_mins = max(15, int(block.duration_mins / multiplier))
                if old_duration != block.duration_mins:
                    mood_adjustments.append(
                        f"Adjusted {block.topic} time: {old_duration}min -> {block.duration_mins}min"
                    )

        elif "increase_duration" in strategy:
            multiplier = strategy["increase_duration"]
            for block in session.time_blocks:
                old_duration = block.duration_mins
                block.duration_mins = min(120, int(block.duration_mins * multiplier))
                if old_duration != block.duration_mins:
                    mood_adjustments.append(
                        f"Extended {block.topic} time: {old_duration}min -> {block.duration_mins}min"
                    )

        # 3. Break insertion
        if strategy.get("add_breaks"):
            session.mood_adjustments_applied.append("Added break reminders every 15 mins")

        # 4. Update session
        session.mood_at_start = detected_emotion
        session.mood_adjustments_applied.extend(mood_adjustments)

        # Save to DB
        await self.db.study_sessions.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "mood_at_start": detected_emotion,
                    "mood_adjustments_applied": session.mood_adjustments_applied,
                    "time_blocks": [
                        block.dict() for block in session.time_blocks
                    ],
                }
            },
        )

        # Check for overload only if plan_id exists
        if session.plan_id is not None:
            await self._check_and_apply_overload_recovery(
                plan_id=session.plan_id,      # type is now PyObjectId (not None)
                user_id=user_id,
                detected_emotion=detected_emotion,
                emotion_trend=emotion_trend,
            )
        return session

    async def _analyze_emotion_trend(
        self, user_id: PyObjectId, days: int = 7
    ) -> Dict[str, int]:
        """
        Analyze emotion trend over the past N days.

        Returns:
            {emotion_label: count, ...}
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        user = await self.db.users.find_one({"_id": user_id})
        mood_logs = user.get("mood_logs", []) if user else []

        # Filter recent logs
        recent_logs = [
            log
            for log in mood_logs
            if log.get("logged_at") and log.get("logged_at") > cutoff_date
        ]

        # Count emotions
        emotion_counts = {}
        for log in recent_logs:
            mood = log.get("mood", "neutral")
            emotion_counts[mood] = emotion_counts.get(mood, 0) + 1

        return emotion_counts

    async def _check_and_apply_overload_recovery(
        self,
        plan_id: PyObjectId,
        user_id: PyObjectId,
        detected_emotion: str,
        emotion_trend: Dict[str, int],
    ) -> bool:
        """
        Check if user is overwhelmed and apply recovery measures.

        Recovery triggers:
        1. Detected emotion is "stressed" or "tired" AND
        2. Trend shows ≥3 days of negative emotions OR
        3. Completion rate < 60% in last 7 days

        Returns:
            True if recovery was applied
        """
        negative_emotions = {"stressed", "frustrated", "confused", "tired"}
        recent_negative_count = sum(
            emotion_trend.get(em, 0) for em in negative_emotions
        )

        if recent_negative_count < 3 and detected_emotion not in negative_emotions:
            return False

        # Apply recovery: Insert buffer day, reduce workload
        # Ensure plan_id is ObjectId
        from bson import ObjectId
        if isinstance(plan_id, str):
            plan_oid = ObjectId(plan_id)
        else:
            plan_oid = plan_id
            
        plan_doc = await self.db.study_plans.find_one({"_id": plan_oid})
        if not plan_doc:
            return False

        from models.planner_schemas import StudyPlan
        from core.datetime_utils import convert_datetime_to_date
        
        plan_doc = convert_datetime_to_date(plan_doc)
        plan = StudyPlan(**plan_doc)

        # Insert recovery day (reduce tasks for tomorrow)
        recovery_measures = [
            "📝 Recovery day recommended",
            "🎯 Reducing task load by 30%",
            "🌟 Focusing on review/practice instead of new learning",
            "💪 You're doing great! Take it easy today.",
        ]

        # Update plan with recovery flag
        await self.db.study_plans.update_one(
            {"_id": plan_id},
            {"$set": {"last_adapted_at": datetime.utcnow()}},
        )

        return True

    async def suggest_session_strategy(self, detected_emotion: str) -> MoodStrategyResponse:
        strategy = self.EMOTION_STRATEGIES.get(detected_emotion, self.EMOTION_STRATEGIES["neutral"])
        return MoodStrategyResponse(
            emotion=detected_emotion,
            recommendation=strategy.get("session_recommendation", "Continue with your current study plan."),
            suggested_task_types=strategy.get("recommended_tasks", []),
            break_reminder=(
                f"Take {strategy.get('break_interval_mins', 15)} min breaks"
                if strategy.get("add_breaks")
                else "No breaks needed"
            ),
            adjustments=[k for k, v in strategy.items() if v is True]
        )


class MoodTrendAnalyzer:
    """
    Analyzes mood trends to detect patterns and predict burnout.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def compute_mood_trend(
        self, user_id: PyObjectId, days: int = 7
    ) -> Dict:
        """
        Compute mood statistics and trend.

        Returns:
            {
                average_mood: str,
                trend: "improving" | "declining" | "stable",
                mood_distribution: {emotion: count},
                risk_level: "low" | "medium" | "high"
            }
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        user = await self.db.users.find_one({"_id": user_id})
        mood_logs = user.get("mood_logs", []) if user else []

        # Filter recent logs
        recent_logs = sorted(
            [
                log
                for log in mood_logs
                if log.get("logged_at") and log.get("logged_at") > cutoff_date
            ],
            key=lambda x: x.get("logged_at", datetime.utcnow()),
        )

        if not recent_logs:
            return {
                "average_mood": "neutral",
                "trend": "stable",
                "mood_distribution": {},
                "risk_level": "low",
            }

        # Count moods
        mood_counts = {}
        for log in recent_logs:
            mood = log.get("mood", "neutral")
            mood_counts[mood] = mood_counts.get(mood, 0) + 1

        # Determine average mood
        mood_scores = {
            "confident": 3,
            "engaged": 2,
            "motivated": 2,
            "neutral": 0,
            "bored": -1,
            "confused": -1,
            "frustrated": -2,
            "stressed": -3,
            "tired": -2,
        }

        avg_score = sum(
            mood_scores.get(log.get("mood", "neutral"), 0)
            for log in recent_logs
        ) / len(recent_logs)

        # Determine trend (first half vs second half)
        mid_point = len(recent_logs) // 2
        first_half_score = sum(
            mood_scores.get(log.get("mood", "neutral"), 0)
            for log in recent_logs[:mid_point]
        ) / max(1, mid_point)
        second_half_score = sum(
            mood_scores.get(log.get("mood", "neutral"), 0)
            for log in recent_logs[mid_point:]
        ) / max(1, len(recent_logs) - mid_point)

        if second_half_score > first_half_score + 1:
            trend = "improving"
        elif second_half_score < first_half_score - 1:
            trend = "declining"
        else:
            trend = "stable"

        # Determine risk level
        negative_moods = {"stressed", "frustrated", "confused", "tired"}
        negative_count = sum(
            mood_counts.get(mood, 0) for mood in negative_moods
        )

        if negative_count >= len(recent_logs) * 0.5:
            risk_level = "high"
        elif negative_count >= len(recent_logs) * 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "average_mood": (
                "stressed" if avg_score < -1 else
                "neutral" if avg_score < 1 else
                "motivated"
            ),
            "trend": trend,
            "mood_distribution": mood_counts,
            "risk_level": risk_level,
            "negative_mood_percentage": (negative_count / len(recent_logs)) * 100,
        }