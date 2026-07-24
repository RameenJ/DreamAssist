"""
Backend Enhancement Guide: Makeup Task Detection
================================================

This guide outlines the recommended backend changes to support explicit
makeup task detection in the schedule info card.

CURRENT STATE:
- TimeBlock has: task_id, topic, task_type, difficulty, start_time, end_time, 
  duration_mins, mood_adjustment, completed, completion_timestamp, notes
- To detect makeup tasks, the frontend currently infers from:
  * Keywords in 'notes' field (e.g., "makeup", "missed", "catch-up")
  * The assumption that makeup blocks might be marked in metadata

RECOMMENDED ENHANCEMENT:
Add explicit fields to identify makeup tasks and their source date.
"""

# backend/models/planner_schemas.py

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, date, time
from bson import ObjectId

class TimeBlock(BaseModel):
    """Individual study unit with optional break"""
    task_id: PyObjectId = Field(..., description="Associated task ID")
    topic: str = Field(..., description="Topic name")
    task_type: Literal["learn", "revise", "practice"] = Field(...)
    difficulty: Literal["easy", "medium", "hard"] = Field(...)
    start_time: time = Field(..., description="Block start time")
    end_time: time = Field(..., description="Block end time")
    duration_mins: int = Field(..., description="Duration in minutes")
    mood_adjustment: Optional[str] = Field(None, description="Mood-based adjustment applied")
    completed: bool = Field(default=False)
    completion_timestamp: Optional[datetime] = Field(None)
    notes: Optional[str] = Field(None)
    
    # ============================================================================
    # NEW FIELDS: Makeup Task Detection
    # ============================================================================
    is_makeup: bool = Field(
        default=False,
        description="True if this task is a makeup/catch-up from a missed session"
    )
    original_scheduled_date: Optional[date] = Field(
        None,
        description="Original date when this task was scheduled (before being rescheduled as makeup)"
    )
    missed_session_date: Optional[date] = Field(
        None,
        description="The date of the missed session that this task is making up from"
    )

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {time: str, datetime: str, date: str}


# ============================================================================
# BACKEND LOGIC: Where to Set Makeup Task Fields
# ============================================================================

"""
When rescheduling a task from a missed session, set these fields:

Example 1: User missed a session on 2025-03-10
- Original task was scheduled for 2025-03-10 09:00-10:00
- Task status changed to "missed"
- Now rescheduling to 2025-03-12 15:00-16:00

The rescheduled TimeBlock should have:
  is_makeup: True
  original_scheduled_date: date(2025, 3, 10)
  missed_session_date: date(2025, 3, 10)
  notes: "Makeup from missed session on 2025-03-10"

Example 2: Partial reschedule (user completed some blocks but missed others)
- Original session had 3 blocks, user completed 2, missed 1
- Missed block details:
  is_makeup: True
  original_scheduled_date: date(2025, 3, 10)
  missed_session_date: date(2025, 3, 10)
"""

# ============================================================================
# SUGGESTED IMPLEMENTATION: In your scheduler service
# ============================================================================

"""
In backend/services/scheduler_service.py (or similar):

def reschedule_missed_session_tasks(
    user_id: PyObjectId,
    missed_session: StudySession,
    new_session_date: date,
):
    '''
    Reschedule uncompleted tasks from a missed session to a new date.
    '''
    session_blocks = missed_session.time_blocks
    
    for block in session_blocks:
        if block.completed:
            continue  # Skip completed blocks
        
        # Create makeup time block
        makeup_block = TimeBlock(
            task_id=block.task_id,
            topic=block.topic,
            task_type=block.task_type,
            difficulty=block.difficulty,
            start_time=block.start_time,
            end_time=block.end_time,
            duration_mins=block.duration_mins,
            completed=False,
            # NEW FIELDS:
            is_makeup=True,
            original_scheduled_date=missed_session.session_date,
            missed_session_date=missed_session.session_date,
            notes=f"Makeup from missed session on {missed_session.session_date}"
        )
        
        # Add to new session
        new_session.time_blocks.append(makeup_block)
    
    db.sessions.insert_one(new_session)


def detect_missed_sessions(user_id: PyObjectId, as_of_date: date):
    '''
    Find all sessions the user missed (status="missed" and no reschedule yet)
    and initiate rescheduling.
    '''
    missed_sessions = db.sessions.find({
        "user_id": user_id,
        "session_date": {"$lt": as_of_date},
        "status": "missed"
    })
    
    for session in missed_sessions:
        # Check if any tasks from this session are already rescheduled
        rescheduled_count = db.sessions.count_documents({
            "user_id": user_id,
            "time_blocks": {
                "$elemMatch": {
                    "missed_session_date": session["session_date"],
                    "is_makeup": True
                }
            }
        })
        
        if rescheduled_count == 0:
            # None of these tasks are scheduled yet, reschedule them
            tomorrow = as_of_date + timedelta(days=1)
            reschedule_missed_session_tasks(user_id, session, tomorrow)
"""

# ============================================================================
# BACKEND VALIDATION: Ensure Consistency
# ============================================================================

