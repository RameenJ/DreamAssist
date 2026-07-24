"""
Migration: Create Unique Session Index and Deduplicate Sessions

This migration:
1. Creates the unique compound index on (user_id, session_date, aggregated_plan_ids)
2. Deduplicates existing sessions (keeps earliest created)
3. Logs detailed results

Usage:
    from migrations.session_deduplication_migration import run_migration
    stats = await run_migration(db)
"""

from datetime import datetime, time
from typing import Dict, List
from bson import ObjectId
from core.db import AsyncIOMotorDatabase
from services.session_deduplication import deduplicate_sessions, get_deduplication_report
import logging

logger = logging.getLogger(__name__)


async def run_migration(db: AsyncIOMotorDatabase, dry_run: bool = False) -> Dict:
    """
    Main migration entry point.

    Args:
        db: MongoDB database connection
        dry_run: If True, only report what would be done

    Returns:
        Migration statistics
    """
    logger.info("=" * 80)
    logger.info("SESSION DEDUPLICATION MIGRATION")
    logger.info("=" * 80)

    migration_stats = {
        "phase": "started",
        "index_created": False,
        "index_error": None,
        "duplicates_found": 0,
        "duplicates_deleted": 0,
        "deduplication_errors": 0,
        "dry_run": dry_run,
    }

    # Phase 1: Create Unique Index
    logger.info("\n🔧 Phase 1: Creating unique session index...")
    try:
        await db.study_sessions.create_index(
            [
                ("user_id", 1),
                ("session_date", 1),
                ("aggregated_plan_ids", 1),
            ],
            unique=True,
            name="idx_unique_session_key",
            background=True,  # Don't block other operations
        )
        migration_stats["index_created"] = True
        logger.info("✅ Unique index created successfully")
    except Exception as e:
        # Check if it already exists
        if "already exists" in str(e) or "duplicate key" in str(e).lower():
            logger.info("✅ Index already exists (idempotent)")
            migration_stats["index_created"] = True
        else:
            migration_stats["index_error"] = str(e)
            logger.error(f"❌ Error creating index: {e}")
            raise

    # Phase 2: Find Duplicates Report
    logger.info("\n📊 Phase 2: Analyzing duplicate sessions...")
    try:
        report = await get_deduplication_report(db, keep_criteria="earliest_created")
        logger.info("\n" + report + "\n")
    except Exception as e:
        logger.error(f"❌ Error generating report: {e}")
        raise

    # Phase 3: Deduplicate Sessions
    logger.info("\n🔄 Phase 3: Deduplicating sessions...")
    try:
        dedup_stats = await deduplicate_sessions(
            db,
            dry_run=dry_run,
            keep_criteria="earliest_created"
        )
        migration_stats.update(dedup_stats)
        logger.info(f"✅ Deduplication complete (dry_run={dry_run})")
    except Exception as e:
        logger.error(f"❌ Error during deduplication: {e}")
        raise

    # Final Summary
    logger.info("\n" + "=" * 80)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Index created: {migration_stats['index_created']}")
    logger.info(f"Duplicate groups found: {migration_stats.get('total_duplicate_groups', 0)}")
    logger.info(f"Sessions deleted: {migration_stats.get('deleted_sessions', 0)}")
    logger.info(f"Errors: {migration_stats.get('errors', 0)}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("=" * 80)

    return migration_stats


async def verify_migration(db: AsyncIOMotorDatabase) -> Dict:
    """
    Verify that the migration was successful.

    Checks:
    1. Unique index exists
    2. No duplicate sessions remain
    3. Index configuration is correct

    Returns:
        Verification results
    """
    logger.info("🔍 Verifying migration...")

    verify_stats = {
        "index_exists": False,
        "index_name": None,
        "no_duplicates": False,
        "duplicate_count": 0,
        "total_sessions": 0,
        "errors": [],
    }

    # Check 1: Verify index exists
    try:
        indexes = await db.study_sessions.list_indexes().to_list(None)
        for idx in indexes:
            if idx["name"] == "idx_unique_session_key":
                verify_stats["index_exists"] = True
                verify_stats["index_name"] = idx["name"]
                logger.info(f"✅ Index 'idx_unique_session_key' exists")
                logger.debug(f"   Key spec: {idx['key']}")
                logger.debug(f"   Unique: {idx.get('unique', False)}")
                break
        
        if not verify_stats["index_exists"]:
            verify_stats["errors"].append("Unique index not found")
            logger.warning("⚠️ Unique index not found")
    except Exception as e:
        verify_stats["errors"].append(f"Error checking indexes: {e}")
        logger.error(f"❌ Error checking indexes: {e}")

    # Check 2: Count total sessions
    try:
        total_count = await db.study_sessions.count_documents({})
        verify_stats["total_sessions"] = total_count
        logger.info(f"📊 Total sessions in collection: {total_count}")
    except Exception as e:
        verify_stats["errors"].append(f"Error counting sessions: {e}")
        logger.error(f"❌ Error counting sessions: {e}")

    # Check 3: Look for any remaining duplicates
    try:
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
                    "count": {"$sum": 1}
                }
            },
            {
                "$match": {"count": {"$gt": 1}}
            },
            {
                "$count": "duplicate_groups"
            }
        ]

        result = await db.study_sessions.aggregate(pipeline).to_list(None)
        duplicate_count = result[0]["duplicate_groups"] if result else 0
        verify_stats["duplicate_count"] = duplicate_count
        verify_stats["no_duplicates"] = (duplicate_count == 0)

        if verify_stats["no_duplicates"]:
            logger.info("✅ No duplicate sessions found")
        else:
            msg = f"⚠️ Found {duplicate_count} duplicate groups remaining"
            verify_stats["errors"].append(msg)
            logger.warning(msg)

    except Exception as e:
        verify_stats["errors"].append(f"Error checking duplicates: {e}")
        logger.error(f"❌ Error checking duplicates: {e}")

    # Final result
    logger.info("\n" + "=" * 80)
    logger.info("VERIFICATION RESULTS")
    logger.info("=" * 80)
    if not verify_stats["errors"]:
        logger.info("✅ Migration verified successfully!")
    else:
        logger.warning("⚠️ Migration verification found issues:")
        for error in verify_stats["errors"]:
            logger.warning(f"  - {error}")
    logger.info("=" * 80)

    return verify_stats


