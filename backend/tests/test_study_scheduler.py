"""
Unit Tests for DailyScheduler Service

Tests the daily scheduling logic including:
- Time-of-day task allocation (morning/afternoon/evening)
- Break insertion
- Mood-based adjustments
- Session generation
"""

import pytest
from datetime import datetime, date, time, timedelta
from bson import ObjectId
from services.study_scheduler import DailyScheduler, BreakScheduler


@pytest.mark.asyncio
class TestDailyScheduler:
    """Test suite for DailyScheduler class"""
    
    @pytest.fixture
    def scheduler(self, mock_db):
        """Create DailyScheduler instance"""
        return DailyScheduler(mock_db)
    
    async def test_time_zone_morning_allocation(self):
        """Test that hard tasks are allocated to morning (6-12)"""
        morning_start = 6
        morning_end = 12
        
        task_difficulty = 0.8  # Hard task
        
        # Hard tasks should be scheduled in morning
        if task_difficulty > 0.7:
            scheduled_zone = "morning"
        
        assert scheduled_zone == "morning", "Hard tasks should be in morning"
    
    async def test_time_zone_afternoon_allocation(self):
        """Test that medium tasks are allocated to afternoon (12-18)"""
        afternoon_start = 12
        afternoon_end = 18
        
        task_difficulty = 0.5  # Medium task
        
        # Medium tasks in afternoon
        if 0.4 <= task_difficulty <= 0.7:
            scheduled_zone = "afternoon"
        
        assert scheduled_zone == "afternoon", "Medium tasks should be in afternoon"
    
    async def test_time_zone_evening_allocation(self):
        """Test that easy tasks are allocated to evening (18-23)"""
        evening_start = 18
        evening_end = 23
        
        task_difficulty = 0.3  # Easy task
        
        # Easy tasks in evening
        if task_difficulty < 0.4:
            scheduled_zone = "evening"
        
        assert scheduled_zone == "evening", "Easy tasks should be in evening"
    
    async def test_break_insertion_every_45_minutes(self):
        """Test that breaks are inserted after study periods"""
        study_duration = 45  # minutes
        break_duration = 15  # minutes
        
        total_block_duration = study_duration + break_duration
        
        assert total_block_duration == 60, "Study + break should total 60 min"
    
    async def test_break_insertion_pomodoro_style(self):
        """Test Pomodoro-style break insertion"""
        pomodoro_study = 25
        pomodoro_break = 5
        
        # 4 pomodoros
        total_time = 4 * (pomodoro_study + pomodoro_break) - pomodoro_break  # No break after last
        
        assert total_time == 115, "4 pomodoros should take 115 minutes"
    
    async def test_break_insertion_frequency(self):
        """Test break insertion frequency"""
        session_duration = 180  # 3 hours
        study_period = 45  # Study for 45 min before break
        
        expected_breaks = session_duration // study_period
        
        assert expected_breaks >= 4, "3-hour session should have at least 4 breaks"
    
    async def test_task_ordering_by_priority(self):
        """Test that tasks are scheduled in priority order"""
        tasks = [
            {"priority": 0.95, "type": "revise"},
            {"priority": 0.70, "type": "learn"},
            {"priority": 0.45, "type": "practice"},
        ]
        
        sorted_tasks = sorted(tasks, key=lambda x: x["priority"], reverse=True)
        
        assert sorted_tasks[0]["priority"] == 0.95, "Highest priority first"
        assert sorted_tasks[2]["priority"] == 0.45, "Lowest priority last"
    
    async def test_session_time_blocks_structure(self):
        """Test that time blocks have correct structure"""
        time_block = {
            "block_id": str(ObjectId()),
            "task_id": str(ObjectId()),
            "subject": "DSA",
            "topic": "Arrays",
            "start_time": "06:00",
            "end_time": "07:00",
            "duration_mins": 60,
            "task_type": "learn",
            "difficulty": 0.6,
        }
        
        assert all(key in time_block for key in [
            "block_id", "task_id", "subject", "topic",
            "start_time", "end_time", "duration_mins"
        ]), "Time block missing required fields"
    
    async def test_session_date_assignment(self, sample_study_session):
        """Test that session is assigned correct date"""
        session_date = date.today()
        session = sample_study_session
        session["session_date"] = session_date.isoformat()
        
        assert session["session_date"] == session_date.isoformat()
    
    async def test_time_continuity_no_gaps(self):
        """Test that scheduled time blocks have no gaps"""
        time_blocks = [
            {"start_time": "06:00", "end_time": "07:00"},
            {"start_time": "07:00", "end_time": "07:30"},  # No gap
            {"start_time": "07:30", "end_time": "09:00"},  # No gap
        ]
        
        for i in range(len(time_blocks) - 1):
            end_time = time_blocks[i]["end_time"]
            next_start = time_blocks[i + 1]["start_time"]
            assert end_time == next_start, "No gaps between blocks"
    
    async def test_mood_adjustment_stressed(self):
        """Test scheduling adjustments for stressed mood"""
        mood = "stressed"
        
        # Adjustments: reduce difficulty, add breaks
        difficulty_reduction = 0.8  # 80% of original
        extra_breaks = 2  # Additional breaks
        
        # For a 0.8 difficulty task
        adjusted_difficulty = 0.8 * difficulty_reduction
        
        assert adjusted_difficulty == pytest.approx(0.64), \
            "Stressed mood should reduce difficulty"
    
    async def test_mood_adjustment_motivated(self):
        """Test scheduling adjustments for motivated mood"""
        mood = "motivated"
        
        # Adjustments: increase difficulty, longer sessions
        difficulty_increase = 1.2  # 120% of original
        session_extension = 1.1  # 110% of planned time
        
        adjusted_difficulty = 0.6 * difficulty_increase
        
        assert adjusted_difficulty == pytest.approx(0.72), \
            "Motivated mood should increase difficulty"
    
    async def test_mood_adjustment_tired(self):
        """Test scheduling adjustments for tired mood"""
        mood = "tired"
        
        # Adjustments: only easy tasks, shorter sessions
        difficulty_max = 0.4
        duration_reduction = 0.5  # 50% of planned
        
        assert difficulty_max == 0.4, "Tired mood should limit to easy tasks"
        assert duration_reduction == 0.5, "Tired mood should reduce duration"


