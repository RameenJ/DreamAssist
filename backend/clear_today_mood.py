"""
Simple script to clear today's mood log for testing purposes
"""
from pymongo import MongoClient
from datetime import datetime, date
import os
from dotenv import load_dotenv

load_dotenv()

def clear_today_mood():
    # Get MongoDB credentials from env
    mongo_uri = os.getenv("DATABASE_URL")
    db_name = "dreamassist_db"
    
    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    today_str = datetime.utcnow().date().isoformat()  # YYYY-MM-DD format (UTC)
    
    # Remove today's mood log from all users
    # Using $pull operator to remove mood log with today's date
    result = db.users.update_many(
        {},  # Empty filter to update all users
        {"$pull": {"mood_logs": {"date": today_str}}}
    )
    
    print(f"✅ Cleared mood logs for date: {today_str}")
    print(f"📊 Modified {result.modified_count} user(s)")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    clear_today_mood()
