
#dreamassist-fyp\backend\core\db.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from core.config import MONGO_DATABASE_URL, DATABASE_NAME

class Database:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None

db_manager = Database()

async def connect_to_mongo():
    print(f"Attempting to connect to MongoDB at {MONGO_DATABASE_URL}...")
    if MONGO_DATABASE_URL:
        db_manager.client = AsyncIOMotorClient(MONGO_DATABASE_URL)
        db_manager.db = db_manager.client[DATABASE_NAME]
        print(f"Successfully connected to MongoDB database: {DATABASE_NAME}")
    else:
        print("MongoDB connection string not configured.")

async def close_mongo_connection():
    if db_manager.client:
        db_manager.client.close()
        print("MongoDB connection closed.")

async def get_database() -> AsyncIOMotorDatabase:
    if db_manager.db is None:
        await connect_to_mongo()
        if db_manager.db is None:
             raise RuntimeError("Database is not connected")
    return db_manager.db

# Alias for compatibility with FastAPI dependencies
async def get_db() -> AsyncIOMotorDatabase:
    """FastAPI dependency for database access."""
    return await get_database()