"""
Add validation in your backend to ensure these fields are set correctly:

def validate_makeup_block(block: TimeBlock):
    '''Ensure makeup task fields are consistent'''
    if block.is_makeup:
        # If marked as makeup, these should be set
        assert block.missed_session_date is not None, \
            "Makeup task must have missed_session_date"
        assert block.original_scheduled_date is not None, \
            "Makeup task must have original_scheduled_date"
        assert block.missed_session_date <= block.original_scheduled_date, \
            "Missed session date cannot be after original date"
    else:
        # If not makeup, these should be None or not set
        assert block.missed_session_date is None, \
            "Non-makeup task should not have missed_session_date"
"""

# ============================================================================
# FRONTEND: Updated TimeBlock Model
# ============================================================================

"""
frontend/lib/core/api/api_models.dart

class TimeBlock {
  final String blockId;
  final String taskId;
  final String? planId;
  final String subject;
  final String topic;
  final String startTime;
  final String endTime;
  final int durationMins;
  final String taskType;
  final double difficulty;
  final bool completed;
  
  // NEW FIELDS:
  final bool isMakeup;
  final String? originalScheduledDate;
  final String? missedSessionDate;

  TimeBlock({
    required this.blockId,
    required this.taskId,
    this.planId,
    required this.subject,
    required this.topic,
    required this.startTime,
    required this.endTime,
    required this.durationMins,
    required this.taskType,
    required this.difficulty,
    required this.completed,
    this.isMakeup = false,
    this.originalScheduledDate,
    this.missedSessionDate,
  });

  factory TimeBlock.fromJson(Map<String, dynamic> json) {
    return TimeBlock(
      blockId: json['block_id'] ?? '',
      taskId: json['task_id'] ?? '',
      planId: json['plan_id'],
      subject: json['subject'] ?? '',
      topic: json['topic'] ?? '',
      startTime: json['start_time'] ?? '06:00',
      endTime: json['end_time'] ?? '07:00',
      durationMins: _toInt(json['duration_mins'], 60),
      taskType: json['task_type'] ?? 'learn',
      difficulty: _toDouble(json['difficulty'], 0.5),
      completed: json['completed'] ?? false,
      isMakeup: json['is_makeup'] ?? false,
      originalScheduledDate: json['original_scheduled_date'],
      missedSessionDate: json['missed_session_date'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'block_id': blockId,
      'task_id': taskId,
      'plan_id': planId,
      'subject': subject,
      'topic': topic,
      'start_time': startTime,
      'end_time': endTime,
      'duration_mins': durationMins,
      'task_type': taskType,
      'difficulty': difficulty,
      'completed': completed,
      'is_makeup': isMakeup,
      'original_scheduled_date': originalScheduledDate,
      'missed_session_date': missedSessionDate,
    };
  }
}
"""

# ============================================================================
# FRONTEND: Updated ScheduleInfoCard Detection
# ============================================================================

"""
Once backend provides explicit fields, update 
frontend/lib/presentation/widgets/schedule_info_card.dart:

bool _isMakeupTask(TimeBlock block) {
  // Primary check: explicit flag from backend
  return block.isMakeup;
}

String _extractMissedDateFromNotes(String notes) {
  // Could be removed entirely once backend provides missed_session_date
  // Or kept as fallback for older data
  final datePattern = RegExp(r'\d{4}-\d{2}-\d{2}');
  final match = datePattern.firstMatch(notes);
  return match?.group(0) ?? 'previous date';
}

Map<String, List<TimeBlock>> _getMakeupBlocksByDate(StudySession session) {
  final makeupBlocks = <String, List<TimeBlock>>{};
  
  for (final block in session.timeBlocks) {
    if (_isMakeupTask(block)) {
      // Use explicit date from backend
      final date = block.missedSessionDate ?? 'previous date';
      makeupBlocks.putIfAbsent(date, () => []).add(block);
    }
  }
  
  return makeupBlocks;
}
"""

# ============================================================================
# DATABASE MIGRATION
# ============================================================================

"""
backend/migrations/XXX_add_makeup_task_fields.py

def migrate_up(db):
    '''Add makeup task fields to existing time blocks'''
    db.sessions.update_many(
        {},
        {
            "$set": {
                "time_blocks.$[].is_makeup": False,
                "time_blocks.$[].original_scheduled_date": None,
                "time_blocks.$[].missed_session_date": None,
            }
        }
    )

def migrate_down(db):
    '''Remove makeup task fields'''
    db.sessions.update_many(
        {},
        {
            "$unset": {
                "time_blocks.$[].is_makeup": "",
                "time_blocks.$[].original_scheduled_date": "",
                "time_blocks.$[].missed_session_date": "",
            }
        }
    )
"""

# ============================================================================
# TESTING RECOMMENDATIONS
# ============================================================================

"""
Test scenarios to verify makeup task detection:

1. User misses a session
   - Create session with status="missed"
   - Verify makeup blocks are created with is_makeup=True
   - Verify missed_session_date is set correctly

2. User partially completes session
   - Create session with 3 blocks: 2 completed, 1 not
   - Verify only incomplete block is rescheduled with is_makeup=True
   - Verify missed session date is set to original session date

3. Multiple missed sessions
   - Miss sessions on different dates
   - Verify each makeup task has correct missed_session_date
   - Verify frontend groups them correctly

4. Frontend detection
   - Mock TimeBlock with is_makeup=True, missed_session_date="2025-03-10"
   - Verify message includes correct date
   - Test with multiple missed sessions
   - Test combining mood adjustments + makeup tasks
"""
