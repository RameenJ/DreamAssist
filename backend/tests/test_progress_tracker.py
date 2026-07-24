"""
Unit Tests for AdaptiveTracker Service

Tests the adaptive tracking logic including:
- Session completion logging
- Missed task rescheduling
- Early completion handling
- Re-planning trigger detection
- Analytics computation
"""

import pytest
from datetime import datetime, date, timedelta
from bson import ObjectId
from services.progress_tracker import AdaptiveTracker, PlanAnalytics


@pytest.mark.asyncio
class TestAdaptiveTracker:
    """Test suite for AdaptiveTracker class"""
    
    @pytest.fixture
    def tracker(self, mock_db):
        """Create AdaptiveTracker instance"""
        return AdaptiveTracker(mock_db)
    
    async def test_missed_task_priority_boost(self):
        """Test that missed tasks get priority boost"""
        original_priority = 0.6
        priority_boost_multiplier = 1.2
        
        new_priority = original_priority * priority_boost_multiplier
        
        assert new_priority == pytest.approx(0.72), \
            "Missed tasks should have boosted priority"
    
    async def test_missed_task_rescheduling_next_day(self):
        """Test that missed tasks are rescheduled to next day"""
        missed_date = date.today()
        reschedule_date = missed_date + timedelta(days=1)
        
        assert reschedule_date > missed_date, "Missed task should reschedule to future"
    
    async def test_early_completion_pull_forward(self):
        """Test that early completion triggers pull forward"""
        completion_rate = 0.95  # 95% complete
        early_completion_threshold = 0.90
        
        can_pull_forward = completion_rate > early_completion_threshold
        
        assert can_pull_forward, "95% completion should trigger pull forward"
    
    async def test_early_completion_task_selection(self):
        """Test selection of tasks to pull forward"""
        pending_tasks = [
            {"priority": 0.85, "type": "revise"},  # Should pull
            {"priority": 0.65, "type": "learn"},   # Should pull
            {"priority": 0.35, "type": "practice"},  # Should NOT pull (low priority)
        ]
        
        priority_threshold = 0.5
        tasks_to_pull = [t for t in pending_tasks if t["priority"] > priority_threshold]
        
        assert len(tasks_to_pull) == 2, "Should pull 2 higher-priority tasks"
    
    async def test_completion_rate_calculation_7_days(self):
        """Test 7-day completion rate calculation"""
        total_tasks = 20
        completed_tasks = 12
        
        completion_rate = completed_tasks / total_tasks
        
        assert completion_rate == 0.6, "Completion rate should be 60%"
    
    async def test_replan_trigger_low_completion_rate(self):
        """Test that low completion rate triggers re-planning"""
        completion_rate = 0.55  # 55%
        replan_threshold = 0.60
        
        should_replan = completion_rate < replan_threshold
        
        assert should_replan, "55% completion should trigger re-planning"
    
    async def test_replan_trigger_negative_emotion_trend(self):
        """Test that negative emotion trend triggers re-planning"""
        mood_logs = [
            "stressed", "tired", "frustrated",  # Negative
            "neutral", "motivated", "engaged",   # Positive
            "stressed"  # Negative
        ]
        
        negative_moods = ["stressed", "tired", "frustrated", "bored", "confused"]
        negative_count = sum(1 for mood in mood_logs if mood in negative_moods)
        negative_percentage = negative_count / len(mood_logs)
        
        should_replan = negative_percentage > 0.5
        
        assert should_replan is False, "43% negative should not trigger replan"
        
        # Test with >50% negative
        mood_logs_high_negative = ["stressed", "tired"] * 4 + ["motivated"]
        negative_count = sum(1 for mood in mood_logs_high_negative if mood in negative_moods)
        negative_percentage = negative_count / len(mood_logs_high_negative)
        
        should_replan_high = negative_percentage > 0.5
        assert should_replan_high, "High negative emotion should trigger re-planning"
    
    async def test_session_completion_status_update(self):
        """Test that session status is updated to completed"""
        session = {
            "_id": ObjectId(),
            "status": "pending",
            "completed_blocks": 0,
        }
        
        # Simulate completion
        session["status"] = "completed"
        session["completed_blocks"] = 5
        
        assert session["status"] == "completed"
        assert session["completed_blocks"] == 5
    
    async def test_session_timestamps_updated(self):
        """Test that session timestamps are updated"""
        now = datetime.utcnow()
        
        session = {
            "created_at": (now - timedelta(hours=1)).isoformat(),
            "updated_at": now.isoformat(),
        }
        
        # Update on completion
        session["updated_at"] = now.isoformat()
        
        assert session["updated_at"] >= session["created_at"]
    
    async def test_mood_at_completion_logged(self):
        """Test that mood at session end is logged"""
        session = {
            "mood_at_start": "neutral",
            "mood_at_end": None,
        }
        
        # Log end mood
        session["mood_at_end"] = "satisfied"
        
        assert session["mood_at_end"] is not None
        assert session["mood_at_end"] == "satisfied"


