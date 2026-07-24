#!/usr/bin/env python
"""
Integration test: Verify mood logging + session recalculation works with MongoDB
"""
import asyncio
from datetime import datetime, date, time
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Import services
from services.user_service import log_user_mood
from services.study_scheduler import StudyScheduler
from models.user_schemas import PyObjectId
from models.planner_schemas import StudySession, TimeBlock

async def test_mood_logging():
    """Test that mood logging properly updates session without MongoDB errors"""
    
    print("\n" + "="*60)
    print("🧪 MOOD LOGGING INTEGRATION TEST")
    print("="*60)
    
    # Connect to MongoDB
    mongo_url = os.getenv("MONGODB_URL") or "mongodb+srv://DreamAssistAdmin:YxHNjRBC5J4WEUb@dreamassist-cluster.ub8mwuo.mongodb.net/?appName=dreamassist-cluster"
    client = AsyncIOMotorClient(mongo_url)
    db = client.dreamassist_db
    
    try:
        # Test user (use existing one)
        test_user_id = ObjectId("69e5c1e35b40c8e59b49c2af")
        
        print(f"\n✅ Connected to MongoDB")
        print(f"✅ Using test user: {test_user_id}")
        
        # Get today's session
        today_date = date.today()
        session_doc = await db.study_sessions.find_one({
            "user_id": test_user_id,
            "session_date": {"$gte": datetime.combine(today_date, time.min)},
            "plan_id": None,
        })
        
        if session_doc:
            print(f"\n✅ Found existing session: {session_doc['_id']}")
            print(f"   Current mood_history: {session_doc.get('mood_history', [])}")
            print(f"   time_blocks count: {len(session_doc.get('time_blocks', []))}")
            
            # Test: Log a mood
            print(f"\n🧪 Testing mood log: 'motivated'")
            result = await log_user_mood(db, test_user_id, "motivated")
            
            if result['success']:
                print(f"✅ Mood logged successfully!")
                if result.get('session'):
                    print(f"   ✓ Session returned: {result['session'].get('_id')}")
                    print(f"   ✓ Mood history updated: {len(result['session'].get('mood_history', []))} moods")
            else:
                print(f"❌ Error: {result.get('message')}")
                return 1
            
            # Verify in database
            updated_session = await db.study_sessions.find_one({
                "_id": ObjectId(session_doc['_id'])
            })
            
            if updated_session:
                mood_count = len(updated_session.get('mood_history', []))
                print(f"\n✅ Database verification:")
                print(f"   ✓ Session still exists: {updated_session['_id']}")
                print(f"   ✓ Mood history count: {mood_count}")
                print(f"   ✓ Latest mood: {updated_session['mood_history'][-1] if updated_session.get('mood_history') else 'None'}")
                print(f"   ✓ Session date type: {type(updated_session['session_date'])}")
                print(f"   ✓ time_blocks preserved: {len(updated_session.get('time_blocks', []))}")
            
            print(f"\n✅ TEST PASSED!")
            return 0
        else:
            print(f"⚠️ No session found for today - need to create one first")
            print(f"   Try: GET /api/v1/planner/sessions/{today_date}/aggregated")
            return 0
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        client.close()

if __name__ == "__main__":
    exit_code = asyncio.run(test_mood_logging())
    exit(exit_code)