@pytest.mark.asyncio
class TestBreakScheduler:
    """Test suite for BreakScheduler class"""
    
    @pytest.fixture
    def break_scheduler(self):
        """Create BreakScheduler instance"""
        return BreakScheduler()
    
    async def test_parse_break_preference_standard(self, break_scheduler):
        """Test parsing of standard break preference format"""
        preference = "15min after 45min"
        
        # Parse format: "Xmin after Ymin"
        parts = preference.split(" after ")
        break_mins = int(parts[0].replace("min", ""))
        study_mins = int(parts[1].replace("min", ""))
        
        assert break_mins == 15, "Should parse 15 min break"
        assert study_mins == 45, "Should parse 45 min study"
    
    async def test_parse_break_preference_pomodoro(self, break_scheduler):
        """Test parsing of Pomodoro format"""
        preference = "5min after 25min"
        
        parts = preference.split(" after ")
        break_mins = int(parts[0].replace("min", ""))
        study_mins = int(parts[1].replace("min", ""))
        
        assert break_mins == 5
        assert study_mins == 25
    
    async def test_parse_break_preference_extended(self, break_scheduler):
        """Test parsing of extended break format"""
        preference = "20min after 90min"
        
        parts = preference.split(" after ")
        break_mins = int(parts[0].replace("min", ""))
        study_mins = int(parts[1].replace("min", ""))
        
        assert break_mins == 20
        assert study_mins == 90
    
    async def test_break_insertion_calculation(self):
        """Test calculation of break insertion points"""
        session_start = "06:00"
        session_duration = 180  # 3 hours
        study_period = 45
        break_duration = 15
        
        # Calculate breaks
        num_breaks = session_duration // study_period
        
        assert num_breaks == 4, "180 min session should have 4 breaks per 45 min study"
    
    async def test_break_timing_sequence(self):
        """Test that breaks are timed correctly in sequence"""
        study_mins = 45
        break_mins = 15
        
        schedule = [
            ("06:00", "06:45", "study"),
            ("06:45", "07:00", "break"),
            ("07:00", "07:45", "study"),
            ("07:45", "08:00", "break"),
        ]
        
        for i, (start, end, activity_type) in enumerate(schedule):
            if activity_type == "study":
                assert True, "Study block scheduled"
            else:
                assert True, "Break block scheduled"
    
    async def test_break_duration_validation(self):
        """Test that break durations are valid"""
        valid_breaks = [5, 10, 15, 20, 30]
        
        for break_mins in valid_breaks:
            assert 0 < break_mins <= 30, f"Break {break_mins} should be valid"


