"""
Background Job Manager for Adaptive Study Plan Updates

This module manages the APScheduler background tasks that:
1. Check active plans for adaptive updates
2. Pre-generate next day's study sessions
3. Detect burnout and trigger re-planning
4. Update plan status based on performance trends

Jobs are run periodically (default: daily at midnight UTC)
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from datetime import date, timedelta, datetime
from typing import Optional

logger = logging.getLogger(__name__)


class BackgroundJobManager:
    """
    Manages APScheduler background jobs for study plan adaptive updates.
    
    Singleton instance is created at app startup and stopped at shutdown.
    """

    def __init__(self):
        """Initialize the scheduler (not started yet)."""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def start(self, db: AsyncIOMotorDatabase):
        """
        Start the background scheduler.
        
        Args:
            db: AsyncIOMotorDatabase instance for job access
        """
        if self.scheduler is not None:
            logger.warning("Scheduler already running")
            return

        self.db = db
        self.scheduler = AsyncIOScheduler()

        # Register the daily adaptive update job
        # Runs daily at 00:00 UTC (midnight)
        self.scheduler.add_job(
            self._adaptive_update_task,
            trigger=CronTrigger(hour=0, minute=0),
            id="adaptive_update_job",
            name="Daily Adaptive Study Plan Updates",
            replace_existing=True,
            max_instances=1,  # Prevent concurrent runs
        )

        # Start the scheduler
        self.scheduler.start()
        logger.info("Background job scheduler started successfully")
        logger.info(
            "Adaptive update job scheduled to run daily at 00:00 UTC (midnight)"
        )

    async def stop(self):
        """Stop the background scheduler gracefully."""
        if self.scheduler is None:
            logger.warning("Scheduler not running")
            return

        self.scheduler.shutdown(wait=True)
        self.scheduler = None
        logger.info("Background job scheduler stopped successfully")

    async def _adaptive_update_task(self):
        """
        Main background job that runs daily.
        
        Responsibilities:
        1. Fetch all active study plans
        2. Check each plan for adaptive update triggers (completion rate, mood trends)
        3. Pre-generate next day's study sessions
        4. Update plan status if needed
        5. Log all actions and errors
        
        This job:
        - Runs once daily at midnight UTC
        - Handles errors gracefully (doesn't crash on individual plan failures)
        - Provides comprehensive logging for monitoring
        """
        if self.db is None:
            logger.error("Database connection not available for adaptive update task")
            return

        try:
            logger.info("=== Adaptive Update Task Started ===")
            logger.info(f"Timestamp: {datetime.utcnow().isoformat()}Z")

            # Get all active plans
            active_plans = await self.db.study_plans.find(
                {"status": "active"}
            ).to_list(None)

            logger.info(f"Found {len(active_plans)} active study plans")

            if len(active_plans) == 0:
                logger.info("No active plans to process")
                return

            # Metrics tracking
            plans_checked = 0
            plans_replanning_suggested = 0
            sessions_pregenerated = 0
            errors_encountered = 0

            for plan_doc in active_plans:
                plan_id = plan_doc.get("_id")
                user_id = plan_doc.get("user_id")
                subjects = plan_doc.get("subjects", [])

                try:
                    logger.debug(
                        f"Processing plan {plan_id} for user {user_id} "
                        f"({len(subjects)} subjects)"
                    )
                    plans_checked += 1

                    # ===== Check if Re-planning Needed =====
                    should_replan, reason = await self._check_replanning_needed(
                        plan_id, user_id
                    )

                    if should_replan:
                        logger.warning(
                            f"[REPLAN SUGGESTED] Plan {plan_id}: {reason}"
                        )
                        plans_replanning_suggested += 1
                        # Note: Actual re-planning can be triggered manually or via
                        # a separate decision engine. For now, we log the suggestion.

                    # ===== Pre-generate Tomorrow's Session =====
                    tomorrow = datetime.utcnow().date() + timedelta(days=1)

                    # Check if session already exists
                    existing_session = await self.db.study_sessions.find_one(
                        {"plan_id": plan_id, "session_date": tomorrow}
                    )

                    if existing_session:
                        logger.debug(
                            f"Session already exists for {tomorrow} in plan {plan_id}"
                        )
                    else:
                        # Check if tomorrow is within plan date range
                        plan_end_date = plan_doc.get("end_date")
                        if isinstance(plan_end_date, str):
                            plan_end_date = date.fromisoformat(plan_end_date)

                        if tomorrow <= plan_end_date:
                            try:
                                await self._generate_tomorrow_session(
                                    plan_id=plan_id,
                                    user_id=user_id,
                                    target_date=tomorrow,
                                )
                                sessions_pregenerated += 1
                                logger.info(
                                    f"Pre-generated session for {tomorrow} in plan {plan_id}"
                                )
                            except Exception as e:
                                logger.error(
                                    f"Failed to generate session for {tomorrow} "
                                    f"in plan {plan_id}: {e}"
                                )
                                errors_encountered += 1
                        else:
                            logger.debug(
                                f"Plan {plan_id} ends on {plan_end_date}, "
                                f"skipping session generation for {tomorrow}"
                            )

                except Exception as e:
                    logger.error(
                        f"Error processing plan {plan_id}: {type(e).__name__}: {e}",
                        exc_info=False,
                    )
                    errors_encountered += 1

            # Log completion summary
            logger.info("=== Adaptive Update Task Completed ===")
            logger.info(f"Plans checked: {plans_checked}")
            logger.info(f"Plans needing re-planning: {plans_replanning_suggested}")
            logger.info(f"Sessions pre-generated: {sessions_pregenerated}")
            logger.info(f"Errors encountered: {errors_encountered}")
            logger.info(f"Completion time: {datetime.utcnow().isoformat()}Z")

        except Exception as e:
            logger.error(
                f"Adaptive Update Task failed: {type(e).__name__}: {e}",
                exc_info=True,
            )

    async def _check_replanning_needed(self, plan_id, user_id: str) -> tuple:
        """
        Check if a study plan needs re-planning based on performance and mood trends.
        
        Triggers include:
        - Completion rate < 60% over last 7 days
        - Negative emotion trend detected (>50% negative emotions)
        - Consistent failures on same topics
        
        Args:
            plan_id: ObjectId of the study plan
            user_id: ID of the plan owner
            
        Returns:
            Tuple of (should_replan: bool, reason: str)
        """
        try:
            from services.progress_tracker import AdaptiveTracker

            tracker = AdaptiveTracker(self.db)
            result = await tracker._should_trigger_replanning(plan_id, user_id)
            return result
        except Exception as e:
            logger.error(
                f"Error checking replan status for plan {plan_id}: {e}"
            )
            return False, f"Error checking replan status: {e}"

    async def _generate_tomorrow_session(
        self, plan_id, user_id: str, target_date: date
    ):
        """
        Generate tomorrow's study session.
        
        Uses DailyScheduler to create time-blocked tasks for the target date,
        with mood-based adjustments if applicable.
        
        Args:
            plan_id: ObjectId of the study plan
            user_id: ID of the plan owner
            target_date: The date for which to generate the session
            
        Raises:
            Exception: If session generation fails
        """
        from services.study_scheduler import DailyScheduler

        scheduler = DailyScheduler(self.db)
        session = await scheduler.schedule_day(
            plan_id=plan_id,
            target_date=target_date,
            user_id=user_id,
        )
        return session

    def get_scheduler_status(self) -> dict:
        """
        Get current scheduler status and running jobs.
        
        Returns:
            Dictionary with scheduler status and job details
        """
        if self.scheduler is None:
            return {"status": "not_running", "jobs": []}

        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "trigger": str(job.trigger),
                    "next_run_time": job.next_run_time.isoformat()
                    if job.next_run_time
                    else None,
                }
            )

        return {
            "status": "running" if self.scheduler.running else "paused",
            "jobs": jobs_info,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global instance
background_job_manager = BackgroundJobManager()
