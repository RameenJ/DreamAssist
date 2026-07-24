import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import json

load_dotenv()

async def check():
    client = AsyncIOMotorClient(os.getenv('DATABASE_URL', 'mongodb://localhost:27017/'))
    db = client['dreamassist_db']
    user = await db.users.find_one({'email': 'emanrizwan123@gmail.com'})
    
    if user:
        print("\n📋 COMPLETE USER DATA:")
        print("=" * 60)
        # Show all fields
        for key, value in user.items():
            if key == '_id':
                print(f"{key}: {value}")
            elif key == 'password_hash':
                print(f"{key}: {'[HASHED PASSWORD]' if value else '[NO PASSWORD]'}")
            else:
                print(f"{key}: {value}")
    client.close()

asyncio.run(check())
