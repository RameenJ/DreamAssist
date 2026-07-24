"""
Daily Progress Tracker Service
Manages daily schedule creation, task completion tracking, and progress analytics
"""

from typing import List, Optional, Dict
from datetime import date, datetime, timedelta, time
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from requests import session
from models.planner_schemas import (
    DailySchedule,
    DailyProgressAnalytics,
    StudySession,
    StudyTask,
)
from models.user_schemas import PyObjectId
from typing import Literal

class DailyProgressTracker:
    """
    Tracks daily study progress and generates analytics:
    1. Creates/updates daily schedules from study sessions
    2. Tracks completion rates and productivity scores
    3. Computes daily analytics for visualization
    4. Maintains completion streaks
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    
    
    async def create_or_update_daily_schedule(
        self,
        user_id: PyObjectId,
        session: StudySession,
    ) -> DailySchedule:
        """
        Create or update a daily schedule based on a study session.
        
        Args:
            user_id: User ID
            session: The study session for the day
            
        Returns:
            DailySchedule with created/updated data
        """
        schedule_date = session.session_date
        # Convert date to datetime for MongoDB query (BSON cannot serialize date objects)
        schedule_datetime = datetime.combine(schedule_date, time.min)
        
        # Try to find existing schedule for this day
        existing_schedule = await self.db.daily_schedules.find_one({
            "user_id": user_id,
            "schedule_date": schedule_datetime,
        })
        
        if existing_schedule:
            # Update existing schedule
            daily_schedule = DailySchedule(**existing_schedule)
        else:
            # Create new schedule
            daily_schedule = DailySchedule(
                user_id=user_id,
                schedule_date=schedule_datetime,
                session_id=session.id,
                aggregated_plan_ids=session.aggregated_plan_ids,
                mood_at_start=None,
                mood_at_end=None,
                notes=None,
            )
        def map_session_status(session_status: str) -> Literal['scheduled', 'in_progress', 'completed', 'incomplete']:
            mapping = {
                "scheduled": "scheduled",
                "in_progress": "in_progress",
                "completed": "completed",
                "missed": "incomplete",
                "paused": "in_progress",
            }
            return mapping.get(session_status, "incomplete")  # type: ignore[return-value]
            # The type ignore is needed because dict.get returns str, but the literal matches.
            # Alternatively, use the if/elif inside the function.

        # Update with current session data
        daily_schedule.total_tasks = session.total_blocks
        daily_schedule.completed_tasks = session.completed_blocks
        daily_schedule.session_id = session.id
        daily_schedule.aggregated_plan_ids = session.aggregated_plan_ids
        daily_schedule.mood_at_start = session.mood_at_start
        daily_schedule.mood_at_end = session.mood_at_end
        daily_schedule.status = map_session_status(session.status)
        
        # Calculate planned duration from time blocks
        if session.start_time and session.end_time:
            start_mins = session.start_time.hour * 60 + session.start_time.minute
            end_mins = session.end_time.hour * 60 + session.end_time.minute
            daily_schedule.planned_duration_mins = end_mins - start_mins
        
        # Set actual duration if available
        if session.actual_duration_mins:
            daily_schedule.actual_duration_mins = session.actual_duration_mins
        
        # Calculate completion rate
        if daily_schedule.total_tasks > 0:
            daily_schedule.completion_rate = (
                daily_schedule.completed_tasks / daily_schedule.total_tasks
            )
        else:
            daily_schedule.completion_rate = 0.0
        
        # Calculate productivity score (0-1)
        # Formula: (completion_rate * 0.7) + (time_utilization * 0.3)
        time_utilization = 0.0
        if (daily_schedule.planned_duration_mins > 0 and 
            daily_schedule.actual_duration_mins is not None and 
            daily_schedule.actual_duration_mins > 0):
            time_utilization = min(
                daily_schedule.actual_duration_mins / daily_schedule.planned_duration_mins,
                1.0
            )
        
        daily_schedule.productivity_score = (
            (daily_schedule.completion_rate * 0.7) + (time_utilization * 0.3)
        )
        
        # Calculate focus score based on uninterrupted time
        # For now, simplified: if session completed without interrupt, high focus
        if session.interrupted:
            daily_schedule.focus_score = daily_schedule.productivity_score * 0.7
        else:
            daily_schedule.focus_score = min(daily_schedule.productivity_score * 1.1, 1.0)
        
        # Update timestamp
        daily_schedule.updated_at = datetime.utcnow()
        
        # Ensure schedule_date is datetime before saving
        daily_schedule.schedule_date = schedule_datetime
        
        # Save to database
        schedule_dict = daily_schedule.model_dump(by_alias=True, exclude_none=True, mode='python')
        # Ensure schedule_date is stored as datetime
        if 'schedule_date' in schedule_dict and isinstance(schedule_dict['schedule_date'], date) and not isinstance(schedule_dict['schedule_date'], datetime):
            schedule_dict['schedule_date'] = datetime.combine(schedule_dict['schedule_date'], time.min)
        
        if existing_schedule:
            # Update
            await self.db.daily_schedules.update_one(
                {"_id": daily_schedule.id},
                {"$set": schedule_dict}
            )
        else:
            # Insert
            result = await self.db.daily_schedules.insert_one(schedule_dict)
            daily_schedule.id = result.inserted_id
        
        return daily_schedule

    async def compute_daily_analytics(
        self,
        user_id: PyObjectId,
        analytics_date: date,
    ) -> DailyProgressAnalytics:
        """
        Compute comprehensive daily analytics for a specific date.
        
        Args:
            user_id: User ID
            analytics_date: Date to compute analytics for
            
        Returns:
            DailyProgressAnalytics with computed metrics
        """
        # Convert date to datetime for MongoDB query (BSON cannot serialize date objects)
        analytics_datetime = datetime.combine(analytics_date, time.min)
        
        # Fetch daily schedule for this date
        daily_schedule_doc = await self.db.daily_schedules.find_one({
            "user_id": user_id,
            "schedule_date": analytics_datetime,
        })
        
        if not daily_schedule_doc:
            # No schedule for this day - create empty analytics
            return DailyProgressAnalytics(
                user_id=user_id,
                analytics_date=analytics_datetime,
                daily_completion_rate=0.0,
                daily_productivity_score=0.0,
                daily_focus_score=0.0,
                total_study_time_mins=0,
                total_tasks_completed=0,
                total_tasks_attempted=0,
                dominant_mood=None,
                summary=None,
            )
        
        daily_schedule = DailySchedule(**daily_schedule_doc)
        
        # Fetch all tasks for this day's session
        subject_performance: Dict[str, Dict] = {}
        if daily_schedule.session_id:
            session_doc = await self.db.study_sessions.find_one(
                {"_id": daily_schedule.session_id}
            )
            if session_doc:
                from core.datetime_utils import convert_datetime_to_date
                session_doc = convert_datetime_to_date(session_doc)
                session = StudySession(**session_doc)
                
                # Build subject performance from time blocks
                for block in session.time_blocks:
                    subject = block.topic  # Or get from task
                    if subject not in subject_performance:
                        subject_performance[subject] = {
                            "completed_tasks": 0,
                            "total_tasks": 0,
                            "score": 0.0,
                        }
                    subject_performance[subject]["total_tasks"] += 1
                    if block.completed:
                        subject_performance[subject]["completed_tasks"] += 1
        
        # Calculate subject scores
        for subject, perf in subject_performance.items():
            if perf["total_tasks"] > 0:
                perf["score"] = perf["completed_tasks"] / perf["total_tasks"]
        
        # Get streak count
        streak_count = await self._calculate_streak(user_id, analytics_date)
        
        # Calculate comparison to average
        avg_completion = await self._get_average_completion_rate(user_id, analytics_date)
        compared_to_average = daily_schedule.completion_rate - avg_completion
        
        # Create analytics record
        analytics = DailyProgressAnalytics(
            user_id=user_id,
            analytics_date=analytics_datetime,
            daily_completion_rate=daily_schedule.completion_rate,
            daily_productivity_score=daily_schedule.productivity_score,
            daily_focus_score=daily_schedule.focus_score,
            total_study_time_mins=daily_schedule.actual_duration_mins,
            total_tasks_completed=daily_schedule.completed_tasks,
            total_tasks_attempted=daily_schedule.total_tasks,
            subject_performance=subject_performance,
            dominant_mood=daily_schedule.mood_at_end or daily_schedule.mood_at_start,
            compared_to_average=compared_to_average,
            streak_count=streak_count,
            summary=None,  # To be generated after analytics is computed
        )
        
        # Generate summary if needed
        analytics.summary = await self._generate_daily_summary(daily_schedule, analytics)
        
        # Save to database
        analytics_dict = analytics.model_dump(by_alias=True, exclude_none=True, mode='python')
        # Ensure analytics_date is stored as datetime
        if 'analytics_date' in analytics_dict and isinstance(analytics_dict['analytics_date'], date) and not isinstance(analytics_dict['analytics_date'], datetime):
            analytics_dict['analytics_date'] = datetime.combine(analytics_dict['analytics_date'], time.min)
        
        result = await self.db.daily_progress_analytics.insert_one(analytics_dict)
        analytics.id = result.inserted_id
        
        return analytics

    async def get_daily_progress_graph_data(
        self,
        user_id: PyObjectId,
        days: int = 30,
    ) -> Dict:
        """
        Fetch daily progress data for the past N days for graphing.
        
        Args:
            user_id: User ID
            days: Number of days to retrieve (default 30)
            
        Returns:
            Dictionary with dates, completion rates, productivity scores, etc.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        
        # Convert to datetime for MongoDB query
        start_datetime = datetime.combine(start_date, time.min)
        end_datetime = datetime.combine(end_date, time.max)
        
        # Fetch analytics for the period
        cursor = self.db.daily_progress_analytics.find({
            "user_id": user_id,
            "analytics_date": {
                "$gte": start_datetime,
                "$lte": end_datetime,
            }
        }).sort("analytics_date", 1)
        
        analytics_list = []
        async for doc in cursor:
            analytics_list.append(DailyProgressAnalytics(**doc))
        
        # Build graph data
        dates = []
        completion_rates = []
        productivity_scores = []
        focus_scores = []
        study_time_mins = []
        
        current_date = start_date
        # Convert analytics dates to date objects for comparison
        analytics_by_date = {}
        for a in analytics_list:
            # Extract date part from datetime
            if isinstance(a.analytics_date, datetime):
                analytics_date_key = a.analytics_date.date()
            else:
                analytics_date_key = a.analytics_date
            analytics_by_date[analytics_date_key] = a
        
        while current_date <= end_date:
            dates.append(str(current_date))
            
            if current_date in analytics_by_date:
                a = analytics_by_date[current_date]
                completion_rates.append(a.daily_completion_rate)
                productivity_scores.append(a.daily_productivity_score)
                focus_scores.append(a.daily_focus_score)
                study_time_mins.append(a.total_study_time_mins)
            else:
                # No data for this day
                completion_rates.append(0.0)
                productivity_scores.append(0.0)
                focus_scores.append(0.0)
                study_time_mins.append(0)
            
            current_date += timedelta(days=1)
        
        # Calculate statistics
        streak_count = await self._calculate_streak(user_id, end_date)
        avg_completion = sum(completion_rates) / len(completion_rates) if completion_rates else 0.0
        avg_productivity = sum(productivity_scores) / len(productivity_scores) if productivity_scores else 0.0
        
        return {
            "dates": dates,
            "completion_rates": completion_rates,
            "productivity_scores": productivity_scores,
            "focus_scores": focus_scores,
            "study_time_mins": study_time_mins,
            "streak_count": streak_count,
            "average_completion_rate": avg_completion,
            "average_productivity": avg_productivity,
        }

    async def _calculate_streak(self, user_id: PyObjectId, end_date: date) -> int:
        """
        Calculate the number of consecutive completed days ending on end_date.
        A day is considered "completed" if completion_rate >= 0.8
        """
        streak = 0
        current_date = end_date
        
        while True:
            # Convert to datetime
            current_datetime = datetime.combine(current_date, time.min)
            
            analytics_doc = await self.db.daily_progress_analytics.find_one({
                "user_id": user_id,
                "analytics_date": current_datetime,
            })
            
            if not analytics_doc:
                break
            
            analytics = DailyProgressAnalytics(**analytics_doc)
            if analytics.daily_completion_rate >= 0.8:
                streak += 1
            else:
                break
            
            current_date -= timedelta(days=1)
        
        return streak

    async def _get_average_completion_rate(
        self, user_id: PyObjectId, end_date: date
    ) -> float:
        """Calculate average completion rate for the past 30 days"""
        thirty_days_ago = end_date - timedelta(days=30)
        start_datetime = datetime.combine(thirty_days_ago, time.min)
        end_datetime = datetime.combine(end_date, time.max)
        
        cursor = self.db.daily_progress_analytics.find({
            "user_id": user_id,
            "analytics_date": {
                "$gte": start_datetime,
                "$lte": end_datetime,
            }
        })
        
        total_completion = 0.0
        count = 0
        async for doc in cursor:
            analytics = DailyProgressAnalytics(**doc)
            total_completion += analytics.daily_completion_rate
            count += 1
        
        return total_completion / count if count > 0 else 0.0

    async def _generate_daily_summary(
        self,
        daily_schedule: DailySchedule,
        analytics: DailyProgressAnalytics,
    ) -> str:
        """Generate a human-readable daily summary"""
        completion_pct = int(analytics.daily_completion_rate * 100)
        productivity_pct = int(analytics.daily_productivity_score * 100)
        
        if completion_pct >= 80:
            status = "Excellent work!"
        elif completion_pct >= 60:
            status = "Good progress."
        elif completion_pct >= 40:
            status = "Fair progress. Try to complete more tasks tomorrow."
        else:
            status = "Low completion. Consider adjusting your schedule."
        
        study_hours = analytics.total_study_time_mins / 60 if analytics.total_study_time_mins else 0
        mood_text = analytics.dominant_mood or "neutral"
        
        summary = (
            f"{status} Completed {analytics.total_tasks_completed}/{analytics.total_tasks_attempted} tasks. "
            f"Studied for {study_hours:.1f} hours with {mood_text} mood. "
            f"Productivity: {productivity_pct}%"
        )
        
        if analytics.compared_to_average > 0:
            summary += f" (Above your average by {int(analytics.compared_to_average * 100)}%)"
        
        return summary