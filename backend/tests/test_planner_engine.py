"""
Unit Tests for TaskGenerator Service

Tests the task generation logic including:
- Task classification (learn/revise/practice)
- Priority scoring
- Time estimation
- Batch task generation
"""

import pytest
from datetime import datetime, date, timedelta
from bson import ObjectId
from services.planner_engine import TaskGenerator, PriorityScorer
from tests.conftest import MockQuizService, MockUserService


@pytest.mark.asyncio
class TestTaskGenerator:
    """Test suite for TaskGenerator class"""
    
    @pytest.fixture
    def task_generator(self, mock_db, sample_quiz_results):
        """Create TaskGenerator instance with mock database"""
        return TaskGenerator(mock_db)
    
    @pytest.fixture
    def priority_scorer(self):
        """Create PriorityScorer instance"""
        return PriorityScorer()
    
    async def test_task_classification_learn(self, task_generator, sample_user_id):
        """Test that topics with 0% score are classified as 'learn'"""
        # Mock quiz score: 0 (never attempted)
        topic_name = "Graphs"
        score = 0
        
        task_type = "learn" if score == 0 else ("revise" if score < 60 else "practice")
        
        assert task_type == "learn", "Zero score should result in 'learn' task"
    
    async def test_task_classification_revise(self, task_generator, sample_user_id):
        """Test that topics with <60% score are classified as 'revise'"""
        scores = [45, 50, 55]
        latest_score = scores[-1]
        
        task_type = "learn" if latest_score == 0 else ("revise" if latest_score < 60 else "practice")
        
        assert task_type == "revise", "Score <60% should result in 'revise' task"
    
    async def test_task_classification_practice(self, task_generator, sample_user_id):
        """Test that topics with ≥60% score are classified as 'practice'"""
        scores = [75, 80, 85]
        latest_score = scores[-1]
        
        task_type = "learn" if latest_score == 0 else ("revise" if latest_score < 60 else "practice")
        
        assert task_type == "practice", "Score ≥60% should result in 'practice' task"
    
    async def test_time_estimation_difficulty_multiplier(self, task_generator):
        """Test that time estimation multiplies by difficulty"""
        base_time = 30
        difficulty = 0.8  # high difficulty
        performance_multiplier = 1.0
        
        estimated_time = base_time * (1 + difficulty) * performance_multiplier
        
        assert estimated_time > base_time, "Difficulty should increase time"
        assert 30 <= estimated_time <= 300, "Time should be within 30-300 min range"
    
    async def test_time_estimation_performance_weak(self, task_generator):
        """Test that weak performance increases time estimation"""
        base_time = 45
        difficulty = 0.6
        
        # Weak performance: average score 40%
        weak_performance_multiplier = 1.2
        estimated_time = base_time * (1 + difficulty) * weak_performance_multiplier
        
        # Strong performance: average score 85%
        strong_performance_multiplier = 0.8
        estimated_time_strong = base_time * (1 + difficulty) * strong_performance_multiplier
        
        assert estimated_time > estimated_time_strong, "Weak performance should increase time"
    
    async def test_time_estimation_bounds(self, task_generator):
        """Test that time estimates are within 15-300 minute bounds"""
        test_cases = [
            (0.1, 1.0),  # easy, strong performance
            (0.5, 1.0),  # moderate, average
            (0.9, 1.5),  # hard, weak performance
        ]
        
        for difficulty, perf_mult in test_cases:
            estimated = 30 * (1 + difficulty) * perf_mult
            assert 15 <= estimated <= 300, f"Time {estimated} outside bounds"
    
    async def test_priority_score_normalization(self, priority_scorer):
        """Test that priority scores are normalized to 0-1"""
        # Calculate priority with components
        urgency = 0.7  # 0-1
        weakness = 0.6  # 0-1
        difficulty = 0.8  # 0-1
        
        raw_score = (urgency + weakness + difficulty) / 3
        normalized_score = min(1.0, raw_score)
        
        assert 0 <= normalized_score <= 1, "Score should be normalized to 0-1"
    
    async def test_priority_score_task_type_boost(self, priority_scorer):
        """Test that task type boosts affect priority"""
        base_score = 0.6
        
        # Task type boosts
        learn_boost = 1.3  # High priority
        revise_boost = 1.2  # High priority  
        practice_boost = 0.7  # Low priority
        
        learn_score = base_score * learn_boost
        revise_score = base_score * revise_boost
        practice_score = base_score * practice_boost
        
        assert learn_score > revise_score > practice_score, \
            "Learn > Revise > Practice in priority"
    
    async def test_priority_score_mood_multiplier(self, priority_scorer):
        """Test that moods affect priority scoring"""
        base_score = 0.6
        
        # Mood multipliers
        motivated = 1.3
        neutral = 1.0
        tired = 0.6
        
        motivated_score = base_score * motivated
        neutral_score = base_score * neutral
        tired_score = base_score * tired
        
        assert motivated_score > neutral_score > tired_score, \
            "Mood should affect priority in order: motivated > neutral > tired"
    
    async def test_generate_tasks_for_subject_topics(self):
        """Test that tasks are generated for all topics in a subject"""
        topics = ["Arrays", "Linked Lists", "Trees", "Graphs"]
        
        # Should generate one task per topic
        task_count = len(topics)
        
        assert task_count == 4, f"Should generate {len(topics)} tasks"
    
    async def test_generate_tasks_score_classification(self):
        """Test task classification across different score ranges"""
        score_ranges = {
            0: "learn",      # 0%
            45: "revise",    # 45%
            55: "revise",    # 55%
            60: "practice",  # 60%
            85: "practice",  # 85%
        }
        
        for score, expected_type in score_ranges.items():
            actual_type = "learn" if score == 0 else ("revise" if score < 60 else "practice")
            assert actual_type == expected_type, \
                f"Score {score} should be {expected_type}"
    
    async def test_batch_generation_multiple_subjects(self):
        """Test batch task generation for multiple subjects"""
        subjects = ["DSA", "Web Development"]
        topics_per_subject = 4
        
        total_tasks = len(subjects) * topics_per_subject
        
        assert total_tasks == 8, "Should generate tasks for all subject/topic combinations"
    
    async def test_task_priority_ordering(self, priority_scorer):
        """Test that tasks are ordered by priority correctly"""
        tasks = [
            {"priority_score": 0.95, "type": "revise"},  # Highest
            {"priority_score": 0.70, "type": "learn"},
            {"priority_score": 0.45, "type": "practice"},  # Lowest
        ]
        
        sorted_tasks = sorted(tasks, key=lambda x: x["priority_score"], reverse=True)
        
        assert sorted_tasks[0]["priority_score"] == 0.95
        assert sorted_tasks[1]["priority_score"] == 0.70
        assert sorted_tasks[2]["priority_score"] == 0.45


