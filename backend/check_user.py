import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import MONGO_DATABASE_URL, DATABASE_NAME

async def check_user():
    client = AsyncIOMotorClient(MONGO_DATABASE_URL)
    db = client[DATABASE_NAME]
    user = await db['users'].find_one({'email': 'rameen123@gmail.com'})
    if user:
        print('✅ User FOUND in database!')
        print(f'Email: {user.get("email")}')
        print(f'Name: {user.get("firstname")} {user.get("lastname")}')
        print(f'Has password hash: {"hashed_password" in user}')
    else:
        print('❌ User NOT found in database!')
    client.close()

asyncio.run(check_user())
