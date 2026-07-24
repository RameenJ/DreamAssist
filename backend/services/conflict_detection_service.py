"""
Multi-Plan Conflict Detection Service (Phase 2c)
Detects when multiple study plans compete for time/resources and suggests resolutions
"""

from typing import List, Dict, Optional, Tuple, Set
from datetime import date, datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import asyncio

from models.user_schemas import PyObjectId
from models.phase2_schemas import PlanConflict, ConflictResolutionSuggestion
from typing import cast, Any



class ConflictDetectionService:
    """Service for detecting and resolving multi-plan conflicts"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.conflicts_collection = db["plan_conflicts"]
        self.study_plans_collection = db["study_plans"]
        self.study_sessions_collection = db["study_sessions"]

    # ========================================================================
    # CONFLICT DETECTION
    # ========================================================================

    async def detect_conflicts(
        self, user_id: ObjectId
    ) -> Tuple[List[PlanConflict], Dict]:
        """
        Detect all conflicts in user's plans
        
        Returns:
            Tuple of (list of conflicts, summary dict)
        """
        # Get all active plans
        plans = await self.study_plans_collection.find(
            {"user_id": user_id, "status": "active"}
        ).to_list(None)

        if len(plans) < 2:
            return [], {"total_conflicts": 0, "affected_hours": 0.0}

        detected_conflicts = []

        # Check for time overlaps
        time_conflicts = await self._detect_time_overlaps(user_id, plans)
        detected_conflicts.extend(time_conflicts)

        # Check for resource exhaustion
        resource_conflicts = await self._detect_resource_exhaustion(user_id, plans)
        detected_conflicts.extend(resource_conflicts)

        # Check for priority clashes
        priority_conflicts = await self._detect_priority_clashes(user_id, plans)
        detected_conflicts.extend(priority_conflicts)

        # Calculate summary
        summary = {
            "total_conflicts": len(detected_conflicts),
            "affected_hours": sum(c.affected_total_hours for c in detected_conflicts),
            "conflict_types": self._count_conflict_types(detected_conflicts),
            "severity_breakdown": self._breakdown_by_severity(detected_conflicts),
        }

        return detected_conflicts, summary

    async def _detect_time_overlaps(
        self, user_id: ObjectId, plans: List[Dict]
    ) -> List[PlanConflict]:
        """Detect when plans schedule sessions on same dates"""
        conflicts = []

        # Get all sessions for each plan
        plan_sessions = {}
        for plan in plans:
            sessions = await self.study_sessions_collection.find(
                {"plan_id": ObjectId(plan["_id"])}
            ).to_list(None)
            plan_sessions[str(plan["_id"])] = sessions

        # Check for date overlaps
        date_to_plans = {}
        for plan_id, sessions in plan_sessions.items():
            for session in sessions:
                session_date = session.get("session_date")
                if session_date:
                    if session_date not in date_to_plans:
                        date_to_plans[session_date] = []
                    date_to_plans[session_date].append(plan_id)

        # Find dates with multiple plans
        for session_date, plan_ids in date_to_plans.items():
            if len(plan_ids) > 1:
                # Get plan names
                plan_names = []
                affected_hours = 0.0
                for plan_id in plan_ids:
                    plan = next(
                        p for p in plans if str(p["_id"]) == plan_id
                    )
                    plan_names.append(plan.get("plan_name", "Unnamed"))

                    # Calculate hours for this plan on this date
                    sessions = plan_sessions[plan_id]
                    for s in sessions:
                        if s.get("session_date") == session_date:
                            time_blocks = s.get("time_blocks", [])
                            affected_hours += len(time_blocks) * 1  # Assume 1 hr per block

                conflict = PlanConflict(
                    user_id=cast(PyObjectId, user_id),   # user_id is ObjectId
                    conflict_date=session_date,
                    plan_ids=[cast(PyObjectId, ObjectId(pid)) for pid in plan_ids],
                    plan_names=plan_names,
                    conflict_type="time_overlap",
                    conflict_description=f"Multiple plans scheduled on {session_date}: {', '.join(plan_names)}",
                    severity="high" if affected_hours > 6 else "medium",
                    affected_sessions_count=len(plan_ids),
                    affected_total_hours=affected_hours,
                    is_resolved=False,
                    resolution_type=None,           # ✅
                    resolution_details=None,        # ✅
                    user_resolution_suggested=None, # ✅
                    resolved_at=None,               # ✅
                )

                conflict_dict = conflict.dict(by_alias=True, exclude={"id"})
                if isinstance(conflict_dict.get("conflict_date"), date) and not isinstance(conflict_dict.get("conflict_date"), datetime):
                    conflict_dict["conflict_date"] = datetime.combine(conflict_dict["conflict_date"], datetime.min.time())
                result = await self.conflicts_collection.insert_one(conflict_dict)
                conflict.id = result.inserted_id
                conflicts.append(conflict)

        return conflicts

    async def _detect_resource_exhaustion(
        self, user_id: ObjectId, plans: List[Dict]
    ) -> List[PlanConflict]:
        """Detect when total study hours exceed max (resource exhaustion)"""
        conflicts = []

        # Get user preferences to find max daily hours
        user_prefs = await self.db["user_plan_preferences"].find_one(
            {"user_id": user_id}
        )
        max_daily_hours = user_prefs.get("max_daily_study_hours", 8.0) if user_prefs else 8.0

        # Calculate total hours per day across all plans
        date_to_hours = {}
        for plan in plans:
            sessions = await self.study_sessions_collection.find(
                {"plan_id": ObjectId(plan["_id"])}
            ).to_list(None)

            for session in sessions:
                session_date = session.get("session_date")
                if session_date:
                    if session_date not in date_to_hours:
                        date_to_hours[session_date] = []
                    
                    # Sum hours in this session
                    time_blocks = session.get("time_blocks", [])
                    hours = len(time_blocks) * 1  # Assume 1 hr per block
                    date_to_hours[session_date].append({
                        "plan_id": plan["_id"],
                        "plan_name": plan.get("plan_name", "Unnamed"),
                        "hours": hours,
                    })

        # Find days exceeding max
        for session_date, hour_entries in date_to_hours.items():
            total_hours = sum(e["hours"] for e in hour_entries)
            if total_hours > max_daily_hours:
                plan_names = [e["plan_name"] for e in hour_entries]
                plan_ids = [ObjectId(e["plan_id"]) for e in hour_entries]

                conflict = PlanConflict(
                    user_id=PyObjectId(user_id),
                    conflict_date=session_date,
                    plan_ids=cast(List[PyObjectId], plan_ids),
                    plan_names=plan_names,
                    conflict_type="resource_exhaustion",
                    conflict_description=f"Total study load on {session_date} is {total_hours:.1f} hours "
                                        f"(max: {max_daily_hours} hours)",
                    severity="high",
                    affected_sessions_count=len(hour_entries),
                    affected_total_hours=total_hours,
                    is_resolved=False,
                    resolution_type=None,           # ✅
                    resolution_details=None,        # ✅
                    user_resolution_suggested=None, # ✅
                    resolved_at=None,               # ✅
                )

                conflict_dict = conflict.dict(by_alias=True, exclude={"id"})
                if isinstance(conflict_dict.get("conflict_date"), date) and not isinstance(conflict_dict.get("conflict_date"), datetime):
                    conflict_dict["conflict_date"] = datetime.combine(conflict_dict["conflict_date"], datetime.min.time())
                result = await self.conflicts_collection.insert_one(conflict_dict)
                conflict.id = result.inserted_id
                conflicts.append(conflict)

        return conflicts

    async def _detect_priority_clashes(
        self, user_id: ObjectId, plans: List[Dict]
    ) -> List[PlanConflict]:
        """Detect when plans have competing priorities"""
        conflicts = []

        # Get all plans with their priorities
        high_priority_plans = [p for p in plans if p.get("status") == "active"]
        
        # If multiple high-priority plans with same subjects, it's a clash
        subject_to_plans = {}
        for plan in high_priority_plans:
            for subject in plan.get("subjects", []):
                if subject not in subject_to_plans:
                    subject_to_plans[subject] = []
                subject_to_plans[subject].append(plan)

        # Find subjects with competing plans
        for subject, competing_plans in subject_to_plans.items():
            if len(competing_plans) > 1:
                # This is a priority clash
                plan_names = [p.get("plan_name", "Unnamed") for p in competing_plans]
                plan_ids = [ObjectId(p["_id"]) for p in competing_plans]

                # Calculate when conflict starts
                min_start_date = min(
                    datetime.fromisoformat(p["start_date"]).date()
                    if isinstance(p["start_date"], str)
                    else p["start_date"]
                    for p in competing_plans
                )


                conflict = PlanConflict(
                    user_id=cast(PyObjectId, user_id),
                    conflict_date=min_start_date,
                    plan_ids=cast(List[PyObjectId], plan_ids),
                    plan_names=plan_names,
                    conflict_type="priority_clash",
                    conflict_description=f"Multiple plans for subject '{subject}': {', '.join(plan_names)}. "
                                        f"Consider merging similar topics.",
                    severity="medium",
                    affected_sessions_count=len(competing_plans),
                    affected_total_hours=sum(p.get("total_available_hours", 0) for p in competing_plans),
                    is_resolved=False,
                    resolution_type=None,           # ✅
                    resolution_details=None,        # ✅
                    user_resolution_suggested=None, # ✅
                    resolved_at=None,               # ✅
                )

                conflict_dict = conflict.dict(by_alias=True, exclude={"id"})
                if isinstance(conflict_dict.get("conflict_date"), date) and not isinstance(conflict_dict.get("conflict_date"), datetime):
                    conflict_dict["conflict_date"] = datetime.combine(conflict_dict["conflict_date"], datetime.min.time())
                result = await self.conflicts_collection.insert_one(conflict_dict)
                conflict.id = result.inserted_id
                conflicts.append(conflict)

        return conflicts

    # ========================================================================
    # RESOLUTION SUGGESTIONS
    # ========================================================================

    async def suggest_resolutions(
        self, conflict_id: ObjectId
    ) -> List[ConflictResolutionSuggestion]:
        """
        Generate resolution suggestions for a conflict
        """
        conflict_doc = await self.conflicts_collection.find_one({"_id": conflict_id})
        if not conflict_doc:
            return []

        conflict = PlanConflict(**conflict_doc)
        suggestions = []

        if conflict.conflict_type == "time_overlap":
            suggestions.extend(
                await self._suggest_time_overlap_resolutions(conflict)
            )
        elif conflict.conflict_type == "resource_exhaustion":
            suggestions.extend(
                await self._suggest_resource_resolutions(conflict)
            )
        elif conflict.conflict_type == "priority_clash":
            suggestions.extend(
                await self._suggest_priority_resolutions(conflict)
            )

        return suggestions

    async def _suggest_time_overlap_resolutions(
        self, conflict: PlanConflict
    ) -> List[ConflictResolutionSuggestion]:
        """Suggest resolutions for time overlap conflicts"""
        suggestions = []

        # Suggestion 1: Reschedule one plan
        for plan_id in conflict.plan_ids:
            plan = await self.study_plans_collection.find_one({"_id": plan_id})
            if plan:
                days_to_deadline = (
                    datetime.fromisoformat(plan["end_date"]).date()
                    if isinstance(plan["end_date"], str)
                    else plan["end_date"]
                ) - date.today()

                if days_to_deadline.days > 7:

                    suggestion = ConflictResolutionSuggestion(
                        conflict_id=cast(PyObjectId, conflict.id),
                        suggestion_type="extend_deadline",   # ✅ must be in the Literal set
                        affected_plans=[plan.get("plan_name", "Unnamed")],
                        new_hours_distribution=None,         # ✅
                        days_to_extend=7,
                        new_deadline=(conflict.conflict_date + timedelta(days=7)),
                        can_merge_topics=None,               # ✅
                        deprioritize_plan=None,              # ✅
                        confidence_score=0.8,
                        impact_score=0.3,
                    )
                    suggestions.append(suggestion)

        # Suggestion 2: Merge sessions (study both subjects together)
        suggestion = ConflictResolutionSuggestion(
            conflict_id=conflict.id,  # maybe need cast to PyObjectId if conflict.id is ObjectId
            suggestion_type="merge_similar",
            affected_plans=conflict.plan_names,
            can_merge_topics=["related topics that can be studied together"],
            confidence_score=0.6,
            impact_score=0.1,
            # Explicitly set unused optional fields to None
            new_hours_distribution=None,
            days_to_extend=None,
            new_deadline=None,
            deprioritize_plan=None,
        )
        suggestions.append(suggestion)

        # Suggestion 3: Redistribute hours
        total_hours = conflict.affected_total_hours
        per_plan = total_hours / len(conflict.plan_ids)
        suggestion = ConflictResolutionSuggestion(
            conflict_id=conflict.id,  # add cast if needed: cast(PyObjectId, conflict.id)
            suggestion_type="redistribute_hours",
            affected_plans=conflict.plan_names,
            new_hours_distribution={
                name: per_plan for name in conflict.plan_names
            },
            confidence_score=0.7,
            impact_score=0.2,
            days_to_extend=None,      # ✅
            new_deadline=None,        # ✅
            can_merge_topics=None,    # ✅
            deprioritize_plan=None,   # ✅
        )
        suggestions.append(suggestion)

        return suggestions

    async def _suggest_resource_resolutions(
        self, conflict: PlanConflict
    ) -> List[ConflictResolutionSuggestion]:
        """Suggest resolutions for resource exhaustion conflicts"""
        suggestions = []

        # Get total available hours
        total_hours = conflict.affected_total_hours
        excess_hours = total_hours - 8.0  # Assume 8hr max

        # Suggestion 1: Extend deadlines
        if len(conflict.plan_ids) > 1:
            for plan_id in conflict.plan_ids:
                plan = await self.study_plans_collection.find_one({"_id": plan_id})
                if plan:
                    days_to_extend = int(excess_hours / 2)  # Add 2 hrs per day
                    suggestion = ConflictResolutionSuggestion(
                        conflict_id=conflict.id,  # add cast if needed: cast(PyObjectId, conflict.id)
                        suggestion_type="extend_deadline",
                        affected_plans=[plan.get("plan_name", "Unnamed")],
                        days_to_extend=days_to_extend,
                        new_deadline=conflict.conflict_date + timedelta(days=days_to_extend),
                        confidence_score=0.85,
                        impact_score=-0.3,
                        new_hours_distribution=None,  # ✅
                        can_merge_topics=None,        # ✅
                        deprioritize_plan=None,       # ✅
                    )
                    suggestions.append(suggestion)

        # Suggestion 2: Deprioritize one plan
        for plan_name in conflict.plan_names[1:]:  # Skip first (highest priority)
            suggestion = ConflictResolutionSuggestion(
                conflict_id=conflict.id,  # add cast(PyObjectId, conflict.id) if needed
                suggestion_type="deprioritize",  # ✅ must match Literal "deprioritize"
                affected_plans=[plan_name],
                deprioritize_plan=plan_name,
                confidence_score=0.6,
                impact_score=-0.4,
                new_hours_distribution=None,  # ✅
                days_to_extend=None,          # ✅
                new_deadline=None,            # ✅
                can_merge_topics=None,        # ✅
            )
            suggestions.append(suggestion)

        return suggestions

    async def _suggest_priority_resolutions(
        self, conflict: PlanConflict
    ) -> List[ConflictResolutionSuggestion]:
        """Suggest resolutions for priority clashes"""
        suggestions = []

        # Suggestion 1: Merge similar topics
        suggestion = ConflictResolutionSuggestion(
            conflict_id=conflict.id,  # add cast(PyObjectId, conflict.id) if needed
            suggestion_type="merge_similar",
            affected_plans=conflict.plan_names,
            can_merge_topics=[
                "Topics that appear in both plans can be studied once"
            ],
            confidence_score=0.8,
            impact_score=0.5,
            new_hours_distribution=None,  # ✅
            days_to_extend=None,          # ✅
            new_deadline=None,            # ✅
            deprioritize_plan=None,       # ✅
        )
        suggestions.append(suggestion)

        # Suggestion 2: Create unified plan
        suggestion = ConflictResolutionSuggestion(
            conflict_id=conflict.id,  # add cast(PyObjectId, conflict.id) if needed
            suggestion_type="merge_similar",
            affected_plans=conflict.plan_names,
            can_merge_topics=["All topics combined into single unified plan"],
            confidence_score=0.7,
            impact_score=0.6,
            new_hours_distribution=None,  # ✅
            days_to_extend=None,          # ✅
            new_deadline=None,            # ✅
            deprioritize_plan=None,       # ✅
        )
        suggestions.append(suggestion)

        return suggestions

    # ========================================================================
    # RESOLUTION EXECUTION
    # ========================================================================

    async def apply_resolution(
        self,
        conflict_id: ObjectId,
        suggestion_type: str,
        resolution_details: Dict,
    ) -> bool:
        """Apply a resolution to a conflict"""
        conflict = await self.conflicts_collection.find_one({"_id": conflict_id})
        if not conflict:
            return False

        # Execute resolution based on type
        
        if suggestion_type == "reschedule":
            await self._reschedule_plan(
                conflict["plan_ids"][0],
                cast(date, resolution_details.get("new_deadline")),         
            )
        elif suggestion_type == "extend_deadline":
            await self._extend_plan_deadline(
                conflict["plan_ids"][0],
                resolution_details.get("days_to_extend", 7),
            )
        elif suggestion_type == "deprioritize":
            await self._deprioritize_plan(
                conflict["plan_ids"][0]
            )

        # Mark conflict as resolved
        await self.conflicts_collection.update_one(
            {"_id": conflict_id},
            {
                "$set": {
                    "is_resolved": True,
                    "resolution_type": suggestion_type,
                    "resolution_details": resolution_details,
                    "resolved_at": datetime.utcnow(),
                }
            },
        )

        return True

    async def _reschedule_plan(
        self, plan_id: ObjectId, new_deadline: date
    ) -> bool:
        """Reschedule a plan to a new deadline"""
        result = await self.study_plans_collection.update_one(
            {"_id": plan_id},
            {
                "$set": {
                    "end_date": new_deadline.isoformat(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    async def _extend_plan_deadline(
        self, plan_id: ObjectId, days: int
    ) -> bool:
        """Extend a plan's deadline"""
        plan = await self.study_plans_collection.find_one({"_id": plan_id})
        if not plan:
            return False

        end_date = (
            datetime.fromisoformat(plan["end_date"]).date()
            if isinstance(plan["end_date"], str)
            else plan["end_date"]
        )
        new_deadline = end_date + timedelta(days=days)

        result = await self.study_plans_collection.update_one(
            {"_id": plan_id},
            {
                "$set": {
                    "end_date": new_deadline.isoformat(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    async def _deprioritize_plan(self, plan_id: ObjectId) -> bool:
        """Mark a plan as lower priority (pause it)"""
        result = await self.study_plans_collection.update_one(
            {"_id": plan_id},
            {
                "$set": {
                    "status": "paused",
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def _count_conflict_types(self, conflicts: List[PlanConflict]) -> Dict[str, int]:
        """Count conflicts by type"""
        counts = {}
        for conflict in conflicts:
            counts[conflict.conflict_type] = counts.get(conflict.conflict_type, 0) + 1
        return counts

    def _breakdown_by_severity(self, conflicts: List[PlanConflict]) -> Dict[str, int]:
        """Break down conflicts by severity"""
        counts = {}
        for conflict in conflicts:
            counts[conflict.severity] = counts.get(conflict.severity, 0) + 1
        return counts

    async def get_conflict(self, conflict_id: ObjectId) -> Optional[PlanConflict]:
        """Retrieve a specific conflict"""
        doc = await self.conflicts_collection.find_one({"_id": conflict_id})
        return PlanConflict(**doc) if doc else None


    async def list_conflicts(
        self, user_id: ObjectId, resolved: Optional[bool] = None
    ) -> List[PlanConflict]:
        query: Dict[str, Any] = {"user_id": user_id}
        if resolved is not None:
            query["is_resolved"] = resolved
        docs = await self.conflicts_collection.find(query).to_list(None)
        return [PlanConflict(**doc) for doc in docs]