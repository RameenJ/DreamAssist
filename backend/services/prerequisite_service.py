"""
Prerequisite Tracking Service
Handles prerequisite validation, chain management, and blocking logic
"""

from typing import List, Dict, Optional, Tuple, Any, Literal
from datetime import date, datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import asyncio
from typing import cast

from models.phase2_schemas import (
    TopicPrerequisite,
    PrerequisiteStatus,
    PrerequisiteChain,
)
from models.user_schemas import PyObjectId


class PrerequisiteService:
    """Service for managing topic prerequisites and dependency chains"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.prerequisites_collection = db["topic_prerequisites"]
        self.prerequisite_status_collection = db["prerequisite_status"]
        self.prerequisite_chains_collection = db["prerequisite_chains"]
        self.study_tasks_collection = db["study_tasks"]

    # ========================================================================
    # PREREQUISITE DEFINITION & MANAGEMENT
    # ========================================================================

    async def create_prerequisite_requirement(
        self,
        subject: str,
        dependent_topic: str,
        prerequisite_topics: List[str],
        difficulty_level: Literal["foundation", "intermediate", "advanced"] = "intermediate",
        is_strict: bool = True,
    ) -> TopicPrerequisite:
        """
        Define a prerequisite relationship between topics
        
        Args:
            subject: Subject name (e.g., 'DSA')
            dependent_topic: Topic that requires prerequisites (e.g., 'Graphs')
            prerequisite_topics: Topics that must be done first (e.g., ['Arrays', 'Linked Lists'])
            difficulty_level: Difficulty of dependent topic
            is_strict: If true, all prerequisites must be completed before scheduling
        
        Returns:
            Created TopicPrerequisite
            
        Example:
            Graphs requires: Arrays, Linked Lists
            Trees requires: Graphs, Binary Trees concept
        """
        prerequisite = TopicPrerequisite(
            subject=subject,
            dependent_topic=dependent_topic,
            prerequisite_topics=prerequisite_topics,
            difficulty_level=difficulty_level,
            is_strict=is_strict,
        )

        # Use mode='python' to preserve ObjectIds
        result = await self.prerequisites_collection.insert_one(
            prerequisite.model_dump(by_alias=True, mode='python')
        )
        prerequisite.id = result.inserted_id
        return prerequisite

    async def get_prerequisites_for_topic(
        self, subject: str, topic: str
    ) -> Optional[TopicPrerequisite]:
        """Get prerequisite requirements for a topic"""
        return await self.prerequisites_collection.find_one(
            {"subject": subject, "dependent_topic": topic}
        )

    async def get_topics_requiring_prerequisite(
        self, subject: str, topic: str
    ) -> List[TopicPrerequisite]:
        """Get all topics that require this topic as prerequisite"""
        return await self.prerequisites_collection.find(
            {
                "subject": subject,
                "prerequisite_topics": topic,
            }
        ).to_list(None)

    # ========================================================================
    # PREREQUISITE CHAIN MANAGEMENT
    # ========================================================================

    async def create_prerequisite_chain(
        self,
        subject: str,
        chain_name: str,
        topics_ordered: List[str],
        estimated_hours_per_topic: List[float],
        difficulty_progression: List[Literal["foundation", "intermediate", "advanced"]],
        description: Optional[str] = None,
    ) -> PrerequisiteChain:
        """
        Create a prerequisite chain (foundation -> intermediate -> advanced)
        
        Example:
            DSA Chain:
            - Arrays (foundation) -> 8 hours
            - Linked Lists (intermediate) -> 10 hours
            - Graphs (advanced) -> 12 hours
            - Trees (advanced) -> 10 hours
        """
        if (
            len(topics_ordered)
            != len(estimated_hours_per_topic)
            != len(difficulty_progression)
        ):
            raise ValueError(
                "All arrays must have same length"
            )

        chain = PrerequisiteChain(
            subject=subject,
            chain_name=chain_name,
            topics_ordered=topics_ordered,
            estimated_hours_per_topic=estimated_hours_per_topic,
            difficulty_progression=difficulty_progression,
            description=description,
        )

        result = await self.prerequisite_chains_collection.insert_one(
            chain.model_dump(by_alias=True, exclude={"id"})
        )
        chain.id = result.inserted_id
        return chain

    async def get_prerequisite_chain(
        self, subject: str, chain_name: str
    ) -> Optional[PrerequisiteChain]:
        """Get a prerequisite chain"""
        doc = await self.prerequisite_chains_collection.find_one(
            {"subject": subject, "chain_name": chain_name}
        )
        return PrerequisiteChain(**doc) if doc else None

    # ========================================================================
    # PREREQUISITE STATUS TRACKING
    # ========================================================================

    async def initialize_prerequisite_status(
        self,
        user_id: ObjectId,
        plan_id: ObjectId,
        topic: str,
        subject: str,
    ) -> PrerequisiteStatus:
        """Initialize prerequisite status for a topic in a plan"""
        # Check if prerequisites exist
        prereq_def = await self.get_prerequisites_for_topic(subject, topic)

        if not prereq_def:
            # No prerequisites defined
            status = PrerequisiteStatus(
                user_id=PyObjectId(user_id),
                plan_id=PyObjectId(plan_id),
                topic=topic,
                subject=subject,
                prerequisites={},
                blocking_prerequisites=[],
                can_start=True,
                estimated_unblock_date=None, 
            )
        else:
            # Initialize with prerequisites not met
            prerequisites_dict = {
                t: False for t in prereq_def.prerequisite_topics
            }
            status = PrerequisiteStatus(
                user_id=PyObjectId(user_id),
                plan_id=PyObjectId(plan_id),
                topic=topic,
                subject=subject,
                prerequisites=prerequisites_dict,
                blocking_prerequisites=prereq_def.prerequisite_topics,
                can_start=not prereq_def.is_strict,
                estimated_unblock_date=None, 
            )

        result = await self.prerequisite_status_collection.insert_one(
            status.model_dump(by_alias=True, exclude={"id"})
        )
        status.id = result.inserted_id
        return status

    async def get_prerequisite_status(
        self,
        user_id: ObjectId,
        plan_id: ObjectId,
        topic: str,
        subject: str,
    ) -> Optional[PrerequisiteStatus]:
        """Get prerequisite status for a topic"""
        doc = await self.prerequisite_status_collection.find_one(
            {
                "user_id": user_id,
                "plan_id": plan_id,
                "topic": topic,
                "subject": subject,
            }
        )
        return PrerequisiteStatus(**doc) if doc else None

    async def mark_prerequisite_completed(
        self,
        user_id: ObjectId,
        plan_id: ObjectId,
        completed_topic: str,
        subject: str,
    ) -> int:
        """
        Mark a prerequisite as completed and update dependent topics
        
        Returns: Number of dependent topics unblocked
        """
        # Find all topics that depend on this completed topic
        dependent_topics = await self.get_topics_requiring_prerequisite(
            subject, completed_topic
        )

        unblocked_count = 0

        for dependent in dependent_topics:
            # Update prerequisite status for dependent topic
            result = await self.prerequisite_status_collection.update_one(
                {
                    "user_id": user_id,
                    "plan_id": plan_id,
                    "topic": dependent.dependent_topic,
                    "subject": subject,
                },
                {
                    "$set": {
                        f"prerequisites.{completed_topic}": True,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            if result.modified_count > 0:
                # Check if all prerequisites now met
                status = await self.get_prerequisite_status(
                    user_id, plan_id, dependent.dependent_topic, subject
                )
                if status and all(status.prerequisites.values()):
                    unblocked_count += 1
                    # Update can_start flag
                    await self.prerequisite_status_collection.update_one(
                        {"_id": status.id},
                        {
                            "$set": {
                                "can_start": True,
                                "blocking_prerequisites": [],
                                "updated_at": datetime.utcnow(),
                            }
                        },
                    )

        return unblocked_count

    # ========================================================================
    # PREREQUISITE VALIDATION
    # ========================================================================

    async def can_start_topic(
        self,
        user_id: ObjectId,
        plan_id: ObjectId,
        topic: str,
        subject: str,
    ) -> Tuple[bool, List[str]]:
        """
        Check if a topic can be started
        
        Returns:
            Tuple of (can_start, list_of_blocking_prerequisites)
        """
        status = await self.get_prerequisite_status(
            user_id, plan_id, topic, subject
        )

        if status is None:
            return True, []

        return status.can_start, status.blocking_prerequisites

    async def estimate_topic_availability(
        self,
        user_id: ObjectId,
        plan_id: ObjectId,
        topic: str,
        subject: str,
    ) -> Optional[date]:
        """
        Estimate when a topic will be available based on prerequisites
        
        Returns:
            Estimated date when topic can be started, or None if already available
        """
        status = await self.get_prerequisite_status(
            user_id, plan_id, topic, subject
        )

        if status is None or status.can_start:
            return None

        # Get blocking prerequisites
        blocking = status.blocking_prerequisites

        # Find earliest completion dates of blocking topics
        blocking_dates = []
        for blocking_topic in blocking:
            # Find tasks for this topic in plan
            tasks = await self.study_tasks_collection.find(
                {
                    "plan_id": plan_id,
                    "topic": blocking_topic,
                    "subject": subject,
                }
            ).to_list(None)

            if tasks:
                # Get latest deadline among tasks
                deadlines = [t.get("deadline") for t in tasks]
                if deadlines:
                    blocking_dates.append(max(deadlines))

        if blocking_dates:
            # Add 1 day buffer after blocking prerequisites
            estimated = max(blocking_dates) + timedelta(days=1)
            return estimated

        return None

    # ========================================================================
    # ANALYTICS & REPORTING
    # ========================================================================

    async def get_prerequisites_blocking_progress(
        self,
        user_id: ObjectId,
        plan_id: ObjectId,
        subject: str,
    ) -> Dict[str, Any]:
        """Get overview of prerequisites blocking progress"""
        # Get all prerequisite statuses for this plan/subject
        statuses = await self.prerequisite_status_collection.find(
            {
                "user_id": user_id,
                "plan_id": plan_id,
                "subject": subject,
            }
        ).to_list(None)

        total_topics = len(statuses)
        topics_unblocked = sum(1 for s in statuses if s.get("can_start"))
        topics_blocked = total_topics - topics_unblocked

        blocking_count = {}
        for status in statuses:
            if not status.get("can_start"):
                for blocking in status.get("blocking_prerequisites", []):
                    blocking_count[blocking] = blocking_count.get(blocking, 0) + 1

        return {
            "total_topics": total_topics,
            "topics_unblocked": topics_unblocked,
            "topics_blocked": topics_blocked,
            "unblock_percentage": (
                (topics_unblocked / total_topics * 100) if total_topics > 0 else 0
            ),
            "critical_blockers": sorted(
                blocking_count.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "estimated_critical_blocker_dates": await self._get_blocker_dates(
                user_id, plan_id, subject
            ),
        }

    async def _get_blocker_dates(
        self, user_id: ObjectId, plan_id: ObjectId, subject: str
    ) -> Dict[str, date]:
        """Get estimated completion dates for critical blockers"""
        statuses = await self.prerequisite_status_collection.find(
            {
                "user_id": user_id,
                "plan_id": plan_id,
                "subject": subject,
                "can_start": False,
            }
        ).to_list(None)

        blocker_dates = {}
        for status in statuses:
            for blocking_topic in status.get("blocking_prerequisites", []):
                if blocking_topic not in blocker_dates:
                    estimated = await self.estimate_topic_availability(
                        user_id, plan_id, status["topic"], subject
                    )
                    if estimated:
                        blocker_dates[blocking_topic] = estimated

        return blocker_dates

    async def get_prerequisite_chain_progress(
        self,
        user_id: ObjectId,
        plan_id: ObjectId,
        chain_id: ObjectId,
    ) -> Dict[str, Any]:
        """Get progress through a prerequisite chain"""
        # Get chain definition
        chain = await self.prerequisite_chains_collection.find_one(
            {"_id": chain_id}
        )

        if chain is None:
            return {"error": "Chain not found"}

        topics = chain["topics_ordered"]
        progress = {}

        for idx, topic in enumerate(topics):
            status = await self.get_prerequisite_status(
                user_id, plan_id, topic, chain["subject"]
            )
            
            tasks = await self.study_tasks_collection.find(
                {
                    "plan_id": plan_id,
                    "topic": topic,
                }
            ).to_list(None)

            completed_tasks = sum(
                1 for t in tasks if t.get("status") == "completed"
            )

            progress[topic] = {
                "index": idx,
                "difficulty": chain["difficulty_progression"][idx],
                "estimated_hours": chain["estimated_hours_per_topic"][idx],
                "can_start": status.can_start if status else True,
                "blocking_prerequisites": (
                    status.blocking_prerequisites if status else []
                ),
                "total_tasks": len(tasks),
                "completed_tasks": completed_tasks,
                "completion_percentage": (
                    (completed_tasks / len(tasks) * 100)
                    if len(tasks) > 0
                    else 0
                ),
            }

        return {
            "chain_name": chain["chain_name"],
            "subject": chain["subject"],
            "total_topics": len(topics),
            "topics_progress": progress,
            "overall_progress": sum(
                p["completion_percentage"] for p in progress.values()
            ) / len(topics) if len(topics) > 0 else 0,
        }