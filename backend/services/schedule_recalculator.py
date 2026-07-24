"""
Schedule Recalculation Engine

Implements reactive schedule updates based on mood changes without:
- Deleting completed tasks
- Resetting progress
- Replacing entire schedule
- Creating new sessions
"""

from typing import List, Optional, Dict
from datetime import datetime
from models.planner_schemas import StudySession, TimeBlock, MoodEvent
from models.user_schemas import PyObjectId
from core.db import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class ScheduleRecalculator:
    """
    Recalculates schedule based on mood changes.
    
    Key principles:
    1. Only modify tasks NOT completed
    2. Preserve all progress state
    3. Adjust difficulty/duration based on mood
    4. Never reset completed tasks
    """
    
    # Mood weight mappings (for adjusting task difficulty/duration)
    MOOD_WEIGHTS = {
        "motivated": 1.2,      # +20% energy, harder tasks
        "engaged": 1.15,       # +15% energy
        "confident": 1.1,      # +10% energy
        "neutral": 1.0,        # baseline
        "bored": 0.9,          # -10% engagement
        "tired": 0.85,         # -15% energy
        "confused": 0.7,       # -30% focus
        "frustrated": 0.6,     # -40% productivity
        "stressed": 0.5,       # -50% capacity
    }
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    def calculate_mood_weight(self, mood_history: List[MoodEvent]) -> float:
        """
        Calculate overall mood weight from history.
        
        Rules:
        1. If no mood logged: return 1.0 (neutral)
        2. If single mood: use its weight
        3. If multiple moods: use latest mood (most recent state)
        
        Args:
            mood_history: List of mood events for the day
            
        Returns:
            Float weight between 0.5 (worst) and 1.2 (best)
        """
        if not mood_history:
            logger.info("📊 No mood history - using neutral weight (1.0)")
            return 1.0
        
        # Get latest mood
        latest_mood = mood_history[-1]  # Most recently logged
        mood_str = latest_mood.mood.lower()
        
        weight = self.MOOD_WEIGHTS.get(mood_str, 1.0)
        logger.info(f"📊 Latest mood '{mood_str}' → weight {weight}")
        
        return weight
    
    def recalculate_schedule(
        self, 
        session: StudySession,
        new_mood: Optional[str] = None
    ) -> StudySession:
        """
        Recalculate schedule based on mood changes.
        
        Process:
        1. Append new mood to mood_history (if provided)
        2. Calculate current mood weight
        3. For each time block:
           - If completed: preserve as-is
           - If not completed: adjust duration/difficulty
        4. Update current_schedule
        5. Preserve all progress state
        
        Args:
            session: Current study session
            new_mood: Optional new mood to append
            
        Returns:
            Updated session with recalculated schedule
        """
        logger.info(f"🔄 Starting schedule recalculation for session {session.id}")
        
        # Step 1: Append new mood if provided
        if new_mood:
            mood_event = MoodEvent(
                mood=new_mood.lower(),
                logged_at=datetime.utcnow(),
                mood_weight=self.MOOD_WEIGHTS.get(new_mood.lower(), 1.0)
            )
            session.mood_history.append(mood_event)
            logger.info(f"➕ Appended new mood: {new_mood}")
        
        # Step 2: Calculate current mood weight
        current_weight = self.calculate_mood_weight(session.mood_history)
        
        # Step 3: Use base_schedule as reference for recalculation.
        # Fall back to current_schedule/time_blocks for sessions created before
        # the persistent schedule fields existed.
        reference_schedule = (
            session.base_schedule
            or session.current_schedule
            or session.time_blocks
        )
        
        if not reference_schedule:
            logger.warning("⚠️ No base or current schedule to recalculate!")
            return session

        if not session.base_schedule:
            session.base_schedule = reference_schedule

        if not session.progress:
            session.progress = {
                str(block.task_id): "completed" if block.completed else "not_started"
                for block in session.time_blocks
            }
        else:
            for block in session.time_blocks:
                if block.completed:
                    session.progress[str(block.task_id)] = "completed"
        
        # Step 4: Recalculate each block
        recalculated_blocks = []
        
        for block in reference_schedule:
            task_id_str = str(block.task_id)
            current_status = session.progress.get(task_id_str, "not_started")
            
            # CRITICAL: Never modify completed tasks
            if current_status == "completed":
                logger.info(f"✅ Block {task_id_str} already completed - preserving as-is")
                recalculated_blocks.append(block)
                continue
            
            # For non-completed tasks: adjust duration based on mood
            adjusted_block = self._adjust_block_by_mood(block, current_weight)
            logger.info(
                f"🔧 Block {task_id_str} adjusted: {block.duration_mins} → {adjusted_block.duration_mins} mins "
                f"(weight: {current_weight})"
            )
            recalculated_blocks.append(adjusted_block)
        
        # Step 5: Update current_schedule
        session.current_schedule = recalculated_blocks
        session.time_blocks = recalculated_blocks  # Keep time_blocks in sync for backward compatibility
        
        # Step 6: Mark as recalculated
        session.updated_at = datetime.utcnow()
        session.mood_adjustments_applied.append(
            f"Schedule recalculated at {datetime.utcnow().isoformat()} with mood weight {current_weight}"
        )
        
        logger.info(f"✅ Schedule recalculation complete for session {session.id}")
        return session
    
    def _adjust_block_by_mood(self, block: TimeBlock, mood_weight: float) -> TimeBlock:
        """
        Adjust a single time block based on mood weight.
        
        Rules:
        - If weight > 1.0: User is energized
          * Can handle harder tasks
          * Keep same difficulty or increase
          * Possibly reduce duration (work faster)
        
        - If weight < 1.0: User is demotivated
          * Should do easier tasks
          * Reduce difficulty if possible
          * May increase duration (need more breaks)
        
        Args:
            block: Original time block
            mood_weight: Mood adjustment multiplier
            
        Returns:
            Adjusted time block (cloned, not mutated)
        """
        import copy
        adjusted = copy.deepcopy(block)
        
        # Adjust duration: multiply by mood weight
        # Range: 0.5x to 1.5x of original
        adjusted.duration_mins = max(
            int(block.duration_mins * mood_weight * 0.8),  # At least 80% of adjusted
            15  # Minimum 15 minutes
        )
        
        # Cap at 2x original (prevent runaway increases)
        adjusted.duration_mins = min(adjusted.duration_mins, block.duration_mins * 2)
        
        # Adjust difficulty based on mood weight
        if mood_weight > 1.15 and block.difficulty != "hard":
            # User is highly motivated: can do harder tasks
            adjusted.difficulty = "hard"
            adjusted.mood_adjustment = "difficulty_increased_high_mood"
        elif mood_weight > 1.0 and block.difficulty == "easy":
            # User is motivated: upgrade easy tasks to medium
            adjusted.difficulty = "medium"
            adjusted.mood_adjustment = "difficulty_increased_positive_mood"
        elif mood_weight < 0.7 and block.difficulty != "easy":
            # User is struggling: downgrade to easier tasks
            adjusted.difficulty = "easy"
            adjusted.mood_adjustment = "difficulty_reduced_negative_mood"
        elif mood_weight < 1.0 and block.difficulty == "hard":
            # User is demotivated: reduce hard tasks to medium
            adjusted.difficulty = "medium"
            adjusted.mood_adjustment = "difficulty_reduced_poor_mood"
        else:
            # No adjustment needed
            adjusted.mood_adjustment = None
        
        return adjusted
    
    async def apply_schedule_recalculation(
        self,
        db: AsyncIOMotorDatabase,
        session: StudySession,
        new_mood: Optional[str] = None
    ) -> StudySession:
        """
        Recalculate schedule and persist to database.
        
        Args:
            db: Database connection
            session: Current session to recalculate
            new_mood: Optional new mood to append
            
        Returns:
            Updated session
        """
        # Recalculate in memory
        updated_session = self.recalculate_schedule(session, new_mood)
        
        # Convert and save to database
        from services.study_scheduler import convert_times_to_str
        session_dict = updated_session.model_dump(by_alias=True, mode='python')
        session_dict = convert_times_to_str(session_dict)
        
        # Update session in database
        await db.study_sessions.update_one(
            {"_id": updated_session.id},
            {"$set": session_dict}
        )
        logger.info(f"💾 Persisted recalculated session {updated_session.id} to database")
        
        return updated_session
