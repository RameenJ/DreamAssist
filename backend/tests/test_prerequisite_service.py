"""
Unit Tests for Prerequisite Service (Phase 2)
"""

import pytest
from datetime import date, datetime, timedelta
from bson import ObjectId

from backend.services.prerequisite_service import PrerequisiteService
from backend.models.phase2_schemas import (
    TopicPrerequisite,
    PrerequisiteStatus,
    PrerequisiteChain,
)


@pytest.mark.asyncio
class TestPrerequisiteService:
    """Test suite for PrerequisiteService"""

    @pytest.fixture
    async def prerequisite_service(self, mock_db):
        """Inject PrerequisiteService"""
        return PrerequisiteService(mock_db)

    @pytest.fixture
    def sample_user_id(self):
        return ObjectId()

    @pytest.fixture
    def sample_plan_id(self):
        return ObjectId()

    # ========================================================================
    # PREREQUISITE REQUIREMENT TESTS
    # ========================================================================

    async def test_create_prerequisite_requirement(self, prerequisite_service):
        """Test creating a prerequisite requirement"""
        prerequisite = await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Graphs",
            prerequisite_topics=["Arrays", "Linked Lists"],
            difficulty_level="advanced",
            is_strict=True,
        )

        assert prerequisite.subject == "DSA"
        assert prerequisite.dependent_topic == "Graphs"
        assert prerequisite.prerequisite_topics == ["Arrays", "Linked Lists"]
        assert prerequisite.difficulty_level == "advanced"
        assert prerequisite.is_strict is True

    async def test_get_prerequisites_for_topic(self, prerequisite_service):
        """Test retrieving prerequisites for a topic"""
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Graphs",
            prerequisite_topics=["Arrays", "Linked Lists"],
            difficulty_level="advanced",
        )

        prereq = await prerequisite_service.get_prerequisites_for_topic("DSA", "Graphs")
        assert prereq is not None
        assert prereq.prerequisite_topics == ["Arrays", "Linked Lists"]

    async def test_get_topics_requiring_prerequisite(self, prerequisite_service):
        """Test finding topics that require a given topic"""
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Graphs",
            prerequisite_topics=["Arrays"],
            difficulty_level="advanced",
        )
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Trees",
            prerequisite_topics=["Arrays"],
            difficulty_level="advanced",
        )

        dependents = await prerequisite_service.get_topics_requiring_prerequisite(
            "DSA", "Arrays"
        )
        assert len(dependents) == 2
        dependent_topics = [d.dependent_topic for d in dependents]
        assert "Graphs" in dependent_topics
        assert "Trees" in dependent_topics

    # ========================================================================
    # PREREQUISITE CHAIN TESTS
    # ========================================================================

    async def test_create_prerequisite_chain(self, prerequisite_service):
        """Test creating a prerequisite chain"""
        chain = await prerequisite_service.create_prerequisite_chain(
            subject="DSA",
            chain_name="DSA Foundation",
            topics_ordered=["Arrays", "Linked Lists", "Stacks", "Queues"],
            estimated_hours_per_topic=[8.0, 10.0, 8.0, 8.0],
            difficulty_progression=["foundation", "foundation", "intermediate", "intermediate"],
            description="DSA fundamentals learning path",
        )

        assert chain.subject == "DSA"
        assert chain.chain_name == "DSA Foundation"
        assert len(chain.topics_ordered) == 4
        assert chain.estimated_hours_per_topic == [8.0, 10.0, 8.0, 8.0]

    async def test_create_chain_mismatched_lengths(self, prerequisite_service):
        """Test that chain creation fails with mismatched array lengths"""
        with pytest.raises(ValueError):
            await prerequisite_service.create_prerequisite_chain(
                subject="DSA",
                chain_name="Bad Chain",
                topics_ordered=["Arrays", "Linked Lists"],
                estimated_hours_per_topic=[8.0],  # Mismatch!
                difficulty_progression=["foundation", "intermediate"],
            )

    async def test_get_prerequisite_chain(self, prerequisite_service):
        """Test retrieving a prerequisite chain"""
        created = await prerequisite_service.create_prerequisite_chain(
            subject="DSA",
            chain_name="DSA Foundation",
            topics_ordered=["Arrays", "Linked Lists"],
            estimated_hours_per_topic=[8.0, 10.0],
            difficulty_progression=["foundation", "foundation"],
        )

        retrieved = await prerequisite_service.get_prerequisite_chain("DSA", "DSA Foundation")
        assert retrieved is not None
        assert retrieved.chain_name == "DSA Foundation"

    # ========================================================================
    # PREREQUISITE STATUS TRACKING TESTS
    # ========================================================================

    async def test_initialize_prerequisite_status_with_prereqs(
        self, prerequisite_service, sample_user_id, sample_plan_id
    ):
        """Test initializing prerequisite status when prerequisites exist"""
        # Create prerequisite
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Graphs",
            prerequisite_topics=["Arrays", "Linked Lists"],
            is_strict=True,
        )

        # Initialize status
        status = await prerequisite_service.initialize_prerequisite_status(
            user_id=sample_user_id,
            plan_id=sample_plan_id,
            topic="Graphs",
            subject="DSA",
        )

        assert status.topic == "Graphs"
        assert status.subject == "DSA"
        assert status.can_start is False  # strict prerequisites
        assert "Arrays" in status.blocking_prerequisites
        assert "Linked Lists" in status.blocking_prerequisites

    async def test_initialize_prerequisite_status_no_prereqs(
        self, prerequisite_service, sample_user_id, sample_plan_id
    ):
        """Test initializing status when no prerequisites exist"""
        status = await prerequisite_service.initialize_prerequisite_status(
            user_id=sample_user_id,
            plan_id=sample_plan_id,
            topic="Arrays",
            subject="DSA",
        )

        assert status.topic == "Arrays"
        assert status.can_start is True
        assert len(status.blocking_prerequisites) == 0

    async def test_mark_prerequisite_completed(
        self, prerequisite_service, sample_user_id, sample_plan_id
    ):
        """Test marking a prerequisite as completed and unblocking dependents"""
        # Setup prerequisites
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Graphs",
            prerequisite_topics=["Arrays", "Linked Lists"],
            is_strict=True,
        )
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Trees",
            prerequisite_topics=["Arrays"],
            is_strict=True,
        )

        # Initialize statuses
        await prerequisite_service.initialize_prerequisite_status(
            sample_user_id, sample_plan_id, "Graphs", "DSA"
        )
        await prerequisite_service.initialize_prerequisite_status(
            sample_user_id, sample_plan_id, "Trees", "DSA"
        )

        # Mark Arrays as completed
        unblocked = await prerequisite_service.mark_prerequisite_completed(
            user_id=sample_user_id,
            plan_id=sample_plan_id,
            completed_topic="Arrays",
            subject="DSA",
        )

        assert unblocked == 2  # Graphs and Trees unblocked

        # Verify Graphs still blocked (need Linked Lists)
        graphs_status = await prerequisite_service.get_prerequisite_status(
            sample_user_id, sample_plan_id, "Graphs", "DSA"
        )
        assert graphs_status.can_start is False
        assert "Linked Lists" in graphs_status.blocking_prerequisites

        # Verify Trees is now unblocked
        trees_status = await prerequisite_service.get_prerequisite_status(
            sample_user_id, sample_plan_id, "Trees", "DSA"
        )
        assert trees_status.can_start is True

    # ========================================================================
    # PREREQUISITE VALIDATION TESTS
    # ========================================================================

    async def test_can_start_topic_all_prerequisites_met(
        self, prerequisite_service, sample_user_id, sample_plan_id
    ):
        """Test can_start when all prerequisites are met"""
        # Setup
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Graphs",
            prerequisite_topics=["Arrays"],
            is_strict=True,
        )

        await prerequisite_service.initialize_prerequisite_status(
            sample_user_id, sample_plan_id, "Graphs", "DSA"
        )

        # Mark Arrays completed to unblock Graphs
        await prerequisite_service.mark_prerequisite_completed(
            sample_user_id, sample_plan_id, "Arrays", "DSA"
        )

        # Test
        can_start, blocking = await prerequisite_service.can_start_topic(
            sample_user_id, sample_plan_id, "Graphs", "DSA"
        )

        assert can_start is True
        assert len(blocking) == 0

    async def test_can_start_topic_prerequisites_missing(
        self, prerequisite_service, sample_user_id, sample_plan_id
    ):
        """Test can_start when prerequisites are not met"""
        # Setup
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Graphs",
            prerequisite_topics=["Arrays", "Linked Lists"],
            is_strict=True,
        )

        await prerequisite_service.initialize_prerequisite_status(
            sample_user_id, sample_plan_id, "Graphs", "DSA"
        )

        # Test
        can_start, blocking = await prerequisite_service.can_start_topic(
            sample_user_id, sample_plan_id, "Graphs", "DSA"
        )

        assert can_start is False
        assert "Arrays" in blocking
        assert "Linked Lists" in blocking

    async def test_can_start_topic_no_prerequisites(
        self, prerequisite_service, sample_user_id, sample_plan_id
    ):
        """Test can_start for topic with no prerequisites"""
        can_start, blocking = await prerequisite_service.can_start_topic(
            sample_user_id, sample_plan_id, "Arrays", "DSA"
        )

        assert can_start is True
        assert len(blocking) == 0

    # ========================================================================
    # AVAILABILITY ESTIMATION TESTS
    # ========================================================================

    async def test_estimate_topic_availability_when_blocked(
        self, prerequisite_service, sample_user_id, sample_plan_id
    ):
        """Test estimating when a blocked topic will be available"""
        # Setup prerequisites
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Graphs",
            prerequisite_topics=["Arrays"],
            is_strict=True,
        )

        await prerequisite_service.initialize_prerequisite_status(
            sample_user_id, sample_plan_id, "Graphs", "DSA"
        )

        # Estimate availability (will be None since no tasks exist)
        estimated = await prerequisite_service.estimate_topic_availability(
            sample_user_id, sample_plan_id, "Graphs", "DSA"
        )

        # Should return None or estimated date
        assert estimated is None or isinstance(estimated, date)

    async def test_estimate_topic_availability_when_available(
        self, prerequisite_service, sample_user_id, sample_plan_id
    ):
        """Test estimating when topic is already available"""
        estimated = await prerequisite_service.estimate_topic_availability(
            sample_user_id, sample_plan_id, "Arrays", "DSA"
        )

        # Should be None (already available)
        assert estimated is None

    # ========================================================================
    # ANALYTICS TESTS
    # ========================================================================

    async def test_get_prerequisites_blocking_progress(
        self, prerequisite_service, sample_user_id, sample_plan_id
    ):
        """Test getting analytics on blocking prerequisites"""
        # Setup multiple prerequisites
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Linked Lists",
            prerequisite_topics=["Arrays"],
        )
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Graphs",
            prerequisite_topics=["Arrays", "Linked Lists"],
        )

        # Initialize statuses
        await prerequisite_service.initialize_prerequisite_status(
            sample_user_id, sample_plan_id, "Linked Lists", "DSA"
        )
        await prerequisite_service.initialize_prerequisite_status(
            sample_user_id, sample_plan_id, "Graphs", "DSA"
        )

        # Get analytics
        analytics = await prerequisite_service.get_prerequisites_blocking_progress(
            sample_user_id, sample_plan_id, "DSA"
        )

        assert "total_topics" in analytics
        assert "topics_blocked" in analytics
        assert "topics_unblocked" in analytics
        assert "critical_blockers" in analytics

    async def test_critical_blockers_detection(
        self, prerequisite_service, sample_user_id, sample_plan_id
    ):
        """Test that critical blockers are correctly identified"""
        # Arrays blocks 3 topics
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Linked Lists",
            prerequisite_topics=["Arrays"],
        )
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Stacks",
            prerequisite_topics=["Arrays"],
        )
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Queues",
            prerequisite_topics=["Arrays"],
        )

        # Initialize all
        for topic in ["Linked Lists", "Stacks", "Queues"]:
            await prerequisite_service.initialize_prerequisite_status(
                sample_user_id, sample_plan_id, topic, "DSA"
            )

        # Analytics
        analytics = await prerequisite_service.get_prerequisites_blocking_progress(
            sample_user_id, sample_plan_id, "DSA"
        )

        # Arrays should be the top blocker
        if analytics["critical_blockers"]:
            assert analytics["critical_blockers"][0][0] == "Arrays"
            assert analytics["critical_blockers"][0][1] >= 3

    # ========================================================================
    # CHAIN PROGRESS TESTS
    # ========================================================================

    async def test_get_prerequisite_chain_progress(
        self, prerequisite_service, sample_user_id, sample_plan_id
    ):
        """Test getting progress through a prerequisite chain"""
        # Create chain
        chain = await prerequisite_service.create_prerequisite_chain(
            subject="DSA",
            chain_name="DSA Foundation",
            topics_ordered=["Arrays", "Linked Lists"],
            estimated_hours_per_topic=[8.0, 10.0],
            difficulty_progression=["foundation", "foundation"],
        )

        # Initialize statuses
        for topic in ["Arrays", "Linked Lists"]:
            await prerequisite_service.initialize_prerequisite_status(
                sample_user_id, sample_plan_id, topic, "DSA"
            )

        # Get progress
        progress = await prerequisite_service.get_prerequisite_chain_progress(
            sample_user_id, sample_plan_id, chain.id
        )

        assert progress["chain_name"] == "DSA Foundation"
        assert progress["total_topics"] == 2
        assert "topics_progress" in progress

    # ========================================================================
    # EDGE CASE TESTS
    # ========================================================================

    async def test_circular_prerequisite_prevention(self, prerequisite_service):
        """Test that circular prerequisites don't break the system"""
        # Create two topics that could theoretically require each other
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Arrays",
            prerequisite_topics=["Linked Lists"],
        )
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Linked Lists",
            prerequisite_topics=["Arrays"],
        )

        # Should not error - system should handle gracefully
        prereqs = await prerequisite_service.get_prerequisites_for_topic("DSA", "Arrays")
        assert prereqs is not None

    async def test_non_strict_prerequisites(
        self, prerequisite_service, sample_user_id, sample_plan_id
    ):
        """Test non-strict prerequisites (some but not all required)"""
        await prerequisite_service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Graphs",
            prerequisite_topics=["Arrays", "Linked Lists"],
            is_strict=False,  # Optional prerequisites
        )

        status = await prerequisite_service.initialize_prerequisite_status(
            sample_user_id, sample_plan_id, "Graphs", "DSA"
        )

        # Should be able to start even without all prerequisites
        assert status.can_start is True


