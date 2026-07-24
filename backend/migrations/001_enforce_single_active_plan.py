"""
Migration: Allow Multiple Active Plans
Users can now have multiple plans with status='active' simultaneously.
This migration is informational only - no data modifications needed.
"""

import asyncio
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

async def migrate_allow_multiple_active_plans(db: AsyncIOMotorDatabase):
    """
    Informational migration - allows users to have multiple active plans.
    No data modifications performed.
    """
    
    try:
        collection = db.study_plans
        
        # Count plans by status
        active_count = await collection.count_documents({"status": "active"})
        paused_count = await collection.count_documents({"status": "paused"})
        completed_count = await collection.count_documents({"status": "completed"})
        archived_count = await collection.count_documents({"status": "archived"})
        
        # Find users with multiple active plans (informational)
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {
                "_id": "$user_id",
                "plan_count": {"$sum": 1},
                "plans": {"$push": {
                    "id": "$_id",
                    "plan_name": "$plan_name",
                    "created_at": "$created_at"
                }}
            }},
            {"$match": {"plan_count": {"$gt": 1}}}
        ]
        
        cursor = collection.aggregate(pipeline)
        users_with_multiple_active = await cursor.to_list(length=None)
        
        logger.info("="*70)
        logger.info("MIGRATION: Allow Multiple Active Plans")
        logger.info("="*70)
        logger.info(f"\n📊 Current Plan Statistics:")
        logger.info(f"  Active plans:    {active_count}")
        logger.info(f"  Paused plans:    {paused_count}")
        logger.info(f"  Completed plans: {completed_count}")
        logger.info(f"  Archived plans:  {archived_count}")
        logger.info(f"  Total:           {active_count + paused_count + completed_count + archived_count}")
        
        logger.info(f"\n👥 Users with Multiple Active Plans: {len(users_with_multiple_active)}")
        
        if users_with_multiple_active:
            for user_data in users_with_multiple_active:
                user_id = user_data["_id"]
                plan_count = user_data["plan_count"]
                logger.info(f"\n  User {user_id}: {plan_count} active plans")
                for plan in user_data["plans"]:
                    logger.info(f"    - {plan['id']}: {plan['plan_name']}")
        
        logger.info("\n✅ Migration complete. Multiple active plans are now allowed.")
        logger.info("="*70)
        
        return {
            "status": "success",
            "message": "Multiple active plans are now allowed",
            "stats": {
                "active": active_count,
                "paused": paused_count,
                "completed": completed_count,
                "archived": archived_count,
                "users_with_multiple_active": len(users_with_multiple_active)
            }
        }
        
    except Exception as e:
        logger.error(f"✗ Migration failed: {e}", exc_info=True)
        raise


async def run_migration():
    """Run migration - for manual execution"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from core.config import MONGO_DATABASE_URL, DATABASE_NAME
    
    client = AsyncIOMotorClient(MONGO_DATABASE_URL)
    db = client[DATABASE_NAME]
    
    result = await migrate_allow_multiple_active_plans(db)
    print(f"\nMigration result: {result}")
    
    client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_migration())