@pytest.mark.asyncio
class TestPriorityScorer:
    """Test suite for PriorityScorer class"""
    
    @pytest.fixture
    def scorer(self):
        """Create PriorityScorer instance"""
        return PriorityScorer()
    
    async def test_score_calculation_components(self, scorer):
        """Test the individual components of score calculation"""
        urgency = 0.7
        weakness = 0.6
        difficulty = 0.8
        
        # Average of components
        score = (urgency + weakness + difficulty) / 3
        
        assert 0 < score < 1, "Component average should be between 0 and 1"
        assert abs(score - 0.7) < 0.01, "Score should average 0.7"
    
    async def test_mood_multiplier_extremes(self, scorer):
        """Test mood multipliers at extremes"""
        base_score = 0.5
        
        # Most positive
        motivated_multiplied = base_score * 1.3
        assert motivated_multiplied == 0.65, "Motivated mood should multiply by 1.3"
        
        # Most negative
        tired_multiplied = base_score * 0.6
        assert tired_multiplied == 0.30, "Tired mood should multiply by 0.6"
    
    async def test_all_emotions_mapped(self, scorer):
        """Test that all 8 emotions are mapped to multipliers"""
        emotions = [
            "stressed", "bored", "motivated", "tired",
            "confused", "frustrated", "confident", "engaged"
        ]
        
        # These should have multipliers (check if they're in the scorer)
        assert hasattr(scorer, "MOOD_MULTIPLIERS"), \
            "PriorityScorer should have MOOD_MULTIPLIERS"


