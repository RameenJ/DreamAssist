"""
Goal-Based Planning Service (Phase 2b)
Generates phased study plans from user-specified goals respecting prerequisites
"""

from typing import List, Dict, Optional, Tuple, cast, Any
from datetime import date, datetime, timedelta, time
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import math

from models.phase2_schemas import LearningGoal, GoalBasedPlan
from models.user_schemas import PyObjectId
from services.prerequisite_service import PrerequisiteService

class GoalBasedPlanningService:
    """Service for generating phased study plans from learning goals"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.goals_collection = db["learning_goals"]
        self.goal_plans_collection = db["goal_based_plans"]
        self.study_plans_collection = db["study_plans"]
        self.prerequisite_service = PrerequisiteService(db)

    # ========================================================================
    # GOAL MANAGEMENT
    # ========================================================================

    async def create_goal(
        self,
        user_id: ObjectId,
        goal_title: str,
        goal_type: str,  # Will be one of: exam, skill_acquisition, interview_prep, certification
        subject: str,
        topics_to_cover: List[str],
        target_score: Optional[float],
        deadline: date,
        priority: str = "medium",  # Will be one of: low, medium, high
        include_prerequisites: bool = True,
    ) -> LearningGoal:
        """
        Create a learning goal
        
        Args:
            user_id: User creating the goal
            goal_title: Human-readable goal (e.g., "Master DSA in 2 weeks")
            goal_type: exam, skill_acquisition, interview_prep, certification
            subject: Primary subject (e.g., "DSA")
            topics_to_cover: Topics user wants to master
            target_score: Target quiz score (0-100)
            deadline: Goal deadline date
            priority: low, medium, high
            include_prerequisites: If True, auto-include prerequisite topics
        
        Returns:
            Created LearningGoal
        """
        # If including prerequisites, expand topic list
        if include_prerequisites:
            topics_with_prereqs = await self._expand_topics_with_prerequisites(
                subject, topics_to_cover
            )
        else:
            topics_with_prereqs = topics_to_cover

        # Estimate hours needed
        estimated_hours = await self._estimate_hours_for_topics(
            subject, topics_with_prereqs
        )

        goal = LearningGoal(
            user_id=PyObjectId(user_id),
            goal_title=goal_title,
            goal_type=goal_type,  # type: ignore  # Validate at runtime
            subject=subject,
            topics_to_cover=topics_with_prereqs,
            target_score=target_score,
            current_score=0.0,
            deadline=deadline,
            priority=priority,  # type: ignore  # Validate at runtime
            estimated_hours_needed=estimated_hours,
            status="not_started",
            # Explicitly set optional fields to their defaults
            prerequisite_chains=[],           # default_factory=list
            prerequisites_met=False,          # default=False
            prerequisites_completion_date=None,
            auto_generated_plan_id=None,
            progress_percentage=0.0,          # default=0.0
            created_at=datetime.utcnow(),     # default_factory; or leave out and use default
            updated_at=datetime.utcnow(),
            completed_at=None,
        )

        # Use mode='python' to preserve ObjectIds
        goal_dict = goal.model_dump(by_alias=True, exclude={"id"}, mode='python')
        
        # Convert deadline from date to datetime for MongoDB (BSON cannot serialize date objects)
        if 'deadline' in goal_dict and isinstance(goal_dict['deadline'], date) and not isinstance(goal_dict['deadline'], datetime):
            goal_dict['deadline'] = datetime.combine(goal_dict['deadline'], time.min)
        
        # Convert prerequisites_completion_date from date to datetime if present
        if 'prerequisites_completion_date' in goal_dict and goal_dict['prerequisites_completion_date']:
            if isinstance(goal_dict['prerequisites_completion_date'], date) and not isinstance(goal_dict['prerequisites_completion_date'], datetime):
                goal_dict['prerequisites_completion_date'] = datetime.combine(goal_dict['prerequisites_completion_date'], time.min)
        
        result = await self.goals_collection.insert_one(goal_dict)
        goal.id = result.inserted_id
        return goal

    async def get_goal(self, goal_id: ObjectId) -> Optional[LearningGoal]:
        """Retrieve a specific goal"""
        doc = await self.goals_collection.find_one({"_id": goal_id})
        return LearningGoal(**doc) if doc else None

    async def list_goals(
        self, user_id: ObjectId, status: Optional[str] = None
    ) -> List[LearningGoal]:
        """List user's goals"""
        query: Dict[str, Any] = {"user_id": user_id}
        if status:
            query["status"] = status  # type: ignore

        docs = await self.goals_collection.find(query).to_list(None)
        return [LearningGoal(**doc) for doc in docs]

    async def update_goal_status(
        self, goal_id: ObjectId, status: str
    ) -> Optional[LearningGoal]:
        """Update goal status"""
        result = await self.goals_collection.update_one(
            {"_id": goal_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        if result.modified_count > 0:
            return await self.get_goal(goal_id)
        return None

    # ========================================================================
    # PHASED PLAN GENERATION
    # ========================================================================

    async def generate_phased_plan(
        self,
        goal_id: ObjectId,
        user_id: ObjectId,
        study_pace: str = "moderate",
    ) -> GoalBasedPlan:
        """
        Generate a phased study plan from a goal
        
        Works backward from deadline, creating phases that respect prerequisites:
        Phase 1: Foundation topics
        Phase 2: Intermediate topics  
        Phase 3: Advanced topics
        Phase 4: Integration & practice
        
        Args:
            goal_id: Goal ID to plan from
            user_id: User creating the plan
            study_pace: slow, moderate, fast (affects daily hours)
        
        Returns:
            GoalBasedPlan with phased structure
        """
        goal = await self.get_goal(goal_id)
        if not goal:
            raise ValueError("Goal not found")

        # Calculate available study hours
        days_until_deadline = (goal.deadline - date.today()).days
        if days_until_deadline <= 0:
            raise ValueError("Deadline must be in the future")

        pace_multipliers = {"slow": 0.8, "moderate": 1.0, "fast": 1.2}
        daily_hours = {
            "slow": 2.0,
            "moderate": 3.0,
            "fast": 4.0,
        }[study_pace]

        total_available_hours = days_until_deadline * daily_hours

        if total_available_hours < goal.estimated_hours_needed:
            raise ValueError(
                f"Not enough time: need {goal.estimated_hours_needed} hours, "
                f"have {total_available_hours} hours available"
            )

        # Organize topics by difficulty
        phases = await self._organize_topics_into_phases(
            goal.subject,
            goal.topics_to_cover,
            goal.deadline,
            goal.estimated_hours_needed,
            study_pace,
        )

        # Create GoalBasedPlan
        phase_deadlines = await self._calculate_phase_deadlines(
            phases, goal.deadline
        )
        
        goal_plan = GoalBasedPlan(
            user_id=PyObjectId(user_id),
            goal_id=PyObjectId(goal_id),
            study_plan_id=PyObjectId(),  # Will be replaced by actual plan
            prerequisite_phases=phases,
            current_phase=0,
            phases_completed=0,
            phase_deadlines=[d.date() if isinstance(d, datetime) else d for d in phase_deadlines],  # Convert back to date
            status="planning",
        )

        # Use mode='python' to preserve ObjectIds
        goal_plan_dict = goal_plan.model_dump(by_alias=True, exclude={"id"}, mode='python')
        
        # Ensure phase_deadlines are datetime objects for MongoDB (BSON cannot serialize date objects)
        if 'phase_deadlines' in goal_plan_dict and goal_plan_dict['phase_deadlines']:
            goal_plan_dict['phase_deadlines'] = [
                d if isinstance(d, datetime) else datetime.combine(d, time.min)
                for d in goal_plan_dict['phase_deadlines']
            ]
        
        result = await self.goal_plans_collection.insert_one(goal_plan_dict)
        goal_plan.id = result.inserted_id

        # Update goal status
        await self.update_goal_status(goal_id, "in_progress")

        return goal_plan

    async def _organize_topics_into_phases(
        self,
        subject: str,
        topics: List[str],
        deadline: date,
        total_hours: float,
        study_pace: str,
    ) -> List[Dict]:
        """
        Organize topics into phases respecting prerequisites
        
        Returns list of phases with topics, hours, deadlines
        """
        # Group topics by difficulty
        foundation_topics = []
        intermediate_topics = []
        advanced_topics = []

        for topic in topics:
            # Get difficulty from prerequisites
            prereq = await self.prerequisite_service.get_prerequisites_for_topic(
                subject, topic
            )
            
            if prereq:
                difficulty = prereq.difficulty_level
            else:
                # Infer from name or default
                difficulty = "intermediate"

            if difficulty == "foundation":
                foundation_topics.append(topic)
            elif difficulty == "advanced":
                advanced_topics.append(topic)
            else:
                intermediate_topics.append(topic)

        # Create phases
        phases = []

        # Phase 1: Foundation (30% of time)
        if foundation_topics:
            phases.append({
                "phase_number": 1,
                "phase_name": "Foundations",
                "topics": foundation_topics,
                "difficulty_level": "foundation",
                "estimated_hours": total_hours * 0.3,
                "description": "Build core understanding of fundamentals"
            })

        # Phase 2: Intermediate (35% of time)
        if intermediate_topics:
            phases.append({
                "phase_number": 2,
                "phase_name": "Core Concepts",
                "topics": intermediate_topics,
                "difficulty_level": "intermediate",
                "estimated_hours": total_hours * 0.35,
                "description": "Develop deeper understanding and problem-solving skills"
            })

        # Phase 3: Advanced (20% of time)
        if advanced_topics:
            phases.append({
                "phase_number": 3,
                "phase_name": "Advanced Topics",
                "topics": advanced_topics,
                "difficulty_level": "advanced",
                "estimated_hours": total_hours * 0.2,
                "description": "Master complex applications and edge cases"
            })

        # Phase 4: Integration & Practice (15% of time)
        phases.append({
            "phase_number": 4 if advanced_topics else 3,
            "phase_name": "Integration & Practice",
            "topics": topics,  # All topics
            "difficulty_level": "practice",
            "estimated_hours": total_hours * 0.15,
            "description": "Integrate knowledge and practice with real problems"
        })

        return phases

    async def _calculate_phase_deadlines(
        self,
        phases: List[Dict],
        goal_deadline: date,
    ) -> List[datetime]:
        """Calculate deadline for each phase, returning datetime objects for MongoDB compatibility"""
        total_hours = sum(p["estimated_hours"] for p in phases)
        deadlines = []
        current_date = date.today()

        for phase in phases:
            phase_progress = phase["estimated_hours"] / total_hours
            days_for_phase = int((goal_deadline - current_date).days * phase_progress)
            phase_deadline = current_date + timedelta(days=days_for_phase)
            # Convert to datetime for MongoDB storage (BSON cannot serialize date objects)
            phase_deadline_dt = datetime.combine(phase_deadline, time.min)
            deadlines.append(phase_deadline_dt)
            current_date = phase_deadline

        return deadlines

    # ========================================================================
    # TOPIC EXPANSION & ESTIMATION
    # ========================================================================

    async def _expand_topics_with_prerequisites(
        self, subject: str, topics: List[str]
    ) -> List[str]:
        """Expand topic list to include prerequisites"""
        expanded = set(topics)

        for topic in topics:
            prereqs = await self.prerequisite_service.get_prerequisites_for_topic(
                subject, topic
            )
            if prereqs:
                expanded.update(prereqs.prerequisite_topics)

        return list(expanded)

    async def _estimate_hours_for_topics(
        self, subject: str, topics: List[str]
    ) -> float:
        """Estimate total hours needed for topics"""
        # Get chain information if available
        chains = await self.db["prerequisite_chains"].find(
            {"subject": subject}
        ).to_list(None)

        total_hours = 0.0

        for topic in topics:
            # Check if topic is in any chain
            found_hours = False
            for chain in chains:
                if topic in chain["topics_ordered"]:
                    idx = chain["topics_ordered"].index(topic)
                    total_hours += chain["estimated_hours_per_topic"][idx]
                    found_hours = True
                    break

            if not found_hours:
                # Default estimate: foundation=8, intermediate=12, advanced=15
                prereq = await self.prerequisite_service.get_prerequisites_for_topic(
                    subject, topic
                )
                if prereq:
                    difficulty = prereq.difficulty_level
                else:
                    difficulty = "intermediate"

                default_hours = {
                    "foundation": 8.0,
                    "intermediate": 12.0,
                    "advanced": 15.0,
                }.get(difficulty, 10.0)

                total_hours += default_hours

        return total_hours

    # ========================================================================
    # PROGRESS TRACKING
    # ========================================================================

    async def update_goal_progress(
        self, goal_id: ObjectId, topics_completed: List[str]
    ) -> Dict:
        """Update progress on a goal"""
        goal = await self.get_goal(goal_id)
        if not goal:
            raise ValueError("Goal not found")

        total_topics = len(goal.topics_to_cover)
        completed_topics = len(topics_completed)
        progress_percentage = (completed_topics / total_topics * 100) if total_topics > 0 else 0

        await self.goals_collection.update_one(
            {"_id": goal_id},
            {
                "$set": {
                    "progress_percentage": progress_percentage,
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        # Check if goal is completed
        if completed_topics == total_topics:
            await self.update_goal_status(goal_id, "completed")

        return {
            "goal_id": str(goal_id),
            "total_topics": total_topics,
            "completed_topics": completed_topics,
            "progress_percentage": progress_percentage,
            "topics_completed": topics_completed,
            "topics_remaining": [
                t for t in goal.topics_to_cover if t not in topics_completed
            ],
        }

    async def get_goal_progress(self, goal_id: ObjectId) -> Dict:
        """Get detailed progress on a goal"""
        goal = await self.get_goal(goal_id)
        if not goal:
            raise ValueError("Goal not found")

        goal_plan = await self.goal_plans_collection.find_one({"goal_id": goal_id})

        # Calculate which topics are completed in study plans
        plans = await self.study_plans_collection.find(
            {"user_id": goal.user_id}
        ).to_list(None)

        completed_topics = []
        for plan in plans:
            tasks = await self.db["study_tasks"].find(
                {"plan_id": ObjectId(plan["_id"]), "status": "completed"}
            ).to_list(None)
            for task in tasks:
                if task["topic"] in goal.topics_to_cover:
                    completed_topics.append(task["topic"])

        completed_topics = list(set(completed_topics))  # Deduplicate

        # Format phase deadlines (convert datetime to ISO format)
        phase_deadlines_iso = []
        if goal_plan and goal_plan.get("phase_deadlines"):
            for deadline in goal_plan["phase_deadlines"]:
                if isinstance(deadline, datetime):
                    phase_deadlines_iso.append(deadline.isoformat())
                elif isinstance(deadline, date):
                    phase_deadlines_iso.append(deadline.isoformat())
                else:
                    phase_deadlines_iso.append(str(deadline))

        return {
            "goal_id": str(goal_id),
            "goal_title": goal.goal_title,
            "deadline": goal.deadline.isoformat(),
            "days_remaining": (goal.deadline - date.today()).days,
            "progress_percentage": (
                (len(completed_topics) / len(goal.topics_to_cover) * 100)
                if goal.topics_to_cover
                else 0
            ),
            "topics_completed": completed_topics,
            "topics_remaining": [
                t for t in goal.topics_to_cover if t not in completed_topics
            ],
            "current_phase": goal_plan["current_phase"] if goal_plan else 0,
            "total_phases": len(goal_plan["prerequisite_phases"]) if goal_plan else 0,
            "phase_deadlines": phase_deadlines_iso,
            "on_track": self._check_if_on_track(goal, completed_topics),
        }

    def _check_if_on_track(self, goal: LearningGoal, completed_topics: List[str]) -> bool:
        """Check if goal progress is on track"""
        days_total = (goal.deadline - date.today()).days
        if days_total <= 0:
            return len(completed_topics) == len(goal.topics_to_cover)

        # Should be at least 50% done by the midpoint
        midpoint_date = date.today() + timedelta(days=days_total // 2)
        days_elapsed = (date.today() - (date.today() - timedelta(days=days_total))).days
        
        expected_progress = (days_elapsed / days_total) * 100
        actual_progress = (len(completed_topics) / len(goal.topics_to_cover) * 100) if goal.topics_to_cover else 0
        
        return actual_progress >= (expected_progress * 0.8)  # Allow 20% slack

    # ========================================================================
    # RECOMMENDATION ENGINE
    # ========================================================================

    async def get_goal_recommendations(self, goal_id: ObjectId) -> Dict:
        """
        Get recommendations to stay on track with goal
        """
        goal = await self.get_goal(goal_id)
        if not goal:
            raise ValueError("Goal not found")

        progress = await self.get_goal_progress(goal_id)
        recommendations = []

        days_remaining = progress["days_remaining"]
        progress_pct = progress["progress_percentage"]

        # Recommendation 1: Pace check
        expected_progress = (1 - (days_remaining / (goal.deadline - date.today()).days)) * 100
        if progress_pct < expected_progress * 0.8:
            recommendations.append({
                "type": "pace_warning",
                "severity": "high",
                "message": f"Behind on pace. You're at {progress_pct:.0f}% but should be at {expected_progress:.0f}%",
                "action": "Increase daily study hours or adjust deadline",
            })
        elif progress_pct > expected_progress * 1.2:
            recommendations.append({
                "type": "pace_ahead",
                "severity": "info",
                "message": f"Ahead of pace! You're at {progress_pct:.0f}% (expected {expected_progress:.0f}%)",
                "action": "Great progress! Maintain momentum.",
            })

        # Recommendation 2: Phase check
        goal_plan = await self.goal_plans_collection.find_one({"goal_id": goal_id})
        if goal_plan:
            current_phase = goal_plan["current_phase"]
            phase_deadlines = goal_plan["phase_deadlines"]
            
            if current_phase < len(phase_deadlines):
                phase_deadline = phase_deadlines[current_phase]
                # Convert datetime to date for comparison (BSON stores as datetime)
                if isinstance(phase_deadline, datetime):
                    phase_deadline_date = phase_deadline.date()
                else:
                    phase_deadline_date = phase_deadline
                
                days_until_phase_deadline = (phase_deadline_date - date.today()).days
                
                if days_until_phase_deadline < 0:
                    recommendations.append({
                        "type": "phase_overdue",
                        "severity": "high",
                        "message": f"Phase {current_phase + 1} deadline passed {abs(days_until_phase_deadline)} days ago",
                        "action": "Focus on completing current phase ASAP",
                    })
                elif days_until_phase_deadline <= 3:
                    recommendations.append({
                        "type": "phase_deadline_soon",
                        "severity": "medium",
                        "message": f"Phase {current_phase + 1} deadline in {days_until_phase_deadline} days",
                        "action": "Accelerate phase completion",
                    })

        # Recommendation 3: Topics to focus on
        remaining_topics = progress["topics_remaining"]
        if remaining_topics:
            recommendations.append({
                "type": "focus_topics",
                "severity": "info",
                "message": f"Topics to master: {', '.join(remaining_topics[:3])}",
                "action": "Create study sessions for these topics",
            })

        return {
            "goal_id": str(goal_id),
            "recommendations": recommendations,
            "on_track": progress["on_track"],
            "suggested_daily_hours": math.ceil(
                goal.estimated_hours_needed / (days_remaining or 1)
            ) if days_remaining > 0 else 0,
        }