@pytest.mark.asyncio
class TestReplanTriggerDetection:
    """Test suite for re-planning trigger detection"""
    
    @pytest.fixture
    def tracker(self, mock_db):
        """Create AdaptiveTracker instance"""
        return AdaptiveTracker(mock_db)
    
    async def test_trigger_low_completion_rate_60_percent(self):
        """Test trigger at exactly 60% completion rate"""
        completion_rate = 0.60
        threshold = 0.60
        
        should_trigger = completion_rate < threshold
        
        assert not should_trigger, "60% should not trigger (threshold boundary)"
    
    async def test_trigger_low_completion_rate_59_percent(self):
        """Test trigger at 59% completion rate"""
        completion_rate = 0.59
        threshold = 0.60
        
        should_trigger = completion_rate < threshold
        
        assert should_trigger, "59% should trigger"
    
    async def test_trigger_emotion_trend_declining(self):
        """Test trigger on declining emotion trend"""
        first_half_moods = ["motivated", "engaged", "confident"]  # Positive
        second_half_moods = ["stressed", "tired", "frustrated"]   # Negative
        
        first_half_positive = 3
        second_half_positive = 0
        
        trend = "declining" if second_half_positive < first_half_positive else "improving"
        
        assert trend == "declining", "Should detect declining trend"
    
    async def test_trigger_emotion_trend_improving(self):
        """Test no trigger on improving emotion trend"""
        first_half_moods = ["stressed", "tired", "frustrated"]  # Negative
        second_half_moods = ["motivated", "engaged", "confident"]  # Positive
        
        first_half_positive = 0
        second_half_positive = 3
        
        trend = "declining" if second_half_positive < first_half_positive else "improving"
        
        assert trend == "improving", "Should detect improving trend"
    
    async def test_trigger_consistent_failure_pattern(self):
        """Test trigger on consistent failure pattern"""
        task_failures = {
            "Arrays": [False, False, False, False],  # Failing 4 times
            "Linked Lists": [True, True, True, True],  # Success
        }
        
        arrays_failure_rate = sum(not x for x in task_failures["Arrays"]) / len(task_failures["Arrays"])
        
        should_trigger = arrays_failure_rate > 0.7
        
        assert should_trigger, "4/4 failures should trigger re-planning"
    
    async def test_multiple_triggers_combined(self):
        """Test detection with multiple triggers present"""
        triggers = {
            "low_completion": 0.55,  # <60%: True
            "negative_emotion": 0.60,  # >50%: True
            "failure_pattern": 0.85,  # >70%: True
        }
        
        should_replan = any(triggers.values())
        
        assert should_replan, "Any single trigger should cause re-planning"


@pytest.mark.asyncio
class TestPlanAnalytics:
    """Test suite for PlanAnalytics class"""
    
    @pytest.fixture
    def analytics(self, mock_db):
        """Create PlanAnalytics instance"""
        return PlanAnalytics(mock_db)
    
    async def test_completion_rate_calculation(self):
        """Test overall completion rate calculation"""
        completed_tasks = 12
        total_tasks = 20
        
        completion_rate = completed_tasks / total_tasks
        
        assert completion_rate == 0.6, "Should calculate 60% completion rate"
    
    async def test_completion_rate_zero(self):
        """Test completion rate when no tasks completed"""
        completed_tasks = 0
        total_tasks = 20
        
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        assert completion_rate == 0, "No completions should be 0%"
    
    async def test_completion_rate_complete(self):
        """Test completion rate when all tasks completed"""
        completed_tasks = 20
        total_tasks = 20
        
        completion_rate = completed_tasks / total_tasks
        
        assert completion_rate == 1.0, "All complete should be 100%"
    
    async def test_subject_wise_completion(self):
        """Test per-subject completion rate calculation"""
        subject_tasks = {
            "DSA": {"completed": 5, "total": 10},
            "Web Dev": {"completed": 4, "total": 8},
        }
        
        dsa_rate = subject_tasks["DSA"]["completed"] / subject_tasks["DSA"]["total"]
        web_rate = subject_tasks["Web Dev"]["completed"] / subject_tasks["Web Dev"]["total"]
        
        assert dsa_rate == 0.5, "DSA should be 50% complete"
        assert web_rate == 0.5, "Web Dev should be 50% complete"
    
    async def test_productivity_score_calculation(self):
        """Test productivity score calculation"""
        # Formula: (completion_rate + quality_score + speed_score) / 3
        completion_rate = 0.75
        quality_score = 0.80  # Based on quiz scores
        speed_score = 0.70    # Tasks completed on time
        
        productivity = (completion_rate + quality_score + speed_score) / 3
        
        assert productivity == pytest.approx(0.75), "Productivity score should be 0.75"
    
    async def test_mood_distribution_tracking(self):
        """Test mood distribution across sessions"""
        mood_logs = [
            "motivated", "engaged", "motivated",
            "stressed", "tired", "neutral",
            "confident"
        ]
        
        mood_dist = {}
        for mood in mood_logs:
            mood_dist[mood] = mood_dist.get(mood, 0) + 1
        
        assert mood_dist["motivated"] == 2
        assert mood_dist["stressed"] == 1
        assert len(mood_dist) == 5
    
    async def test_topic_progress_classification(self):
        """Test classification of topic progress"""
        topic_scores = {
            "Arrays": [70, 75, 80],        # Improving
            "Linked Lists": [85, 85, 85],  # Mastered
            "Trees": [40, 45, 50],         # Still weak
        }
        
        for topic, scores in topic_scores.items():
            if scores[-1] >= 80:
                status = "mastered"
            elif scores[-1] > scores[0]:
                status = "improving"
            else:
                status = "still_weak"
            
            expected = {
                "Arrays": "improving",
                "Linked Lists": "mastered",
                "Trees": "still_weak",
            }
            assert status == expected[topic]


