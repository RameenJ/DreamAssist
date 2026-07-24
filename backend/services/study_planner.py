# backend/services/study_planner.py
"""
Study Planner - Long-Term Planning Logic
Generates multi-day study roadmaps and allocates time across subjects
"""

from typing import List, Dict, Optional, Tuple, Literal
from datetime import date, datetime, timedelta
from bson import ObjectId
from .planner_engine import TaskGenerator, PriorityScorer, generate_all_tasks_for_plan
from models.planner_schemas import (
    StudyPlan,
    StudyTask,
    DailyRoadmapEntry,
    PlanRoadmap,
)
from models.user_schemas import PyObjectId
from core.db import AsyncIOMotorDatabase


class StudyPlanner:
    """
    Generates long-term study plans by:
    1. Computing subject weights based on difficulty and weakness
    2. Allocating study hours proportionally
    3. Sequencing topics by priority
    4. Building a daily roadmap
    5. Inserting break days
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.priority_scorer = PriorityScorer()

    async def generate_study_plan(
        self,
        user_id: PyObjectId,
        subjects: List[str],
        deadline: date,
        mode: Literal['unified', 'per_subject'] = "unified",
        total_study_hours_per_week: float = 20.0,
        plan_name: Optional[str] = None,
        study_pace: Literal['slow', 'moderate', 'fast'] = "moderate",
    ) -> StudyPlan:
        """
        Generate a comprehensive study plan.

        Args:
            user_id: User ID
            subjects: List of subject names
            deadline: Exam/deadline date
            mode: "unified" or "per_subject"
            total_study_hours_per_week: Available hours per week
            plan_name: Optional custom plan name
            study_pace: "slow", "moderate", "fast"

        Returns:
            StudyPlan object
        """
        today = date.today()

        # 1. Create plan document
        plan = StudyPlan(
            user_id=user_id,
            plan_name=plan_name or f"Study Plan: {', '.join(subjects[:2])}...",
            subjects=subjects,
            start_date=today,
            end_date=deadline,
            mode=mode,
            status="active",
            total_available_hours=self._calculate_total_hours(today, deadline, total_study_hours_per_week),
            study_pace=study_pace,
            last_adapted_at=None,
        )

        # Save plan to DB
        # Use mode='python' to preserve ObjectIds
        plan_dict = plan.model_dump(by_alias=True, mode='python')
        
        # Explicitly ensure _id is stored as ObjectId (not string)
        id_value = plan_dict.get('_id')
        if id_value:
            if isinstance(id_value, str):
                plan_dict['_id'] = ObjectId(id_value)
            elif not isinstance(id_value, ObjectId):
                # Handle PyObjectId or other types
                plan_dict['_id'] = ObjectId(str(id_value))
            # else: already ObjectId, keep as-is
        else:
            # No _id provided, MongoDB will generate one (as ObjectId)
            pass
        
        # Explicitly ensure user_id is stored as ObjectId
        user_id_value = plan_dict.get('user_id')
        if isinstance(user_id_value, str):
            plan_dict['user_id'] = ObjectId(user_id_value)
        elif isinstance(user_id_value, ObjectId):
            plan_dict['user_id'] = user_id_value  # Already ObjectId
        else:
            # Handle PyObjectId or other types
            plan_dict['user_id'] = ObjectId(str(user_id_value))
            
        # Convert date objects to datetime for MongoDB compatibility
        plan_dict['start_date'] = datetime.combine(plan_dict['start_date'], datetime.min.time())
        plan_dict['end_date'] = datetime.combine(plan_dict['end_date'], datetime.min.time())
        result = await self.db.study_plans.insert_one(plan_dict)
        plan.id = result.inserted_id

        # 2. Generate tasks for all subjects
        all_tasks = await generate_all_tasks_for_plan(
            db=self.db,
            user_id=user_id,
            subjects=subjects,
            deadline=deadline,
            plan_id=plan.id,
        )

        # 3. Score all tasks
        scored_tasks = self.priority_scorer.score_all_tasks(all_tasks, today)

        # 4. Allocate hours to subjects
        subject_hours = await self._allocate_hours_to_subjects(
            subjects=subjects,
            total_hours=plan.total_available_hours,
            scored_tasks=scored_tasks,
            user_id=user_id,
        )

        # 5. Build daily roadmap
        roadmap = await self._build_daily_roadmap(
            scored_tasks=scored_tasks,
            subject_hours=subject_hours,
            start_date=today,
            end_date=deadline,
            study_pace=study_pace,
        )

        # 6. Save tasks to DB
        task_ids = []
        for task, priority_score in scored_tasks:
            task.priority_score = priority_score
            task_dict = task.model_dump(by_alias=True, mode='python')
            
            # Convert deadline from date to datetime for MongoDB
            if 'deadline' in task_dict and isinstance(task_dict['deadline'], date):
                task_dict['deadline'] = datetime.combine(task_dict['deadline'], datetime.min.time())
            
            # Ensure all ObjectIds are stored as ObjectId, not string
            if '_id' in task_dict and task_dict['_id']:
                id_val = task_dict['_id']
                if isinstance(id_val, str):
                    task_dict['_id'] = ObjectId(id_val)
                elif not isinstance(id_val, ObjectId):
                    task_dict['_id'] = ObjectId(str(id_val))
            
            if 'plan_id' in task_dict and task_dict['plan_id']:
                plan_id_val = task_dict['plan_id']
                if isinstance(plan_id_val, str):
                    task_dict['plan_id'] = ObjectId(plan_id_val)
                elif not isinstance(plan_id_val, ObjectId):
                    task_dict['plan_id'] = ObjectId(str(plan_id_val))
            
            result = await self.db.study_tasks.insert_one(task_dict)
            task_ids.append(result.inserted_id)

        # 7. Update plan with tasks
        plan.tasks = task_ids
        plan.scheduled_sessions = len(roadmap.roadmap)
        await self.db.study_plans.update_one(
            {"_id": plan.id},
            {"$set": {"tasks": task_ids, "scheduled_sessions": plan.scheduled_sessions}},
        )

        # 8. Link plan to user
        await self.db.users.update_one(
            {"_id": user_id},
            {"$push": {"active_plans": plan.id}},
        )

        return plan

    def _calculate_total_hours(
        self, start_date: date, end_date: date, hours_per_week: float
    ) -> float:
        """Calculate total available study hours until deadline."""
        days_available = (end_date - start_date).days
        weeks_available = days_available / 7
        return weeks_available * hours_per_week

    async def _allocate_hours_to_subjects(
        self,
        subjects: List[str],
        total_hours: float,
        scored_tasks: List[Tuple[StudyTask, float]],
        user_id: PyObjectId,
    ) -> Dict[str, float]:
        """
        Allocate study hours proportionally to subjects based on:
        - Topic count per subject
        - Average difficulty
        - Weakness score

        Returns:
            Dict mapping subject -> allocated hours
        """
        subject_weights = {}

        for subject in subjects:
            # Filter tasks for this subject
            subject_tasks = [t for t, _ in scored_tasks if t.subject == subject]

            if not subject_tasks:
                continue

            # Compute weight: Difficulty × Topic_Count × Weakness
            avg_difficulty = sum(
                {"easy": 1, "medium": 2, "hard": 3}.get(t.difficulty, 2)
                for t in subject_tasks
            ) / len(subject_tasks)

            topic_count = len(set(t.topic for t in subject_tasks))

            # Average weakness from quiz scores
            scores = [t.quiz_score for t in subject_tasks if t.quiz_score is not None]
            avg_score = sum(scores) / len(scores) if scores else 50.0
            weakness_score = 1 - (avg_score / 100)

            weight = avg_difficulty * topic_count * (1 + weakness_score)
            subject_weights[subject] = weight

        # Normalize weights to allocate hours
        total_weight = sum(subject_weights.values())
        if total_weight == 0:
            # Equal allocation
            return {subject: total_hours / len(subjects) for subject in subjects}

        return {
            subject: (weight / total_weight) * total_hours
            for subject, weight in subject_weights.items()
        }

    async def _build_daily_roadmap(
        self,
        scored_tasks: List[Tuple[StudyTask, float]],
        subject_hours: Dict[str, float],
        start_date: date,
        end_date: date,
        study_pace: Literal['slow', 'moderate', 'fast'] = "moderate",
    ) -> PlanRoadmap:
        """
        Build a daily study roadmap.

        Strategy:
        1. Group tasks by priority
        2. Distribute high-priority tasks across the week
        3. Insert buffer/break days every 5-6 study days
        4. Allocate sessions to days based on available hours

        Returns:
            PlanRoadmap with daily entries
        """
        days_available = (end_date - start_date).days
        roadmap_entries = []

        # Separate tasks by type for better sequencing
        revise_tasks = [(t, s) for t, s in scored_tasks if t.task_type == "revise"]
        learn_tasks = [(t, s) for t, s in scored_tasks if t.task_type == "learn"]
        practice_tasks = [(t, s) for t, s in scored_tasks if t.task_type == "practice"]

        current_date = start_date
        day_count = 0
        break_interval = {"slow": 7, "moderate": 6, "fast": 5}.get(study_pace, 6)

        while current_date <= end_date and day_count < days_available:
            # Determine if this is a break day
            if day_count > 0 and day_count % break_interval == 0:
                entry = DailyRoadmapEntry(
                    day_number=day_count + 1,
                    calendar_date=current_date,
                    allocated_subjects=[],
                    focus_topics=[],
                    session_type="buffer",
                    planned_hours=0,
                    notes="Rest/buffer day - review notes or take light quiz",
                )
            else:
                # Pick topics to focus on this day
                # Rotate through subjects and task types for variety

                # Determine task type for this day
                if len(revise_tasks) > 0 and day_count % 4 == 0:
                    focus_type = "revise"
                    task_pool = revise_tasks
                    session_type = "revision"
                elif len(learn_tasks) > 0 and day_count % 3 == 1:
                    focus_type = "learn"
                    task_pool = learn_tasks
                    session_type = "learning"
                else:
                    focus_type = "practice"
                    task_pool = practice_tasks
                    session_type = "practice"

                # Get tasks for this day
                day_tasks = task_pool[:3] if task_pool else []
                focus_subjects = list(set(t[0].subject for t in day_tasks))
                focus_topics = [t[0].topic for t in day_tasks]

                # Calculate planned hours based on task duration
                planned_hours = sum(t[0].estimated_time_mins / 60 for t in day_tasks)

                entry = DailyRoadmapEntry(
                    day_number=day_count + 1,
                    calendar_date=current_date,
                    allocated_subjects=focus_subjects,
                    focus_topics=focus_topics,
                    session_type=session_type,
                    planned_hours=planned_hours,
                    notes=f"Focus: {', '.join(focus_topics[:2])}",
                )

                # Remove used tasks
                if focus_type == "revise":
                    revise_tasks = revise_tasks[3:]
                elif focus_type == "learn":
                    learn_tasks = learn_tasks[3:]
                else:
                    practice_tasks = practice_tasks[3:]

            roadmap_entries.append(entry)
            current_date += timedelta(days=1)
            day_count += 1

        # Create roadmap summary
        summary = (
            f"Study Plan: {days_available} days, {len(scored_tasks)} tasks across "
            f"{len(set(t.subject for t, _ in scored_tasks))} subjects. "
            f"Break days every {break_interval} days."
        )

        return PlanRoadmap(
            plan_id="",  # Will be set by caller
            roadmap=roadmap_entries,
            total_days=day_count,
            summary=summary,
        )


async def auto_generate_initial_plan(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    subjects: List[str],
    deadline: date,
) -> StudyPlan:
    """
    Auto-generate an initial study plan for a user.
    Typically called after diagnostic quiz completion.

    Args:
        db: MongoDB database instance
        user_id: User ID
        subjects: List of subjects to plan for
        deadline: Exam/deadline date

    Returns:
        Generated StudyPlan
    """
    planner = StudyPlanner(db)

    # Fetch user's preferences
    user = await db.users.find_one({"_id": user_id})
    subject_profiles = user.get("subject_profiles", []) if user else []

    # Determine study pace
    study_pace = "moderate"
    if subject_profiles:
        study_pace = subject_profiles[0].get("study_pace", "moderate")

    # Generate plan
    plan = await planner.generate_study_plan(
        user_id=user_id,
        subjects=subjects,
        deadline=deadline,
        mode="unified",
        total_study_hours_per_week=20.0,
        plan_name=None,
        study_pace=study_pace,
    )

    return plan