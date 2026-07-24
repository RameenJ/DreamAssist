"""
Tests for Goal-Based Planning Service (Phase 2b) and Conflict Detection Service (Phase 2c)
"""

import pytest
import asyncio
from datetime import date, datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.goal_based_planning_service import GoalBasedPlanningService
from backend.services.conflict_detection_service import ConflictDetectionService
from backend.models.phase2_schemas import LearningGoal, GoalBasedPlan, PlanConflict


# ========================================================================
# FIXTURES
# ========================================================================


@pytest.fixture
async def mock_db():
    """Create a mock MongoDB database"""
    db = AsyncMock(spec=AsyncIOMotorDatabase)
    
    # Mock collections
    db.__getitem__ = MagicMock()
    db.__getitem__.return_value = AsyncMock()
    
    return db


@pytest.fixture
async def planning_service(mock_db):
    """Create GoalBasedPlanningService instance"""
    service = GoalBasedPlanningService(mock_db)
    return service


@pytest.fixture
async def conflict_service(mock_db):
    """Create ConflictDetectionService instance"""
    service = ConflictDetectionService(mock_db)
    return service


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return ObjectId()


@pytest.fixture
def test_goal_id():
    """Test goal ID"""
    return ObjectId()


@pytest.fixture
def test_deadline():
    """Test deadline (30 days from now)"""
    return date.today() + timedelta(days=30)


# ========================================================================
# GOAL-BASED PLANNING SERVICE TESTS
# ========================================================================


@pytest.mark.asyncio
async def test_create_goal_basic(planning_service, test_user_id, test_deadline):
    """Test basic goal creation"""
    planning_service.goals_collection.insert_one = AsyncMock(
        return_value=AsyncMock(inserted_id=ObjectId())
    )
    
    goal = await planning_service.create_goal(
        user_id=test_user_id,
        goal_title="Master DSA",
        goal_type="skill_acquisition",
        subject="DSA",
        topics_to_cover=["Arrays", "Linked Lists", "Trees"],
        target_score=90,
        deadline=test_deadline,
        priority="high",
        include_prerequisites=False,
    )
    
    assert goal is not None
    assert goal.goal_title == "Master DSA"
    assert goal.subject == "DSA"
    assert goal.status == "not_started"
    assert len(goal.topics_to_cover) == 3


@pytest.mark.asyncio
async def test_create_goal_with_prerequisites(planning_service, test_user_id, test_deadline):
    """Test goal creation with prerequisite expansion"""
    planning_service.goals_collection.insert_one = AsyncMock(
        return_value=AsyncMock(inserted_id=ObjectId())
    )
    
    # Mock prerequisite service
    with patch.object(
        planning_service.prerequisite_service,
        'get_prerequisites_for_topic',
        new_callable=AsyncMock
    ) as mock_get_prereqs:
        mock_get_prereqs.return_value = None
        
        goal = await planning_service.create_goal(
            user_id=test_user_id,
            goal_title="DSA Expert",
            goal_type="skill_acquisition",
            subject="DSA",
            topics_to_cover=["Trees"],
            target_score=95,
            deadline=test_deadline,
            include_prerequisites=True,
        )
        
        assert goal is not None


@pytest.mark.asyncio
async def test_estimate_hours_for_topics(planning_service):
    """Test hours estimation"""
    # Mock database
    planning_service.db.__getitem__.return_value.find.return_value.to_list = AsyncMock(
        return_value=[]
    )
    
    # Mock prerequisite service
    with patch.object(
        planning_service.prerequisite_service,
        'get_prerequisites_for_topic',
        new_callable=AsyncMock
    ) as mock_get_prereqs:
        from backend.models.phase2_schemas import TopicPrerequisiteMapping
        
        mock_prereq = TopicPrerequisiteMapping(
            topic="Arrays",
            subject="DSA",
            difficulty_level="foundation",
            prerequisite_topics=[],
            estimated_hours=10,
        )
        mock_get_prereqs.return_value = mock_prereq
        
        hours = await planning_service._estimate_hours_for_topics("DSA", ["Arrays"])
        
        assert hours == 10.0


@pytest.mark.asyncio
async def test_generate_phased_plan_success(planning_service, test_user_id, test_goal_id, test_deadline):
    """Test successful phased plan generation"""
    goal = LearningGoal(
        id=test_goal_id,
        user_id=test_user_id,
        goal_title="Master DSA",
        goal_type="skill_acquisition",
        subject="DSA",
        topics_to_cover=["Arrays", "Linked Lists", "Trees", "Graphs"],
        target_score=90,
        deadline=test_deadline,
        priority="high",
        estimated_hours_needed=40,
        status="not_started",
    )
    
    planning_service.get_goal = AsyncMock(return_value=goal)
    planning_service.goal_plans_collection.insert_one = AsyncMock(
        return_value=AsyncMock(inserted_id=ObjectId())
    )
    
    # Mock prerequisite service
    with patch.object(
        planning_service.prerequisite_service,
        'get_prerequisites_for_topic',
        new_callable=AsyncMock
    ) as mock_get_prereqs:
        mock_get_prereqs.return_value = None
        
        plan = await planning_service.generate_phased_plan(
            goal_id=test_goal_id,
            user_id=test_user_id,
            study_pace="moderate",
        )
        
        assert plan is not None
        assert len(plan.prerequisite_phases) > 0