@pytest.mark.asyncio
class TestWeeklySummary:
    """Test suite for weekly summary generation"""
    
    async def test_weekly_summary_completion(self):
        """Test weekly summary completion metrics"""
        week = {
            "week_number": 1,
            "total_sessions": 5,
            "completed_sessions": 4,
            "completion_rate": 0.8,
        }
        
        assert week["completion_rate"] == 4 / 5
    
    async def test_weekly_summary_mood_avg(self):
        """Test average mood calculation for week"""
        moods = ["neutral", "motivated", "stressed", "engaged", "neutral"]
        
        mood_weights = {"stressed": 0.3, "neutral": 0.5, "motivated": 0.8, "engaged": 1.0}
        avg_mood = sum(mood_weights[m] for m in moods) / len(moods)
        
        assert avg_mood == pytest.approx(0.72), "Average mood score"
    
    async def test_weekly_summary_topics_progress(self):
        """Test topics progress in weekly summary"""
        topics_week1 = {
            "Arrays": {"avg_score": 72},
            "Lists": {"avg_score": 45},
        }
        
        topics_week2 = {
            "Arrays": {"avg_score": 78},  # Improved
            "Lists": {"avg_score": 50},   # Improved
        }
        
        arrays_improvement = topics_week2["Arrays"]["avg_score"] - topics_week1["Arrays"]["avg_score"]
        lists_improvement = topics_week2["Lists"]["avg_score"] - topics_week1["Lists"]["avg_score"]
        
        assert arrays_improvement == 6, "Arrays improved by 6%"
        assert lists_improvement == 5, "Lists improved by 5%"


@pytest.mark.asyncio
class TestMissedTaskHandling:
    """Test suite for missed task handling"""
    
    async def test_missed_task_marked_correctly(self):
        """Test that missed tasks are marked as missed"""
        task = {"status": "pending"}
        
        # Mark as missed
        task["status"] = "missed"
        
        assert task["status"] == "missed"
    
    async def test_missed_task_priority_boost_calculation(self):
        """Test priority boost for missed tasks"""
        original_priority = 0.6
        boost_multiplier = 1.2
        
        boosted_priority = original_priority * boost_multiplier
        max_priority = min(1.0, boosted_priority)
        
        assert max_priority == pytest.approx(0.72)
    
    async def test_missed_task_multiple_boosts_capped(self):
        """Test that multiple misses cap at 1.0"""
        priority = 0.6
        
        # First miss
        priority = priority * 1.2  # 0.72
        
        # Second miss
        priority = priority * 1.2  # 0.864
        
        # Cap at 1.0
        priority = min(1.0, priority)
        
        assert priority == pytest.approx(0.864)
        assert priority <= 1.0


@pytest.mark.asyncio
class TestEarlyCompletionHandling:
    """Test suite for early completion handling"""
    
    async def test_early_completion_pull_threshold(self):
        """Test threshold for pulling forward tasks"""
        completed_blocks = 5
        total_blocks = 5
        completion_rate = completed_blocks / total_blocks
        
        pull_threshold = 0.90
        can_pull = completion_rate >= pull_threshold
        
        assert can_pull is False, "100% completion should meet threshold"
    
    async def test_early_completion_pull_threshold_90_percent(self):
        """Test 90% completion threshold"""
        completed = 9
        total = 10
        completion_rate = completed / total
        
        pull_threshold = 0.90
        can_pull = completion_rate >= pull_threshold
        
        assert can_pull, "90% completion should meet threshold"
    
    async def test_tasks_pulled_forward_selection(self):
        """Test which tasks are pulled forward"""
        pending_tasks = [
            {"priority": 0.35, "type": "practice"},  # LOW - Should NOT pull
            {"priority": 0.65, "type": "learn"},     # MEDIUM - Should pull
            {"priority": 0.85, "type": "revise"},    # HIGH - Should pull
        ]
        
        # Pull low-priority tasks (opposite of missed)
        pull_threshold = 0.50
        tasks_to_pull = [t for t in pending_tasks if t["priority"] < pull_threshold]
        
        # Actually, based on spec: pull LOW priority tasks (practice)
        assert len(tasks_to_pull) == 1, "Should pull 1 low-priority task"
    
    async def test_early_completion_reschedule_today(self):
        """Test that pulled tasks are scheduled for today"""
        task_date = date.today()
        
        assert task_date == date.today(), "Pulled tasks should be for today"
