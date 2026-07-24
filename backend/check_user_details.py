#!/usr/bin/env python3
"""
Quick script to check if a user exists in the database
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from bson import ObjectId
import bcrypt

load_dotenv()

async def check_user():
    DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017/")
    DB_NAME = "dreamassist_db"
    
    try:
        client = AsyncIOMotorClient(DATABASE_URL)
        db = client[DB_NAME]
        users_collection = db.users
        
        email_to_check = "emanrizwan123@gmail.com"
        password_to_check = "Emanrizwan123@"
        
        print(f"\n🔍 Searching for user: {email_to_check}")
        print("=" * 60)
        
        # Find user by email
        user = await users_collection.find_one({"email": email_to_check})
        
        if user:
            print(f"✅ USER FOUND!")
            print(f"\nUser ID: {user.get('_id')}")
            print(f"Email: {user.get('email')}")
            print(f"Username: {user.get('username', 'N/A')}")
            print(f"Created At: {user.get('created_at')}")
            print(f"Role: {user.get('role', 'user')}")
            
            # Check password
            stored_password_hash = user.get('password_hash')
            if stored_password_hash:
                is_valid = bcrypt.checkpw(
                    password_to_check.encode('utf-8'),
                    stored_password_hash.encode('utf-8')
                )
                print(f"\nPassword Verification: {'✅ CORRECT' if is_valid else '❌ WRONG'}")
            
            # Get other info
            print(f"\nOther Details:")
            print(f"  - Unlocked Personas: {user.get('unlocked_personas', [])}")
            print(f"  - Selected Persona: {user.get('selected_persona', 'N/A')}")
            print(f"  - Email Verified: {user.get('email_verified', False)}")
        else:
            print(f"❌ USER NOT FOUND")
            print(f"\nNo user with email: {email_to_check}")
            
            # List all users for debugging
            all_users = await users_collection.find().to_list(None)
            print(f"\n📊 Total users in database: {len(all_users)}")
            if all_users:
                print("\nAll users:")
                for u in all_users:
                    print(f"  - {u.get('email')} (ID: {u.get('_id')})")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_user())
