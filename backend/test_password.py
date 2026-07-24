import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

MONGO_DATABASE_URL = "mongodb+srv://DreamAssistAdmin:YxHNjRBC5J4WEUb@dreamassist-cluster.ub8mwuo.mongodb.net/?appName=dreamassist-cluster"
DATABASE_NAME = "dreamassist_db"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def test_password():
    client = AsyncIOMotorClient(MONGO_DATABASE_URL)
    db = client[DATABASE_NAME]
    user = await db['users'].find_one({'email': 'rameen123@gmail.com'})
    
    if user:
        password_to_test = "Rameen123@"
        hashed_password = user.get('hashed_password')
        
        print(f"Testing password: {password_to_test}")
        print(f"Hashed password in DB: {hashed_password[:30]}...")
        
        try:
            is_correct = pwd_context.verify(password_to_test, hashed_password)
            if is_correct:
                print('✅ Password is CORRECT!')
            else:
                print('❌ Password is WRONG!')
        except Exception as e:
            print(f'❌ Error verifying password: {e}')
    else:
        print('User not found')
    
    client.close()

asyncio.run(test_password())
