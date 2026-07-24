#!/usr/bin/env python3
"""
Initialize missing fields for existing users
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_user():
    client = AsyncIOMotorClient(os.getenv('DATABASE_URL', 'mongodb://localhost:27017/'))
    db = client['dreamassist_db']
    users_collection = db.users
    
    email = "emanrizwan123@gmail.com"
    
    print(f"\n🔧 Fixing user: {email}")
    print("=" * 60)
    
    try:
        # Add missing fields to user
        result = await users_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "unlocked_personas": ["newton"],  # Newton is default and always unlocked
                    "selected_persona": "newton"
                }
            }
        )
        
        if result.modified_count > 0:
            print("✅ User profile updated successfully!")
            print("   - Added unlocked_personas: ['newton']")
            print("   - Added selected_persona: 'newton'")
        else:
            print("⚠️ User not found or no changes needed")
        
        # Verify the update
        user = await users_collection.find_one({"email": email})
        if user:
            print(f"\n✅ Verified:")
            print(f"   - unlocked_personas: {user.get('unlocked_personas', [])}")
            print(f"   - selected_persona: {user.get('selected_persona', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_user())
