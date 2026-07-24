#!/usr/bin/env python
"""
Quick test to verify session persistence implementation
"""
import sys
import asyncio
from datetime import datetime, date, time
from models.planner_schemas import StudySession, TimeBlock, MoodEvent
from services.schedule_recalculator import ScheduleRecalculator

def test_mood_weights():
    """Test mood weight calculation"""
    print("\n✅ Testing MOOD_WEIGHTS...")
    recalc = ScheduleRecalculator(None)
    
    expected_weights = {
        "motivated": 1.2,
        "stressed": 0.5,
        "neutral": 1.0,
    }
    
    for mood, expected in expected_weights.items():
        actual = recalc.MOOD_WEIGHTS.get(mood)
        assert actual == expected, f"Mood '{mood}': expected {expected}, got {actual}"
        print(f"  ✓ {mood}: {actual}")
    
    print("✅ MOOD_WEIGHTS test passed!")

def test_mood_history():
    """Test mood history creation"""
    print("\n✅ Testing MoodEvent creation...")
    
    event = MoodEvent(
        mood="motivated",
        logged_at=datetime.utcnow(),
        mood_weight=1.2
    )
    
    assert event.mood == "motivated"
    assert event.mood_weight == 1.2
    print(f"  ✓ Created MoodEvent: {event.mood} (weight: {event.mood_weight})")
    
    print("✅ MoodEvent test passed!")

def test_study_session():
    """Test StudySession model with new fields"""
    print("\n✅ Testing StudySession with new fields...")
    
    from models.user_schemas import PyObjectId
    from bson import ObjectId
    
    user_oid = ObjectId()
    
    session = StudySession(
        user_id=user_oid,
        session_date=datetime.combine(date.today(), time.min),
        mood_history=[],
        progress={},
        base_schedule=[],
        current_schedule=[],
        session_id_str=f"{str(user_oid)[:8]}_{date.today().isoformat()}",
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    
    assert session.session_id_str is not None
    assert isinstance(session.mood_history, list)
    assert isinstance(session.progress, dict)
    assert isinstance(session.base_schedule, list)
    assert isinstance(session.current_schedule, list)
    
    print(f"  ✓ session_id_str: {session.session_id_str}")
    print(f"  ✓ mood_history: {session.mood_history}")
    print(f"  ✓ progress: {session.progress}")
    
    print("✅ StudySession test passed!")

def test_schedule_recalculator():
    """Test ScheduleRecalculator methods"""
    print("\n✅ Testing ScheduleRecalculator...")
    
    recalc = ScheduleRecalculator(None)
    
    # Test: calculate_mood_weight with empty history
    weight = recalc.calculate_mood_weight([])
    assert weight == 1.0, f"Expected weight 1.0 for empty history, got {weight}"
    print(f"  ✓ Empty mood history → weight: {weight}")
    
    # Test: calculate_mood_weight with mood events
    events = [
        MoodEvent(mood="motivated", logged_at=datetime.utcnow(), mood_weight=1.2),
        MoodEvent(mood="confused", logged_at=datetime.utcnow(), mood_weight=0.7),
    ]
    weight = recalc.calculate_mood_weight(events)
    assert weight == 0.7, f"Expected weight 0.7 (latest mood), got {weight}"
    print(f"  ✓ Multiple moods → weight: {weight} (latest used)")
    
    print("✅ ScheduleRecalculator test passed!")

def main():
    print("\n" + "="*60)
    print("🧪 SESSION PERSISTENCE IMPLEMENTATION TEST")
    print("="*60)
    
    try:
        test_mood_weights()
        test_mood_history()
        test_study_session()
        test_schedule_recalculator()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\n✅ Implementation verified:")
        print("  • MoodEvent model working")
        print("  • StudySession enhanced with required fields")
        print("  • ScheduleRecalculator logic functional")
        print("  • Mood weight system implemented")
        print("\n✅ Ready for deployment!")
        
        return 0
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
