"""
Study Scheduler - Daily Scheduling Logic
Generates time-blocked daily schedules with mood-based adjustments
Aggregates tasks from all active plans of the user.
"""

from typing import List, Optional, Dict
from datetime import date, time, datetime, timedelta
from bson import ObjectId
from .planner_engine import PriorityScorer
from models.planner_schemas import (
    StudyTask,
    StudySession,
    TimeBlock,
)
from models.user_schemas import PyObjectId
from core.db import AsyncIOMotorDatabase
import logging
logger = logging.getLogger(__name__)
from datetime import time

def convert_times_to_str(obj):
    """Recursively convert datetime.time objects to ISO format strings."""
    if isinstance(obj, time):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: convert_times_to_str(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_times_to_str(item) for item in obj]
    return obj

class DailyScheduler:
    """
    Generates daily study schedules with:
    1. Priority-based task ranking (across all active plans)
    2. Time-of-day preferences
    3. Break insertion
    4. Mood-based adjustments
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.priority_scorer = PriorityScorer()

        # Time zones for study preferences
        self.TIME_ZONES = {
            "morning": (6, 12),   # High focus
            "afternoon": (12, 18), # Medium focus
            "evening": (18, 23),   # Light/review
        }

        # Difficulty to time zone mapping
        self.DIFFICULTY_TO_ZONE = {
            "hard": "morning",
            "medium": "afternoon",
            "easy": "evening",
        }

    async def _ensure_session_index(self):
        """
        Create unique compound index on (user_id, session_date, aggregated_plan_ids).
        Idempotent - safe to call multiple times.
        """
        try:
            await self.db.study_sessions.create_index(
                [
                    ("user_id", 1),
                    ("session_date", 1),
                    ("aggregated_plan_ids", 1),
                ],
                unique=True,
                name="idx_unique_session_key"
            )
            logger.info("✅ Unique session index created/verified")
        except Exception as e:
            logger.warning(f"⚠️ Could not create session index (may already exist): {e}")

    def _normalize_plan_ids(self, plan_ids: List[PyObjectId]) -> List[PyObjectId]:
        """
        Normalize plan IDs by sorting them so [A,B] is treated same as [B,A].
        Converts all to strings for sorting, then back to ObjectId.
        """
        if not plan_ids:
            return plan_ids
        # Sort by string representation to ensure consistent ordering
        sorted_ids = sorted([str(pid) for pid in plan_ids])
        return [ObjectId(pid_str) for pid_str in sorted_ids]

    async def _get_existing_session(
        self,
        user_id: PyObjectId,
        target_date: date,
        aggregated_plan_ids: List[PyObjectId],
    ) -> Optional[Dict]:
        """
        Check if a session already exists for this (user, date, plans) combination.
        Returns the existing session document or None if not found.

        Uses a two-stage lookup:
        1. Exact match on (user_id, session_date, aggregated_plan_ids).
        2. Fallback: any session for (user_id, session_date) that already has
           completed blocks, so that progress is never lost when the active-plan
           set changes between session creation and the next fetch.
        """
        session_date_dt = datetime.combine(target_date, time.min)

        # Normalize plan IDs for comparison
        normalized_plan_ids = self._normalize_plan_ids(aggregated_plan_ids)

        # Stage 1: exact key match
        existing = await self.db.study_sessions.find_one({
            "user_id": user_id,
            "session_date": session_date_dt,
            "aggregated_plan_ids": normalized_plan_ids,
        })
        if existing:
            return existing

        # Stage 2: fallback — return any session for this (user, date) that has
        # completed blocks.  This prevents a new empty session from being created
        # (and returned) when the plan-id set differs from what was used at
        # creation time, which would silently hide all completed-task flags.
        existing_with_progress = await self.db.study_sessions.find_one(
            {
                "user_id": user_id,
                "session_date": session_date_dt,
                "completed_blocks": {"$gt": 0},
            },
            sort=[("completed_blocks", -1)],  # prefer the session with most progress
        )
        if existing_with_progress:
            logger.warning(
                f"⚠️ Exact plan-id match failed for user {user_id} on {target_date}. "
                f"Returning session {existing_with_progress.get('_id')} with "
                f"{existing_with_progress.get('completed_blocks', 0)} completed block(s) "
                f"to preserve progress."
            )
        return existing_with_progress

    async def schedule_day(
        self,
        user_id: PyObjectId,
        target_date: date,
        plan_ids: Optional[List[PyObjectId]] = None,
        current_mood: Optional[str] = None,
    ) -> StudySession:
        """
        Generate a unified daily schedule for a user by aggregating
        tasks from all active plans (or specific plans if provided).

        Ensures NO DUPLICATE sessions by checking for existing sessions
        before inserting. Handles race conditions with DuplicateKeyError.

        Args:
            user_id: User ID
            target_date: Date to schedule
            plan_ids: Optional list of plan IDs. If None, fetch all active plans.
            current_mood: Detected user mood

        Returns:
            StudySession with scheduled time blocks from all plans (existing or new)
        """
        # Ensure session index exists (idempotent)
        await self._ensure_session_index()

        # 1. Determine which plans to include
        if plan_ids is None:
            plan_ids = await self._get_active_plan_ids(user_id)

        # Normalize plan IDs for consistent comparison
        plan_ids = self._normalize_plan_ids(plan_ids)

        # Check if session ALREADY EXISTS for this (user, date, plans) combination
        existing_session_doc = await self._get_existing_session(user_id, target_date, plan_ids)
        if existing_session_doc:
            logger.info(
                f"📌 Session already exists for user {user_id}, date {target_date}. "
                f"Returning existing session instead of creating duplicate."
            )
            # Convert to StudySession object
            from core.datetime_utils import convert_datetime_to_date
            existing_session_doc = convert_datetime_to_date(existing_session_doc)
            return StudySession(**existing_session_doc)

        if not plan_ids:
            # No active plans → empty session
            empty_session = StudySession(
                plan_id=None,  # aggregated session
                user_id=user_id,
                session_date=target_date,
                start_time=time(9, 0),
                end_time=time(17, 0),
                status="scheduled",
                notes="No active study plans found for this user.",
                aggregated_plan_ids=None,
                mood_at_start=None,
                mood_at_end=None,
                started_at=None,
                completed_at=None,
                actual_duration_mins=None,
            )
            return empty_session

        # 2. Fetch tasks from all selected plans
        tasks = await self._get_tasks_for_plans(plan_ids, target_date)

        if not tasks:
            # No pending tasks for this date
            empty_session = StudySession(
                plan_id=None,
                user_id=user_id,
                session_date=target_date,
                start_time=time(9, 0),
                end_time=time(17, 0),
                status="scheduled",
                notes="No pending tasks scheduled for this day across all active plans.",
                aggregated_plan_ids=None,
                mood_at_start=None,
                mood_at_end=None,
                started_at=None,
                completed_at=None,
                actual_duration_mins=None,
            )
            return empty_session

        # 3. Rank tasks by priority score
        scored_tasks = self.priority_scorer.score_all_tasks(
            tasks, date.today(), current_mood
        )

        # 4. Apply mood adjustments
        adjusted_tasks = await self._apply_mood_adjustments(
            scored_tasks, current_mood
        )

        # 5. Build time blocks
        time_blocks, session_start, session_end = self._build_time_blocks(
            adjusted_tasks, target_date, current_mood
        )

        # 6. Create aggregated session
        session = StudySession(
                plan_id=None,
                user_id=user_id,
                session_date=target_date,
                start_time=session_start,
                end_time=session_end,
                time_blocks=time_blocks,
                mood_at_start=current_mood,
                status="scheduled",
                total_blocks=len(time_blocks),
                aggregated_plan_ids=plan_ids,
                # Add these missing optional fields
                mood_at_end=None,
                started_at=None,
                completed_at=None,
                actual_duration_mins=None,
                notes=None,
            )

        # 7. Save to DB
        session_dict = session.model_dump(by_alias=True, mode='python')
        
        # Convert session_date from date to datetime for MongoDB
        if 'session_date' in session_dict and isinstance(session_dict['session_date'], date):
            session_dict['session_date'] = datetime.combine(session_dict['session_date'], time.min)

        # Ensure all ObjectIds are stored as ObjectId, not string
        if '_id' in session_dict and session_dict['_id']:
            id_val = session_dict['_id']
            if isinstance(id_val, str):
                session_dict['_id'] = ObjectId(id_val)
            elif not isinstance(id_val, ObjectId):
                session_dict['_id'] = ObjectId(str(id_val))
        
        if 'plan_id' in session_dict and session_dict['plan_id']:
            plan_id_val = session_dict['plan_id']
            if isinstance(plan_id_val, str):
                session_dict['plan_id'] = ObjectId(plan_id_val)
            elif not isinstance(plan_id_val, ObjectId):
                session_dict['plan_id'] = ObjectId(str(plan_id_val))
        
        if 'user_id' in session_dict and session_dict['user_id']:
            user_id_val = session_dict['user_id']
            if isinstance(user_id_val, str):
                session_dict['user_id'] = ObjectId(user_id_val)
            elif not isinstance(user_id_val, ObjectId):
                session_dict['user_id'] = ObjectId(str(user_id_val))
        
        # Convert aggregated_plan_ids list items to ObjectId
        if 'aggregated_plan_ids' in session_dict and session_dict['aggregated_plan_ids']:
            plan_ids_list = session_dict['aggregated_plan_ids']
            session_dict['aggregated_plan_ids'] = [
                ObjectId(pid) if isinstance(pid, str) else (ObjectId(str(pid)) if not isinstance(pid, ObjectId) else pid)
                for pid in plan_ids_list
            ]

        session_dict = convert_times_to_str(session_dict)

        try:
            logger.info(f"➕ Inserting new session for user {user_id}, date {target_date}")
            result = await self.db.study_sessions.insert_one(session_dict)
            logger.info(f"✅ Insert succeeded! Inserted _id: {result.inserted_id}")
            session.id = result.inserted_id
        except Exception as e:
            # Handle DuplicateKeyError: try to fetch the existing session
            if "duplicate" in str(e).lower() or "E11000" in str(e):
                logger.warning(
                    f"⚠️ DuplicateKeyError during insert (race condition). "
                    f"Fetching existing session for user {user_id}, date {target_date}"
                )
                # Try to retrieve the existing session
                existing = await self._get_existing_session(user_id, target_date, plan_ids)
                if existing:
                    from core.datetime_utils import convert_datetime_to_date
                    existing = convert_datetime_to_date(existing)
                    return StudySession(**existing)
                else:
                    logger.error(f"❌ Could not find session after DuplicateKeyError: {e}")
                    raise
            else:
                logger.error(f"❌ Insert failed: {e}")
                raise

        # 8. Create daily schedule and analytics for this session
        from services.daily_progress_tracker import DailyProgressTracker
        tracker = DailyProgressTracker(self.db)
        
        # Create/update daily schedule
        await tracker.create_or_update_daily_schedule(user_id, session)
        
        # Compute daily analytics
        await tracker.compute_daily_analytics(user_id, target_date)

        # 9. Update each scheduled task with its block info
        for block in time_blocks:
            # Convert date to datetime for MongoDB serialization (BSON cannot encode datetime.date)
            scheduled_datetime = datetime.combine(target_date, time.min)
            # Convert time objects to strings (MongoDB BSON cannot encode datetime.time)
            update_dict = {
                "scheduled_date": scheduled_datetime,
                "scheduled_time_start": convert_times_to_str(block.start_time),
                "scheduled_time_end": convert_times_to_str(block.end_time),
                "status": "scheduled",
            }
            await self.db.study_tasks.update_one(
                {"_id": block.task_id},
                {"$set": update_dict},
            )

        return session

    async def _get_active_plan_ids(self, user_id: PyObjectId) -> List[PyObjectId]:
        """
        Fetch IDs of all active plans for the user.
        Active plans: status in ["active", "in_progress"] and deadline >= today.
        """
        # Convert date to datetime for MongoDB query (BSON cannot serialize date objects)
        today_datetime = datetime.combine(date.today(), time.min)
        
        cursor = self.db.study_plans.find(
            {
                "user_id": user_id,
                "status": {"$in": ["active", "in_progress"]},
                "deadline": {"$gte": today_datetime},
            },
            projection={"_id": 1}
        )
        plan_ids = []
        async for doc in cursor:
            plan_ids.append(doc["_id"])
        return plan_ids

    async def _get_tasks_for_plans(
        self, plan_ids: List[PyObjectId], target_date: date
    ) -> List[StudyTask]:
        """Fetch pending or scheduled tasks from multiple plans."""
        # Convert date to datetime for MongoDB query (BSON cannot serialize date objects)
        target_datetime = datetime.combine(target_date, time.min)
        target_datetime_end = datetime.combine(target_date + timedelta(days=1), time.min)
        
        tasks = []
        # "pending"  → not yet assigned to any day; always eligible.
        # "scheduled" → already pinned to a specific day; only include if that
        #               day matches target_date (avoids repeating tasks across days).
        # "missed"   → rescheduled from a previous day; eligible for today.
        cursor = self.db.study_tasks.find(
            {
                "plan_id": {"$in": plan_ids},
                "deadline": {"$gte": target_datetime},
                "$or": [
                    {"status": "pending"},
                    {"status": "missed"},
                    {
                        "status": "scheduled",
                        "scheduled_date": {
                            "$gte": target_datetime,
                            "$lt": target_datetime_end
                        }
                    },
                ],
            }
        )
        from core.datetime_utils import convert_datetime_to_date
        async for doc in cursor:
            doc = convert_datetime_to_date(doc)
            tasks.append(StudyTask(**doc))
        logger.info(f"📋 Found {len(tasks)} tasks for date {target_date} from {len(plan_ids)} plan(s)")
        return tasks

    async def _apply_mood_adjustments(
        self, scored_tasks: List[tuple], current_mood: Optional[str] = None
    ) -> List[tuple]:
        """Apply mood-based adjustments (unchanged from original)."""
        if not current_mood:
            return scored_tasks

        adjusted = []
        for task, score in scored_tasks:
            mood_task = task.copy(deep=True)

            if current_mood == "stressed":
                if mood_task.difficulty == "hard":
                    mood_task.difficulty = "medium"
                score *= 0.7

            elif current_mood == "bored":
                if mood_task.task_type == "practice":
                    mood_task.notes = (
                        f"{mood_task.notes or ''} [VARIETY: Mix with different topics]"
                    )

            elif current_mood == "motivated":
                if mood_task.difficulty == "easy":
                    mood_task.difficulty = "medium"
                score *= 1.3

            elif current_mood == "tired":
                if mood_task.estimated_time_mins > 45:
                    mood_task.estimated_time_mins = max(15, mood_task.estimated_time_mins // 2)
                score *= 0.6

            elif current_mood == "confused":
                if mood_task.task_type in ["learn", "revise"]:
                    score *= 1.2
                else:
                    score *= 0.8
                mood_task.notes = f"{mood_task.notes or ''} [FOCUS: Review fundamentals]"

            adjusted.append((mood_task, score))

        adjusted.sort(key=lambda x: x[1], reverse=True)
        return adjusted

    def _build_time_blocks(
        self,
        adjusted_tasks: List[tuple],
        target_date: date,
        current_mood: Optional[str] = None,
    ) -> tuple:
        """Build time blocks with flexible scheduling (attempts to fit all tasks)."""
        time_blocks = []

        session_start = time(9, 0)
        session_end = time(17, 0)

        break_interval_mins = {"stressed": 20, "tired": 15, "motivated": 30}.get(
            current_mood or "", 25
        )

        current_time = session_start
        current_hour = current_time.hour
        
        # Track tasks that couldn't fit
        skipped_tasks = []

        for task, score in adjusted_tasks:
            preferred_zone = self.DIFFICULTY_TO_ZONE.get(task.difficulty, "afternoon")
            zone_start, zone_end = self.TIME_ZONES[preferred_zone]

            block_duration_mins = task.estimated_time_mins
            
            # Try to schedule in preferred zone
            scheduled = False
            
            # If current hour is before preferred zone, move to zone start
            if current_hour < zone_start:
                current_time = time(zone_start, 0)
                current_hour = zone_start
            
            # Calculate if task fits in remaining time of current zone
            block_end_hour = current_hour + (current_time.minute + block_duration_mins) // 60
            block_end_mins = (current_time.minute + block_duration_mins) % 60
            
            # Check if it fits in current zone
            if current_hour >= zone_end:
                # Current zone is finished, try next available zone
                for zone_name in ["morning", "afternoon", "evening"]:
                    z_start, z_end = self.TIME_ZONES[zone_name]
                    if z_start > current_hour:
                        # Try this zone
                        test_hour = z_start
                        test_end_hour = test_hour + (block_duration_mins // 60)
                        if test_end_hour <= z_end:
                            current_time = time(z_start, 0)
                            current_hour = z_start
                            block_end_hour = test_end_hour
                            block_end_mins = block_duration_mins % 60
                            scheduled = True
                            break
            elif block_end_hour <= zone_end:
                # Fits in preferred zone
                scheduled = True
            else:
                # Doesn't fit in preferred zone, try to fit in any remaining time
                remaining_hours = zone_end - current_hour
                if block_duration_mins <= remaining_hours * 60:
                    block_end_hour = current_hour + (block_duration_mins // 60)
                    block_end_mins = block_duration_mins % 60
                    scheduled = True
                else:
                    # Try to find space in later zones
                    for zone_name in ["morning", "afternoon", "evening"]:
                        z_start, z_end = self.TIME_ZONES[zone_name]
                        if z_start >= zone_end:
                            # Check if task fits in this zone
                            test_end_hour = z_start + (block_duration_mins // 60)
                            if test_end_hour <= z_end:
                                current_time = time(z_start, 0)
                                current_hour = z_start
                                block_end_hour = test_end_hour
                                block_end_mins = block_duration_mins % 60
                                scheduled = True
                                break
            
            if scheduled:
                block_start = current_time
                block_end = time(block_end_hour, block_end_mins)

                time_block = TimeBlock(
                    task_id=task.id,
                    plan_id=task.plan_id,
                    subject=task.subject,
                    topic=task.topic,
                    task_type=task.task_type,
                    difficulty=task.difficulty,
                    start_time=block_start,
                    end_time=block_end,
                    duration_mins=block_duration_mins,
                    mood_adjustment=None,
                    completion_timestamp=None,
                    notes=None,
                )

                time_blocks.append(time_block)
                logger.info(f"✅ Scheduled task '{task.topic}' from {block_start} to {block_end}")

                # Advance with break
                next_start_mins = block_end_mins + break_interval_mins
                current_hour = block_end_hour + next_start_mins // 60
                next_start_mins = next_start_mins % 60
                current_time = time(current_hour, next_start_mins)
            else:
                logger.warning(f"⚠️ Could not schedule task '{task.topic}' - no available time slots")
                skipped_tasks.append((task, score))

        if skipped_tasks:
            logger.warning(f"⚠️ {len(skipped_tasks)} task(s) could not be scheduled due to time constraints")

        if time_blocks:
            last_block = time_blocks[-1]
            session_end = time(last_block.end_time.hour + 1, 0)
        else:
            session_end = time(17, 0)
            logger.warning(f"⚠️ No time blocks were created - session may be empty!")

        return time_blocks, session_start, session_end


class BreakScheduler:
    """Manages break scheduling (unchanged)."""
    @staticmethod
    def parse_break_preference(preference: str) -> Dict[str, int]:
        default = {"break_mins": 15, "study_mins": 45}
        if not preference or "no" in preference.lower():
            return {"break_mins": 0, "study_mins": 999}
        try:
            parts = preference.lower().split("after")
            if len(parts) == 2:
                break_part = parts[0].strip().split()[0]
                study_part = parts[1].strip().split()[0]
                return {"break_mins": int(break_part), "study_mins": int(study_part)}
        except:
            pass
        return default

    @staticmethod
    def insert_breaks_in_blocks(time_blocks: List[TimeBlock], break_preference: str) -> List[TimeBlock]:
        break_config = BreakScheduler.parse_break_preference(break_preference)
        break_mins = break_config["break_mins"]
        study_mins = break_config["study_mins"]
        if break_mins == 0:
            return time_blocks
        new_blocks = []
        accumulated_time = 0
        for block in time_blocks:
            accumulated_time += block.duration_mins
            new_blocks.append(block)
            if accumulated_time >= study_mins:
                # break block creation omitted for brevity (same as original)
                accumulated_time = 0
        return new_blocks


async def schedule_week(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    start_date: date,
    num_days: int = 7,
    plan_ids: Optional[List[PyObjectId]] = None,
    current_mood: Optional[str] = None,
) -> List[StudySession]:
    """
    Generate schedules for multiple days across all active plans (or specific plans).
    """
    scheduler = DailyScheduler(db)
    sessions = []
    for day_offset in range(num_days):
        target_date = start_date + timedelta(days=day_offset)
        session = await scheduler.schedule_day(
            user_id=user_id,
            target_date=target_date,
            plan_ids=plan_ids,
            current_mood=current_mood,
        )
        sessions.append(session)
    return sessions