@pytest.mark.asyncio
async def test_generate_phased_plan_insufficient_time(planning_service, test_user_id, test_goal_id):
    """Test phased plan generation with insufficient time"""
    goal = LearningGoal(
        id=test_goal_id,
        user_id=test_user_id,
        goal_title="Master Complex Subject",
        goal_type="skill_acquisition",
        subject="DSA",
        topics_to_cover=["Complex Topics"],
        deadline=date.today() + timedelta(days=1),  # Only 1 day
        estimated_hours_needed=100,  # 100 hours needed
        status="not_started",
    )
    
    planning_service.get_goal = AsyncMock(return_value=goal)
    
    with pytest.raises(ValueError):
        await planning_service.generate_phased_plan(
            goal_id=test_goal_id,
            user_id=test_user_id,
            study_pace="moderate",
        )


@pytest.mark.asyncio
async def test_update_goal_progress(planning_service, test_goal_id):
    """Test goal progress update"""
    planning_service.goals_collection.update_one = AsyncMock(
        return_value=AsyncMock(modified_count=1)
    )
    planning_service.get_goal = AsyncMock(return_value=None)
    
    # First get should fail for demo, but update should succeed
    planning_service.goals_collection.find_one = AsyncMock(
        return_value={
            "_id": test_goal_id,
            "user_id": ObjectId(),
            "goal_title": "Test",
            "topics_to_cover": ["Topic1", "Topic2", "Topic3"],
        }
    )
    
    progress = await planning_service.update_goal_progress(
        test_goal_id,
        ["Topic1", "Topic2"],
    )
    
    assert progress is not None
    assert progress["completed_topics"] == 2
    assert progress["total_topics"] == 3


@pytest.mark.asyncio
async def test_goal_progress_on_track(planning_service):
    """Test on-track detection"""
    goal = LearningGoal(
        id=ObjectId(),
        user_id=ObjectId(),
        goal_title="Test Goal",
        goal_type="skill_acquisition",
        subject="DSA",
        topics_to_cover=["T1", "T2", "T3", "T4"],
        deadline=date.today() + timedelta(days=30),
        estimated_hours_needed=40,
        status="in_progress",
    )
    
    # Completed 2 out of 4 = 50% (should be roughly on track)
    completed = ["T1", "T2"]
    
    on_track = planning_service._check_if_on_track(goal, completed)
    
    assert on_track is True


# ========================================================================
# CONFLICT DETECTION SERVICE TESTS
# ========================================================================


@pytest.mark.asyncio
async def test_detect_time_overlaps(conflict_service, test_user_id):
    """Test time overlap detection"""
    plan1_id = ObjectId()
    plan2_id = ObjectId()
    session_date = date.today() + timedelta(days=5)
    
    # Mock plans
    plans = [
        {"_id": plan1_id, "plan_name": "DSA Study"},
        {"_id": plan2_id, "plan_name": "Web Dev Study"},
    ]
    
    # Mock sessions
    sessions1 = [
        {
            "plan_id": plan1_id,
            "session_date": session_date,
            "time_blocks": [1, 2],  # 2 hours
        }
    ]
    sessions2 = [
        {
            "plan_id": plan2_id,
            "session_date": session_date,
            "time_blocks": [1, 2],  # 2 hours
        }
    ]
    
    conflict_service.study_sessions_collection.find = MagicMock()
    
    async def mock_find(query):
        mock_cursor = AsyncMock()
        if query.get("plan_id") == plan1_id:
            mock_cursor.to_list = AsyncMock(return_value=sessions1)
        elif query.get("plan_id") == plan2_id:
            mock_cursor.to_list = AsyncMock(return_value=sessions2)
        else:
            mock_cursor.to_list = AsyncMock(return_value=[])
        return mock_cursor
    
    conflict_service.study_sessions_collection.find.side_effect = mock_find
    
    conflicts = await conflict_service._detect_time_overlaps(test_user_id, plans)
    
    assert len(conflicts) > 0
    assert conflicts[0].conflict_type == "time_overlap"