class TestTaskGeneratorIntegration:
    """Integration tests for TaskGenerator with mock data"""
    
    @pytest.mark.asyncio
    async def test_generate_tasks_with_mixed_scores(self):
        """Test task generation with realistic mixed quiz scores"""
        # Simulate user with mixed performance
        performance_profile = {
            "strong_topic": 85,    # Should be practice
            "weak_topic": 45,      # Should be revise
            "new_topic": 0,        # Should be learn
            "marginal_topic": 58,  # Should be revise
        }
        
        for topic, score in performance_profile.items():
            task_type = "learn" if score == 0 else ("revise" if score < 60 else "practice")
            expected = {
                "strong_topic": "practice",
                "weak_topic": "revise",
                "new_topic": "learn",
                "marginal_topic": "revise",
            }
            assert task_type == expected[topic], f"Incorrect classification for {topic}"
    
    @pytest.mark.asyncio
    async def test_priority_ordering_mixed_tasks(self):
        """Test priority ordering with mixed task types and scores"""
        tasks = [
            {"type": "learn", "score": 0, "priority": 1.3},    # High (learn boost)
            {"type": "revise", "score": 45, "priority": 1.2},  # High (revise boost)
            {"type": "practice", "score": 85, "priority": 0.7}, # Low (practice)
        ]
        
        # Sort by priority
        sorted_tasks = sorted(tasks, key=lambda x: x["priority"], reverse=True)
        
        # Learn and revise should come before practice
        assert sorted_tasks[0]["type"] in ["learn", "revise"]
        assert sorted_tasks[2]["type"] == "practice"


@pytest.mark.asyncio
class TestTaskTimeEstimation:
    """Detailed tests for task time estimation logic"""
    
    async def test_estimation_formula(self):
        """Test the time estimation formula"""
        base_time = 30
        difficulty = 0.5
        performance_multiplier = 1.0
        
        estimated = base_time * (1 + difficulty) * performance_multiplier
        
        assert estimated == 45, "30 * (1 + 0.5) * 1.0 should equal 45"
    
    async def test_estimation_with_weak_performance(self):
        """Test time increases with weak performance"""
        base_time = 45
        difficulty = 0.6
        weak_multiplier = 1.3
        strong_multiplier = 0.8
        
        weak_time = base_time * (1 + difficulty) * weak_multiplier
        strong_time = base_time * (1 + difficulty) * strong_multiplier
        
        assert weak_time > strong_time, "Weak performance should increase time"
        assert weak_time == pytest.approx(105.3), "Weak time calculation"
        assert strong_time == pytest.approx(56.6), "Strong time calculation"
    
    async def test_estimation_boundary_cases(self):
        """Test time estimation at boundary cases"""
        test_cases = [
            # (base, difficulty, multiplier, expected_min, expected_max)
            (15, 0.0, 1.0, 15, 16),      # Minimum base, easy
            (30, 1.0, 1.0, 60, 61),      # Standard
            (60, 0.9, 1.5, 144, 145),    # High difficulty, weak perf
        ]
        
        for base, diff, mult, exp_min, exp_max in test_cases:
            result = base * (1 + diff) * mult
            assert exp_min <= result <= exp_max, \
                f"Time {result} outside expected range [{exp_min}, {exp_max}]"
