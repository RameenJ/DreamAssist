#!/usr/bin/env python3
"""Check tasks and query matching"""
import asyncio
from datetime import datetime, date, time, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def check_tasks():
    mongo_url = "mongodb+srv://DreamAssistAdmin:YxHNjRBC5J4WEUb@dreamassist-cluster.ub8mwuo.mongodb.net/?appName=dreamassist-cluster"
    client = AsyncIOMotorClient(mongo_url)
    db = client.dreamassist_db
    
    try:
        # Find user's active plan
        user_id = ObjectId("69e5c1e35b40c8e59b49c2af")
        plan = await db.study_plans.find_one({
            "user_id": user_id,
            "status": {"$in": ["active", "in_progress"]}
        })
        
        if not plan:
            print("No active plan found")
            return
        
        plan_id = plan["_id"]
        
        # Check existing sessions for today
        today = date.today()
        today_datetime = datetime.combine(today, time.min)
        tomorrow_datetime = datetime.combine(today + timedelta(days=1), time.min)
        
        session = await db.study_sessions.find_one({
            "user_id": user_id,
            "session_date": {"$gte": today_datetime, "$lt": tomorrow_datetime},
            "plan_id": None
        })
        
        if session:
            print(f"✅ Session exists for today")
            blocks = session.get('time_blocks', [])
            print(f"   Time blocks: {len(blocks)}")
            for block in blocks[:3]:
                print(f"      - {block.get('topic')}: {block.get('start_time')} to {block.get('end_time')}")
        else:
            print("❌ No session found for today")
            
            # Check what tasks would be included if we look at all statuses
            all_tasks = await db.study_tasks.find({"plan_id": plan_id}).to_list(None)
            
            print(f"\n📊 Task status distribution for today:")
            status_counts = {}
            for task in all_tasks:
                if task.get('scheduled_date'):
                    sched_date = task['scheduled_date']
                    if isinstance(sched_date, datetime):
                        if sched_date.date() == today:
                            status = task.get('status', 'unknown')
                            status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                print(f"   {status}: {count}")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_tasks())
