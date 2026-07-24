# backend/services/progress_tracker.py
"""
Progress Tracker - Adaptive Rescheduling & Analytics
Tracks session completion and triggers adaptive plan updates
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta, time, timezone
from bson import ObjectId
from models.planner_schemas import (
    StudySession,
    StudyPlan,
    StudyPlanAnalytics,
    WeeklySummary,
    StudyTask,
)
from models.user_schemas import PyObjectId
from core.db import AsyncIOMotorDatabase


class AdaptiveTracker:
    """
    Tracks session completion and adaptively updates plans based on:
    1. Missed tasks (increase priority, reschedule)
    2. Early completion (pull future tasks forward if enabled)
    3. Consistent patterns (detect failure patterns, mood decline)
    4. Triggers re-planning when needed
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def log_session_completion(
        self,
        session_id: PyObjectId,
        completed_task_ids: List[PyObjectId],
        user_emotion_end: Optional[str] = None,
        interrupted: bool = False,
        notes: Optional[str] = None,
    ) -> Dict:
        """
        Log completion of a study session and trigger adaptive updates.

        Args:
            session_id: Session ID
            completed_task_ids: List of task IDs that were completed
            user_emotion_end: User's mood at session end
            interrupted: Whether session was interrupted
            notes: Session notes

        Returns:
            {
                success: bool,
                message: str,
                adaptive_actions_taken: List[str],
                next_session_suggestion: Dict,
            }
        """
        session_doc = await self.db.study_sessions.find_one({"_id": session_id})
        if not session_doc:
            raise ValueError(f"Session {session_id} not found")

        completed_at = datetime.utcnow()
        
        # === FIX #2: Update individual time_blocks ===
        # Build set of completed task IDs for fast lookup
        completed_task_id_set = {str(tid) if isinstance(tid, ObjectId) else tid for tid in completed_task_ids}
        
        # Update time_blocks in session - mark matching blocks as completed
        time_blocks = session_doc.get("time_blocks", [])
        updated_blocks = []
        completed_count = 0
        
        for block in time_blocks:
            task_id = block.get("task_id")
            task_id_str = str(task_id) if isinstance(task_id, ObjectId) else task_id

            if task_id_str in completed_task_id_set:
                block["completed"] = True
                block["completion_timestamp"] = completed_at
            updated_blocks.append(block)

        # Count ALL completed blocks (including those marked in previous calls).
        # Do NOT use len(completed_task_ids) — that only reflects the current request.
        completed_count = sum(1 for b in updated_blocks if b.get("completed", False))
        total_blocks = len(updated_blocks)
        final_status = "completed" if completed_count == total_blocks and total_blocks > 0 else "in_progress"

        # Update session with synchronized time_blocks
        await self.db.study_sessions.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "status": final_status,
                    "completed_at": completed_at if final_status == "completed" else None,
                    "completed_blocks": completed_count,
                    "total_blocks": total_blocks,
                    "time_blocks": updated_blocks,
                    "mood_at_end": user_emotion_end,
                    "interrupted": interrupted,
                    "notes": notes,
                }
            },
        )

        # Update completed tasks
        for task_id in completed_task_ids:
            await self.db.study_tasks.update_one(
                {"_id": task_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": completed_at,
                    }
                },
            )

        # Keep daily_schedules in sync so analytics and the UI counter stay correct.
        # This collection is only written during session creation otherwise.
        session_date_dt = session_doc.get("session_date")
        if session_date_dt:
            completion_rate = completed_count / total_blocks if total_blocks > 0 else 0.0
            await self.db.daily_schedules.update_one(
                {
                    "user_id": session_doc.get("user_id"),
                    "schedule_date": session_date_dt,
                },
                {
                    "$set": {
                        "completed_tasks": completed_count,
                        "completion_rate": completion_rate,
                        "status": final_status if final_status == "completed" else "in_progress",
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

        all_scheduled_tasks = [block.get("task_id") for block in session_doc.get("time_blocks", [])]

        adaptive_actions = []

        # Rescheduling of incomplete tasks is intentionally deferred to end-of-day.
        # Calling _reschedule_missed_tasks here would treat every task not yet marked
        # complete as "missed" even mid-session, which changes task statuses and
        # produces incorrect per-day task distribution.

        # 2. Handle early completion
        early_completion_ratio = (
            len(completed_task_ids) / max(1, len(all_scheduled_tasks))
        )
        if early_completion_ratio > 0.9:  # Completed 90%+
            adaptive_actions.append(
                "✓ Great progress! Consider pulling forward some future tasks."
            )
            # If aggressive_adaptation enabled, pull tasks forward
            plan_id = session_doc.get("plan_id")
            if plan_id:
                # Ensure plan_id is PyObjectId
                if isinstance(plan_id, str):
                    plan_oid = PyObjectId(plan_id)
                elif isinstance(plan_id, ObjectId) and not isinstance(plan_id, PyObjectId):
                    plan_oid = PyObjectId(plan_id)
                else:
                    plan_oid = plan_id
                    
                plan_doc = await self.db.study_plans.find_one({"_id": plan_oid})
                if plan_doc and plan_doc.get("aggressive_adaptation"):
                    adaptive_actions.extend(
                        await self._pull_forward_tasks(plan_oid)
                    )

        # 3. Analyze patterns and detect if re-planning needed
        plan_id = session_doc.get("plan_id")
        replan_needed, replan_reason = await self._should_trigger_replanning(
            plan_id,
            session_doc.get("user_id"),
        )

        if replan_needed:
            adaptive_actions.append(f"⚠️ Plan update recommended: {replan_reason}")

        # Log action to activity
        await self.db.user_activities.insert_one(
            {
                "user_id": session_doc.get("user_id"),
                "activity_type": "session_completed",
                "timestamp": completed_at,
                "metadata": {
                    "session_id": str(session_id),
                    "completed_tasks": len(completed_task_ids),
                    "total_tasks": len(all_scheduled_tasks),
                    "adaptive_actions": adaptive_actions,
                },
            }
        )

        return {
            "success": True,
            "message": "Session logged successfully",
            "adaptive_actions_taken": adaptive_actions,
            "next_session_suggestion": {
                "date": (date.today() + timedelta(days=1)).isoformat(),
                "recommendation": (
                    "You're on track!" if len(adaptive_actions) == 0
                    else "Consider the suggested adjustments above."
                ),
            },
        }

    async def _reschedule_missed_tasks(
        self,
        missed_task_ids: List[PyObjectId],
        plan_id: PyObjectId,
        session_date: date,
    ) -> List[str]:
        """
        Reschedule missed tasks with increased priority.

        Strategy:
        1. Mark as "missed" status
        2. Increase priority
        3. Schedule for next available day
        4. Notify user

        Returns:
            List of action descriptions
        """
        actions = []

        for task_id in missed_task_ids:
            task_doc = await self.db.study_tasks.find_one({"_id": task_id})
            if not task_doc:
                continue

            # Increase priority (multiply by 1.2)
            new_priority = min(1.0, task_doc.get("priority_score", 0.5) * 1.2)

            # Reschedule to next day
            next_day = session_date + timedelta(days=1)

            await self.db.study_tasks.update_one(
                {"_id": task_id},
                {
                    "$set": {
                        "status": "missed",
                        "priority_score": new_priority,
                        "scheduled_date": next_day,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            actions.append(
                f"📌 Rescheduled '{task_doc.get('topic', 'task')}' to {next_day} with increased priority"
            )

        # Update plan stats
        await self.db.study_plans.update_one(
            {"_id": plan_id},
            {"$inc": {"missed_sessions": len(missed_task_ids)}},
        )

        return actions

    async def _pull_forward_tasks(self, plan_id: PyObjectId) -> List[str]:
        """
        Pull forward non-urgent tasks if aggressive adaptation enabled.

        Returns:
            List of action descriptions
        """
        actions = []

        # Fetch pending tasks
        pending_tasks = await self.db.study_tasks.find(
            {"plan_id": plan_id, "status": "pending"}
        ).to_list(10)  # Limit to first 10

        for task in pending_tasks:
            # Only pull forward low-priority practice tasks
            if task.get("task_type") == "practice" and task.get("priority_score", 0) < 0.4:
                # Convert date to datetime for MongoDB compatibility (BSON cannot serialize date objects)
                scheduled_datetime = datetime.combine(date.today(), time.min)
                await self.db.study_tasks.update_one(
                    {"_id": task["_id"]},
                    {"$set": {"scheduled_date": scheduled_datetime}},
                )
                actions.append(f"⏩ Pulled forward '{task.get('topic')}' practice task")

        return actions

    async def _should_trigger_replanning(
        self, plan_id: PyObjectId, user_id: PyObjectId
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if adaptive re-planning is needed.

        Triggers:
        1. Completion rate < 60% over last 7 days
        2. Negative emotion trend detected
        3. Consistent task failures (same topic failed 3x)
        4. Manual user request

        Returns:
            (should_replan: bool, reason: str)
        """
        # 1. Check completion rate over last 7 days
        seven_days_ago = date.today() - timedelta(days=7)
        # Convert to datetime for MongoDB query (BSON cannot serialize date objects)
        seven_days_ago_dt = datetime.combine(seven_days_ago, time.min)
        
        recent_sessions = await self.db.study_sessions.find(
            {
                "aggregated_plan_ids": plan_id,
                "session_date": {"$gte": seven_days_ago_dt},
            }
        ).to_list(None)

        if recent_sessions:
            total_blocks = sum(s.get("total_blocks", 0) for s in recent_sessions)
            completed_blocks = sum(s.get("completed_blocks", 0) for s in recent_sessions)

            completion_rate = (
                completed_blocks / total_blocks if total_blocks > 0 else 0
            )

            if completion_rate < 0.6:
                return True, f"Completion rate low ({completion_rate:.0%}). Reducing workload."

        # 2. Check mood trend
        user = await self.db.users.find_one({"_id": user_id})
        mood_logs = user.get("mood_logs", []) if user else []

        recent_moods = [
            log for log in mood_logs
            if log.get("logged_at") and log.get("logged_at") > datetime.utcnow() - timedelta(days=7)
        ]

        negative_moods = {"stressed", "frustrated", "confused", "tired"}
        negative_count = sum(
            1 for log in recent_moods
            if log.get("mood") in negative_moods
        )

        if len(recent_moods) > 0 and negative_count > len(recent_moods) * 0.5:
            return True, "Negative emotion trend detected. Taking load off."

        return False, None


class PlanAnalytics:
    """
    Computes comprehensive analytics for study plans.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def compute_plan_analytics(
        self, plan_id: PyObjectId
    ) -> StudyPlanAnalytics:
        """
        Compute all analytics for a plan.

        Returns:
            StudyPlanAnalytics object
        """
        # Ensure plan_id is ObjectId
        if isinstance(plan_id, str):
            plan_oid = ObjectId(plan_id)
        else:
            plan_oid = plan_id
        
        plan_doc = await self.db.study_plans.find_one({"_id": plan_oid})
        if not plan_doc:
            raise ValueError(f"Plan {plan_id} not found")

        from models.planner_schemas import StudyPlan
        from core.datetime_utils import convert_datetime_to_date
        
        plan_doc = convert_datetime_to_date(plan_doc)
        plan = StudyPlan(**plan_doc)

        # 1. Compute overall metrics
        # Sessions are aggregated (plan_id=null); filter by aggregated_plan_ids instead.
        sessions = await self.db.study_sessions.find(
            {"aggregated_plan_ids": plan_oid}
        ).to_list(None)

        total_scheduled = len(sessions) if sessions else 0
        total_completed = len(
            [s for s in sessions if s.get("status") == "completed"]
        ) if sessions else 0
        total_missed = len([s for s in sessions if s.get("status") == "missed"]) if sessions else 0

        # Ensure numeric values are never None
        total_scheduled = total_scheduled or 0
        total_completed = total_completed or 0
        total_missed = total_missed or 0

        completion_rate = (
            total_completed / total_scheduled if total_scheduled > 0 else 0.0
        )

        # 2. Compute subject-wise progress - use ObjectId for queries
        tasks = await self.db.study_tasks.find(
            {"plan_id": plan_oid}
        ).to_list(None)

        subject_completion = {}
        for subject in plan.subjects:
            subject_tasks = [t for t in tasks if t.get("subject") == subject] if tasks else []
            if subject_tasks:
                completed = len(
                    [t for t in subject_tasks if t.get("status") == "completed"]
                )
                # Ensure this is a valid float
                subject_completion[subject] = float(
                    completed / len(subject_tasks)
                ) if len(subject_tasks) > 0 else 0.0

        # 3. Compute mood trend
        mood_distribution = {}
        for session in sessions:
            mood = session.get("mood_at_start") or "neutral"
            mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
        
        # Ensure mood_distribution is not None
        mood_distribution = mood_distribution or {}

        # 4. Compute productivity score
        # Handle None values explicitly
        total_time_planned = sum(
            (t.get("estimated_time_mins") or 0) for t in tasks
        )
        total_time_actual = sum(
            (s.get("actual_duration_mins") or 0) 
            for s in sessions 
            if s.get("status") == "completed"
        )

        total_time_planned = total_time_planned or 0
        total_time_actual = total_time_actual or 0

        if total_time_planned > 0:
            productivity_score = min(1.0, total_time_actual / total_time_planned)
        else:
            productivity_score = 0.0

        # 5. Compute weekly summaries
        weekly_summaries = await self._compute_weekly_summaries(plan, plan_oid)

        # 6. Identify improved/weak/mastered topics
        improved_topics = []
        still_weak_topics = []
        mastered_topics = []

        for task in tasks:
            quiz_score = task.get("quiz_score")
            if quiz_score is None:
                quiz_score = 0
            if quiz_score >= 80:
                mastered_topics.append(task.get("topic"))
            elif quiz_score >= 60:
                improved_topics.append(task.get("topic"))
            else:
                still_weak_topics.append(task.get("topic"))

        # Create analytics object with all fields properly initialized and typed
        avg_duration = 0.0
        if (total_completed or 0) > 0 and (total_time_actual or 0) > 0:
            avg_duration = float((total_time_actual or 0) / (total_completed or 1))
        avg_duration = avg_duration or 0.0
        
        print("\n=== ANALYTICS DEBUG ===")
        print(f"overall_completion_rate: {completion_rate} (type: {type(completion_rate)})")
        print(f"overall_productivity_score: {productivity_score} (type: {type(productivity_score)})")
        for i, ws in enumerate(weekly_summaries):
            print(f"weekly_summaries[{i}].completion_rate: {ws.completion_rate} (type: {type(ws.completion_rate)})")
        print("=======================\n")

        analytics = StudyPlanAnalytics(
            plan_id=plan_id,
            user_id=plan.user_id,
            overall_completion_rate=float(completion_rate) if completion_rate is not None else 0.0,
            overall_productivity_score=float(productivity_score) if productivity_score is not None else 0.0,
            subject_completion=subject_completion or {},
            total_sessions_scheduled=int(total_scheduled or 0),
            total_sessions_completed=int(total_completed or 0),
            total_sessions_missed=int(total_missed or 0),
            avg_session_duration_mins=avg_duration,
            mood_distribution=mood_distribution or {},
            mood_trend=self._compute_mood_trend(mood_distribution or {}),
            weekly_summaries=weekly_summaries or [],
            improved_topics=list(set(improved_topics)) if improved_topics else [],
            still_weak_topics=list(set(still_weak_topics)) if still_weak_topics else [],
            mastered_topics=list(set(mastered_topics)) if mastered_topics else [],
        )

        # Save to DB
        analytics_dict = analytics.model_dump(by_alias=True, mode='python')
        # WeeklySummary.start_date / end_date are date objects — convert to datetime
        for ws in analytics_dict.get("weekly_summaries", []):
            for field in ("start_date", "end_date"):
                val = ws.get(field)
                if isinstance(val, date) and not isinstance(val, datetime):
                    ws[field] = datetime.combine(val, datetime.min.time())
        result = await self.db.study_plan_analytics.insert_one(analytics_dict)
        analytics.id = result.inserted_id

        return analytics

    async def _compute_weekly_summaries(
        self, plan: StudyPlan, plan_oid: ObjectId
    ) -> List[WeeklySummary]:
        """Compute analytics for each week of the plan."""
        summaries = []

        # Guard against None dates
        if plan.start_date is None or plan.end_date is None:
            return summaries

        current_date = plan.start_date
        week_num = 1

        while current_date < plan.end_date:
            week_start = current_date
            week_end = min(current_date + timedelta(days=6), plan.end_date)

            # Convert date objects to datetime for MongoDB query
            week_start_dt = datetime.combine(week_start, datetime.min.time())
            week_end_dt = datetime.combine(week_end, datetime.min.time())

            sessions = await self.db.study_sessions.find(
                {
                    "aggregated_plan_ids": plan_oid,
                    "session_date": {
                        "$gte": week_start_dt,
                        "$lte": week_end_dt,
                    },
                }
            ).to_list(None)

            if sessions:
                completed = len(
                    [s for s in sessions if s.get("status") == "completed"]
                )
                total = len(sessions)
                completion_rate = completed / total if total > 0 else 0

                # Compute mood
                moods = [s.get("mood_at_start") for s in sessions if s.get("mood_at_start")]
                avg_mood = max(
                    set(moods), key=moods.count
                ) if moods else "neutral"

                summary = WeeklySummary(
                    week_number=week_num,
                    start_date=week_start,
                    end_date=week_end,
                    sessions_scheduled=total,
                    sessions_completed=completed,
                    completion_rate=completion_rate,
                    avg_mood=avg_mood,
                    productivity_score=0.0,
                    total_hours_planned=0.0,
                    total_hours_actual=0.0,
                    tasks_completed=0,
                    tasks_missed=0,
                    notes=None,
                )
                summaries.append(summary)

            week_num += 1
            current_date = week_end + timedelta(days=1)

        return summaries

    def _compute_mood_trend(self, mood_distribution: Dict[str, int]) -> str:
        """Determine mood trend from distribution."""
        if not mood_distribution:
            return "stable"

        positive_moods = {"confident", "engaged", "motivated"}
        negative_moods = {"stressed", "frustrated", "confused", "tired"}

        positive_count = sum(
            mood_distribution.get(m, 0) for m in positive_moods
        )
        negative_count = sum(
            mood_distribution.get(m, 0) for m in negative_moods
        )

        if negative_count > positive_count * 1.5:
            return "declining"
        elif positive_count > negative_count * 1.5:
            return "improving"
        else:
            return "stable"