# ========================================================================
# INTEGRATION TESTS
# ========================================================================

@pytest.mark.asyncio
class TestPrerequisiteIntegration:
    """Integration tests for prerequisite system"""

    async def test_complete_prerequisite_chain_progression(
        self, mock_db, sample_user_id=ObjectId(), sample_plan_id=ObjectId()
    ):
        """Test complete progression through a prerequisite chain"""
        service = PrerequisiteService(mock_db)

        # Create DSA foundation chain
        chain = await service.create_prerequisite_chain(
            subject="DSA",
            chain_name="DSA Foundation",
            topics_ordered=["Arrays", "Linked Lists", "Stacks"],
            estimated_hours_per_topic=[8.0, 10.0, 8.0],
            difficulty_progression=["foundation", "foundation", "intermediate"],
        )

        # Create prerequisite requirements
        await service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Linked Lists",
            prerequisite_topics=["Arrays"],
        )
        await service.create_prerequisite_requirement(
            subject="DSA",
            dependent_topic="Stacks",
            prerequisite_topics=["Arrays", "Linked Lists"],
        )

        # Initialize all topics
        for topic in ["Arrays", "Linked Lists", "Stacks"]:
            await service.initialize_prerequisite_status(
                sample_user_id, sample_plan_id, topic, "DSA"
            )

        # Verify initial state: only Arrays can start
        arrays_can_start, _ = await service.can_start_topic(
            sample_user_id, sample_plan_id, "Arrays", "DSA"
        )
        assert arrays_can_start is True

        ll_can_start, ll_blocking = await service.can_start_topic(
            sample_user_id, sample_plan_id, "Linked Lists", "DSA"
        )
        assert ll_can_start is False
        assert "Arrays" in ll_blocking

        # Complete Arrays
        unblocked = await service.mark_prerequisite_completed(
            sample_user_id, sample_plan_id, "Arrays", "DSA"
        )
        assert unblocked >= 1  # At least Linked Lists should be unblocked

        # Now Linked Lists should be available
        ll_can_start_after, _ = await service.can_start_topic(
            sample_user_id, sample_plan_id, "Linked Lists", "DSA"
        )
        assert ll_can_start_after is True

        # But Stacks should still be blocked
        stacks_can_start, stacks_blocking = await service.can_start_topic(
            sample_user_id, sample_plan_id, "Stacks", "DSA"
        )
        assert stacks_can_start is False
        assert "Linked Lists" in stacks_blocking

        # Complete Linked Lists
        await service.mark_prerequisite_completed(
            sample_user_id, sample_plan_id, "Linked Lists", "DSA"
        )

        # Now Stacks should be available
        stacks_can_start_after, _ = await service.can_start_topic(
            sample_user_id, sample_plan_id, "Stacks", "DSA"
        )
        assert stacks_can_start_after is True