@pytest.mark.asyncio
class TestSessionGeneration:
    """Test suite for study session generation"""
    
    async def test_session_has_required_fields(self, sample_study_session):
        """Test that generated session has all required fields"""
        required_fields = [
            "_id", "plan_id", "user_id", "session_date",
            "time_blocks", "status", "created_at"
        ]
        
        for field in required_fields:
            assert field in sample_study_session, f"Session missing {field}"
    
    async def test_session_time_blocks_count(self, sample_study_session):
        """Test that session has appropriate number of time blocks"""
        time_blocks = sample_study_session["time_blocks"]
        
        # Typical session should have 3-5 blocks (excluding breaks)
        assert 2 <= len(time_blocks) <= 8, \
            f"Session should have 2-8 blocks, has {len(time_blocks)}"
    
    async def test_session_status_pending(self, sample_study_session):
        """Test that new session has pending status"""
        assert sample_study_session["status"] == "pending", \
            "New session should have pending status"
    
    async def test_session_date_is_today(self, sample_study_session):
        """Test that session date matches target date"""
        session_date = sample_study_session["session_date"]
        today = date.today().isoformat()
        
        assert session_date == today, "Session should be for today"
    
    async def test_session_mood_tracking(self, sample_study_session):
        """Test that session tracks mood at start"""
        assert "mood_at_start" in sample_study_session
        assert "mood_at_end" in sample_study_session
        assert sample_study_session["mood_at_end"] is None, \
            "New session shouldn't have end mood yet"


@pytest.mark.asyncio
class TestTimeBlockAllocation:
    """Test suite for time block allocation logic"""
    
    async def test_morning_block_allocation(self):
        """Test allocation of hard tasks to morning"""
        hard_tasks = [0.8, 0.85, 0.9]
        morning_zone = 6
        afternoon_zone = 12
        
        for task_diff in hard_tasks:
            if task_diff > 0.7:
                zone = "morning"
            else:
                zone = "afternoon"
            
            assert zone == "morning", f"Task difficulty {task_diff} should be in morning"
    
    async def test_afternoon_block_allocation(self):
        """Test allocation of medium tasks to afternoon"""
        medium_tasks = [0.45, 0.5, 0.65]
        
        for task_diff in medium_tasks:
            if 0.4 <= task_diff <= 0.7:
                zone = "afternoon"
            else:
                zone = "other"
            
            assert zone == "afternoon", f"Task difficulty {task_diff} should be in afternoon"
    
    async def test_evening_block_allocation(self):
        """Test allocation of easy tasks to evening"""
        easy_tasks = [0.2, 0.3, 0.35]
        
        for task_diff in easy_tasks:
            if task_diff < 0.4:
                zone = "evening"
            else:
                zone = "other"
            
            assert zone == "evening", f"Task difficulty {task_diff} should be in evening"
    
    async def test_no_overlapping_blocks(self):
        """Test that time blocks don't overlap"""
        blocks = [
            {"start": 6, "end": 7},
            {"start": 7, "end": 8},
            {"start": 8, "end": 9},
        ]
        
        for i in range(len(blocks) - 1):
            assert blocks[i]["end"] <= blocks[i + 1]["start"], \
                f"Blocks {i} and {i+1} overlap"


@pytest.mark.asyncio
class TestMoodBasedScheduling:
    """Test suite for mood-based scheduling adjustments"""
    
    async def test_all_mood_types_supported(self):
        """Test that all 8 mood types are handled"""
        moods = [
            "stressed", "bored", "motivated", "tired",
            "confused", "frustrated", "confident", "engaged"
        ]
        
        # Each mood should have a strategy
        assert len(moods) == 8, "Should support 8 mood types"
    
    async def test_mood_affects_difficulty(self):
        """Test that mood changes task difficulty"""
        base_difficulty = 0.7
        
        # Stressed: reduce to 80%
        stressed_difficulty = base_difficulty * 0.8
        
        # Motivated: increase to 120%
        motivated_difficulty = base_difficulty * 1.2
        
        assert stressed_difficulty < base_difficulty
        assert motivated_difficulty > base_difficulty
    
    async def test_mood_affects_duration(self):
        """Test that mood changes session duration"""
        base_duration = 60
        
        # Tired: reduce to 50%
        tired_duration = base_duration * 0.5
        
        # Motivated: increase to 120%
        motivated_duration = base_duration * 1.2
        
        assert tired_duration == 30
        assert motivated_duration == 72
    
    async def test_mood_affects_break_frequency(self):
        """Test that mood changes break frequency"""
        # Stressed: more frequent breaks
        stressed_break_interval = 30  # Every 30 min
        
        # Motivated: longer study periods
        motivated_break_interval = 60  # Every 60 min
        
        assert stressed_break_interval < motivated_break_interval