@pytest.mark.asyncio
async def test_detect_resource_exhaustion(conflict_service, test_user_id):
    """Test resource exhaustion detection"""
    plan1_id = ObjectId()
    plan2_id = ObjectId()
    session_date = date.today() + timedelta(days=5)
    
    plans = [
        {"_id": plan1_id, "plan_name": "Plan 1"},
        {"_id": plan2_id, "plan_name": "Plan 2"},
    ]
    
    # Mock sessions with many time blocks (exceeding max daily hours)
    sessions = [
        {
            "plan_id": plan1_id,
            "session_date": session_date,
            "time_blocks": [1, 2, 3, 4, 5],  # 5 hours
        }
    ]
    
    conflict_service.study_sessions_collection.find = MagicMock()
    conflict_service.db.__getitem__.return_value.find_one = AsyncMock(
        return_value={"max_daily_study_hours": 8.0}
    )
    
    async def mock_find(query):
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=sessions)
        return mock_cursor
    
    conflict_service.study_sessions_collection.find.side_effect = mock_find
    
    conflicts = await conflict_service._detect_resource_exhaustion(test_user_id, plans)
    
    # Should not have conflicts if total < 8 hours
    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_suggest_time_overlap_resolutions(conflict_service):
    """Test resolution suggestions for time overlaps"""
    conflict = PlanConflict(
        user_id=ObjectId(),
        conflict_date=date.today() + timedelta(days=5),
        plan_ids=[ObjectId(), ObjectId()],
        plan_names=["Plan 1", "Plan 2"],
        conflict_type="time_overlap",
        conflict_description="Two plans on same date",
        severity="high",
        affected_sessions_count=2,
        affected_total_hours=4.0,
        is_resolved=False,
    )
    
    suggestions = await conflict_service._suggest_time_overlap_resolutions(conflict)
    
    assert len(suggestions) > 0
    # Should have reschedule, merge, and redistribute suggestions
    types = {s.suggestion_type for s in suggestions}
    assert "reschedule" in types or "merge_similar" in types


@pytest.mark.asyncio
async def test_apply_resolution_reschedule(conflict_service):
    """Test applying reschedule resolution"""
    conflict_id = ObjectId()
    plan_id = ObjectId()
    new_deadline = date.today() + timedelta(days=45)
    
    conflict_service.conflicts_collection.find_one = AsyncMock(
        return_value={
            "_id": conflict_id,
            "plan_ids": [plan_id],
            "conflict_type": "time_overlap",
        }
    )
    
    conflict_service.study_plans_collection.update_one = AsyncMock(
        return_value=AsyncMock(modified_count=1)
    )
    
    conflict_service.conflicts_collection.update_one = AsyncMock(
        return_value=AsyncMock(modified_count=1)
    )
    
    success = await conflict_service.apply_resolution(
        conflict_id,
        "reschedule",
        {"new_deadline": new_deadline},
    )
    
    assert success is True


@pytest.mark.asyncio
async def test_detect_conflicts_integration(conflict_service, test_user_id):
    """Integration test for detecting all conflicts"""
    conflict_service.study_plans_collection.find = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    conflict_service.study_plans_collection.find.return_value = mock_cursor
    
    conflicts, summary = await conflict_service.detect_conflicts(test_user_id)
    
    assert isinstance(conflicts, list)
    assert isinstance(summary, dict)
    assert "total_conflicts" in summary


# ========================================================================
# INTEGRATION TESTS
# ========================================================================


@pytest.mark.asyncio
async def test_goal_to_plan_workflow(planning_service, test_user_id, test_deadline):
    """Test complete goal to plan workflow"""
    planning_service.goals_collection.insert_one = AsyncMock(
        return_value=AsyncMock(inserted_id=ObjectId())
    )
    planning_service.goal_plans_collection.insert_one = AsyncMock(
        return_value=AsyncMock(inserted_id=ObjectId())
    )
    
    # Create goal
    goal = await planning_service.create_goal(
        user_id=test_user_id,
        goal_title="Learn Python",
        goal_type="skill_acquisition",
        subject="Python",
        topics_to_cover=["Basics", "OOP", "Async"],
        target_score=85,
        deadline=test_deadline,
        include_prerequisites=False,
    )
    
    assert goal is not None
    assert goal.status == "not_started"
    
    # Mark goal as retrieved
    planning_service.get_goal = AsyncMock(return_value=goal)
    
    # Generate plan from goal
    with patch.object(
        planning_service.prerequisite_service,
        'get_prerequisites_for_topic',
        new_callable=AsyncMock
    ) as mock_get_prereqs:
        mock_get_prereqs.return_value = None
        
        plan = await planning_service.generate_phased_plan(
            goal_id=goal.id,
            user_id=test_user_id,
        )
        
        assert plan is not None
        assert len(plan.prerequisite_phases) > 0
        assert plan.status == "planning"


@pytest.mark.asyncio
async def test_conflict_detection_and_resolution_workflow(conflict_service, test_user_id):
    """Test complete conflict detection and resolution workflow"""
    conflict_id = ObjectId()
    
    # Setup mocks
    conflict_service.study_plans_collection.find = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    conflict_service.study_plans_collection.find.return_value = mock_cursor
    
    # Detect conflicts
    conflicts, summary = await conflict_service.detect_conflicts(test_user_id)
    
    assert isinstance(summary, dict)
    
    if len(conflicts) > 0:
        # Get suggestions
        conflict_service.conflicts_collection.find_one = AsyncMock(
            return_value={
                "_id": conflicts[0].id,
                "plan_ids": [ObjectId(), ObjectId()],
                "conflict_type": "time_overlap",
            }
        )
        
        suggestions = await conflict_service.suggest_resolutions(conflicts[0].id)
        assert len(suggestions) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