async def rollback_migration(db: AsyncIOMotorDatabase) -> Dict:
    """
    Rollback the migration by dropping the unique index.

    WARNING: After rollback, duplicate sessions can be created again!

    Returns:
        Rollback results
    """
    logger.warning("⚠️ ROLLING BACK migration...")

    rollback_stats = {
        "index_dropped": False,
        "error": None,
    }

    try:
        await db.study_sessions.drop_index("idx_unique_session_key")
        rollback_stats["index_dropped"] = True
        logger.info("✅ Unique index dropped")
    except Exception as e:
        if "index not found" in str(e).lower():
            logger.info("ℹ️ Index doesn't exist (already rolled back or never created)")
            rollback_stats["index_dropped"] = True
        else:
            rollback_stats["error"] = str(e)
            logger.error(f"❌ Error dropping index: {e}")

    return rollback_stats


# Testing utilities

async def create_test_duplicate_sessions(db: AsyncIOMotorDatabase) -> Dict:
    """
    Create test duplicate sessions for verification.
    Useful for testing the deduplication logic.

    Returns:
        Dict with IDs of created test sessions
    """
    logger.info("🧪 Creating test duplicate sessions...")

    test_user_id = ObjectId()
    test_date = datetime.combine(datetime.now().date(), time.min)
    test_plan_ids = [ObjectId(), ObjectId()]

    session_1 = {
        "user_id": test_user_id,
        "session_date": test_date,
        "aggregated_plan_ids": sorted([str(pid) for pid in test_plan_ids]),  # Sorted
        "status": "scheduled",
        "created_at": datetime.utcnow(),
        "total_blocks": 3,
        "completed_blocks": 0,
        "notes": "Test duplicate 1"
    }

    session_2 = {
        "user_id": test_user_id,
        "session_date": test_date,
        "aggregated_plan_ids": sorted([str(pid) for pid in test_plan_ids]),  # Same, sorted
        "status": "scheduled",
        "created_at": datetime.utcnow(),
        "total_blocks": 3,
        "completed_blocks": 2,
        "notes": "Test duplicate 2"
    }

    try:
        result1 = await db.study_sessions.insert_one(session_1)
        result2 = await db.study_sessions.insert_one(session_2)

        logger.info(f"✅ Created 2 test duplicate sessions")
        logger.info(f"   Session 1 (no completion): {result1.inserted_id}")
        logger.info(f"   Session 2 (2/3 blocks): {result2.inserted_id}")

        return {
            "test_user_id": test_user_id,
            "test_date": test_date,
            "session_1_id": result1.inserted_id,
            "session_2_id": result2.inserted_id,
        }
    except Exception as e:
        logger.error(f"❌ Error creating test sessions: {e}")
        return {"error": str(e)}
