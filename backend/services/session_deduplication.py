"""
Session Deduplication Utility

Finds and removes duplicate study_sessions created before the unique index was in place.
Keeps the best session (most recently created, or one with completed blocks if available).
"""

from datetime import datetime, date, time
from typing import Dict, List, Tuple, Optional
from bson import ObjectId
from core.db import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


async def deduplicate_sessions(
    db: AsyncIOMotorDatabase,
    dry_run: bool = True,
    keep_criteria: str = "earliest_created"  # or "most_completed"
) -> Dict:
    """
    Find and remove duplicate sessions across all users.

    Duplicates are identified by matching (user_id, session_date, aggregated_plan_ids).
    For each group of duplicates:
    - If keep_criteria == "earliest_created": keep the one created first
    - If keep_criteria == "most_completed": keep the one with most completed_blocks

    Args:
        db: MongoDB database connection
        dry_run: If True, only report duplicates without deleting
        keep_criteria: Which session to keep in each duplicate group

    Returns:
        Dict with statistics:
        {
            "total_duplicate_groups": int,
            "total_sessions_to_delete": int,
            "deleted_sessions": int,
            "errors": int,
            "sample_groups": List[Dict]  # First 5 groups for review
        }
    """
    logger.info(f"🔍 Starting session deduplication (dry_run={dry_run}, keep_criteria={keep_criteria})")

    stats = {
        "total_duplicate_groups": 0,
        "total_sessions_to_delete": 0,
        "deleted_sessions": 0,
        "errors": 0,
        "sample_groups": [],
    }

    # Find all duplicate groups using aggregation pipeline
    pipeline = [
        {
            "$group": {
                "_id": {
                    "user_id": "$user_id",
                    "session_date": "$session_date",
                    # Sort plan IDs so [A,B] is same as [B,A]
                    "aggregated_plan_ids": {
                        "$cond": [
                            {"$isArray": "$aggregated_plan_ids"},
                            {"$sort": {"$map": {"input": "$aggregated_plan_ids", "as": "pid", "in": "$$pid"}}},
                            None
                        ]
                    }
                },
                "sessions": {
                    "$push": {
                        "_id": "$_id",
                        "created_at": "$created_at",
                        "completed_blocks": "$completed_blocks",
                        "total_blocks": "$total_blocks",
                    }
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$match": {"count": {"$gt": 1}}  # Only duplicate groups
        },
        {
            "$sort": {"count": -1}
        }
    ]

    duplicate_groups = []
    cursor = db.study_sessions.aggregate(pipeline)
    async for group in cursor:
        duplicate_groups.append(group)

    stats["total_duplicate_groups"] = len(duplicate_groups)
    logger.info(f"📊 Found {len(duplicate_groups)} duplicate groups")

    if not duplicate_groups:
        logger.info("✅ No duplicates found!")
        return stats

    # Process each duplicate group
    sessions_to_delete = []

    for idx, group in enumerate(duplicate_groups):
        sessions = group["sessions"]
        key = group["_id"]

        # Determine which session to keep
        if keep_criteria == "earliest_created":
            # Keep the one with earliest created_at
            sessions_sorted = sorted(
                sessions,
                key=lambda s: s.get("created_at") or datetime.utcnow()
            )
            keep_session = sessions_sorted[0]
            delete_sessions = sessions_sorted[1:]
        else:  # most_completed
            # Keep the one with most completed_blocks (tie-break by earliest created)
            sessions_sorted = sorted(
                sessions,
                key=lambda s: (
                    -(s.get("completed_blocks") or 0),  # Negative for descending
                    s.get("created_at") or datetime.utcnow()
                )
            )
            keep_session = sessions_sorted[0]
            delete_sessions = sessions_sorted[1:]

        # Record for deletion
        for delete_session in delete_sessions:
            sessions_to_delete.append(delete_session["_id"])

        # Add to sample for review (first 5 groups)
        if idx < 5:
            stats["sample_groups"].append({
                "user_id": str(key["user_id"]),
                "session_date": str(key["session_date"]),
                "num_duplicates": len(sessions),
                "keep_session_id": str(keep_session["_id"]),
                "keep_session_created_at": keep_session.get("created_at"),
                "keep_session_completed_blocks": keep_session.get("completed_blocks"),
                "delete_session_ids": [str(s["_id"]) for s in delete_sessions],
            })

        logger.debug(
            f"  Group {idx + 1}: user={key['user_id']}, date={key['session_date']}, "
            f"count={len(sessions)}, keep_id={keep_session['_id']}"
        )

    stats["total_sessions_to_delete"] = len(sessions_to_delete)

    if dry_run:
        logger.info(f"🏜️ DRY RUN: Would delete {len(sessions_to_delete)} sessions")
        return stats

    # Actually delete the sessions
    logger.info(f"🗑️ Deleting {len(sessions_to_delete)} duplicate sessions...")

    for session_id in sessions_to_delete:
        try:
            result = await db.study_sessions.delete_one({"_id": session_id})
            if result.deleted_count == 1:
                stats["deleted_sessions"] += 1
                logger.debug(f"   Deleted session {session_id}")
            else:
                logger.warning(f"   Session {session_id} not found for deletion")
        except Exception as e:
            stats["errors"] += 1
            logger.error(f"   Error deleting session {session_id}: {e}")

    logger.info(
        f"✅ Deduplication complete: {stats['deleted_sessions']} deleted, "
        f"{stats['errors']} errors"
    )

    return stats


async def find_duplicate_sessions(db: AsyncIOMotorDatabase) -> List[Dict]:
    """
    Find all duplicate sessions without deleting them.

    Returns:
        List of duplicate groups with details.
    """
    logger.info("🔍 Finding duplicate sessions...")

    pipeline = [
        {
            "$group": {
                "_id": {
                    "user_id": "$user_id",
                    "session_date": "$session_date",
                    "aggregated_plan_ids": {
                        "$cond": [
                            {"$isArray": "$aggregated_plan_ids"},
                            {"$sort": {"$map": {"input": "$aggregated_plan_ids", "as": "pid", "in": "$$pid"}}},
                            None
                        ]
                    }
                },
                "sessions": {
                    "$push": {
                        "_id": "$_id",
                        "created_at": "$created_at",
                        "completed_blocks": "$completed_blocks",
                        "total_blocks": "$total_blocks",
                        "status": "$status",
                    }
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$match": {"count": {"$gt": 1}}
        },
        {
            "$sort": {"count": -1}
        }
    ]

    duplicate_groups = []
    cursor = db.study_sessions.aggregate(pipeline)
    async for group in cursor:
        duplicate_groups.append(group)

    logger.info(f"📊 Found {len(duplicate_groups)} duplicate groups")
    return duplicate_groups


async def get_deduplication_report(
    db: AsyncIOMotorDatabase,
    keep_criteria: str = "earliest_created"
) -> str:
    """
    Generate a human-readable report of duplicates and which would be deleted.

    Returns:
        Formatted string report.
    """
    duplicate_groups = await find_duplicate_sessions(db)

    if not duplicate_groups:
        return "✅ No duplicate sessions found!"

    report_lines = [
        f"📋 Deduplication Report ({len(duplicate_groups)} groups)\n",
        f"Keep criteria: {keep_criteria}\n",
        "=" * 80,
    ]

    total_to_delete = 0

    for idx, group in enumerate(duplicate_groups, 1):
        sessions = group["sessions"]
        key = group["_id"]

        # Determine which would be kept
        if keep_criteria == "earliest_created":
            sessions_sorted = sorted(
                sessions,
                key=lambda s: s.get("created_at") or datetime.utcnow()
            )
            keep_session = sessions_sorted[0]
            delete_sessions = sessions_sorted[1:]
        else:  # most_completed
            sessions_sorted = sorted(
                sessions,
                key=lambda s: (
                    -(s.get("completed_blocks") or 0),
                    s.get("created_at") or datetime.utcnow()
                )
            )
            keep_session = sessions_sorted[0]
            delete_sessions = sessions_sorted[1:]

        total_to_delete += len(delete_sessions)

        report_lines.append(f"\nGroup {idx}:")
        report_lines.append(f"  User: {key['user_id']}")
        report_lines.append(f"  Date: {key['session_date']}")
        report_lines.append(f"  Plans: {key['aggregated_plan_ids']}")
        report_lines.append(f"  Total duplicates: {len(sessions)}")
        report_lines.append(f"\n  KEEP:")
        report_lines.append(f"    ID: {keep_session['_id']}")
        report_lines.append(f"    Created: {keep_session.get('created_at')}")
        report_lines.append(f"    Completed blocks: {keep_session.get('completed_blocks')}/{keep_session.get('total_blocks')}")
        report_lines.append(f"\n  DELETE ({len(delete_sessions)}):")

        for ds in delete_sessions:
            report_lines.append(f"    - ID: {ds['_id']}")
            report_lines.append(f"      Created: {ds.get('created_at')}")
            report_lines.append(f"      Completed blocks: {ds.get('completed_blocks')}/{ds.get('total_blocks')}")

    report_lines.append("\n" + "=" * 80)
    report_lines.append(f"\n📊 Summary:")
    report_lines.append(f"  Duplicate groups: {len(duplicate_groups)}")
    report_lines.append(f"  Sessions to delete: {total_to_delete}")
    report_lines.append(f"\nRun deduplicate_sessions(db, dry_run=False, keep_criteria='{keep_criteria}')")
    report_lines.append(f"to perform the actual deletion.")

    return "\n".join(report_lines)


# Helper function for one-time use in main.py or CLI
async def cleanup_duplicate_sessions(db: AsyncIOMotorDatabase) -> None:
    """
    One-shot cleanup function for duplicate sessions.
    This can be called from a management endpoint or CLI command.

    Usage in main.py or a CLI script:
        await cleanup_duplicate_sessions(db)
    """
    logger.info("=" * 80)
    logger.info("SESSION DEDUPLICATION CLEANUP")
    logger.info("=" * 80)

    # First, show a report
    report = await get_deduplication_report(db, keep_criteria="earliest_created")
    logger.info("\n" + report + "\n")

    # Ask for confirmation (would need stdin handling if running as CLI)
    logger.info("Proceeding with deduplication (earliest_created)...")

    # Run deduplication
    stats = await deduplicate_sessions(
        db,
        dry_run=False,
        keep_criteria="earliest_created"
    )

    # Log results
    logger.info("\n" + "=" * 80)
    logger.info("DEDUPLICATION RESULTS")
    logger.info("=" * 80)
    logger.info(f"Total duplicate groups found: {stats['total_duplicate_groups']}")
    logger.info(f"Total sessions deleted: {stats['deleted_sessions']}")
    logger.info(f"Errors encountered: {stats['errors']}")
    logger.info("=" * 80)
