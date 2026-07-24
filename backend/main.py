# C:\Users\mohsi\Projects\learn-ease-fyp\backend\main.py
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from core.db import connect_to_mongo, close_mongo_connection, get_database 
from motor.motor_asyncio import AsyncIOMotorDatabase
from routers import auth_router, book_router, ai_router, subject_router, user_router, progress_router, recommendation_router, forum_router, study_groups_router, chat_router, diagnostic_router, persona_router, subject_profile_router, planner_router, goal_based_planning_router, conflict_detection_router
from services.background_jobs import background_job_manager
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Lifespan manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ===== STARTUP =====
    logger.info("🚀 DreamAssist Backend Starting Up...")
    
    # Connect to MongoDB
    await connect_to_mongo()
    logger.info("✅ MongoDB connection established")
    
    # Start background job scheduler
    db = await get_database()
    await background_job_manager.start(db)
    logger.info("✅ Background job scheduler initialized")
    
    # Log scheduler status
    scheduler_status = background_job_manager.get_scheduler_status()
    logger.info(f"📋 Scheduler Status: {scheduler_status}")
    
    logger.info("🎯 DreamAssist Backend is READY!")
    
    yield
    
    # ===== SHUTDOWN =====
    logger.info("🛑 DreamAssist Backend Shutting Down...")
    
    # Stop background job scheduler
    await background_job_manager.stop()
    logger.info("✅ Background job scheduler stopped")
    
    # Close MongoDB connection
    await close_mongo_connection()
    logger.info("✅ MongoDB connection closed")
    
    logger.info("👋 Shutdown Complete")

app = FastAPI(lifespan=lifespan) # Pass lifespan manager to app

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://10.0.2.2:8000",
    # NOTE: '*' (allow all origins) removed for security. Add specific domains in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  
)

app.include_router(auth_router.router)
app.include_router(book_router.router)
app.include_router(ai_router.router)
app.include_router(subject_router.router)
app.include_router(user_router.router)
app.include_router(progress_router.router)
app.include_router(recommendation_router.router)
app.include_router(forum_router.router)
app.include_router(study_groups_router.router)
app.include_router(chat_router.router)
app.include_router(diagnostic_router.router)
app.include_router(subject_profile_router.router)
app.include_router(planner_router.router, prefix="/api/v1/planner", tags=["planner"])
app.include_router(goal_based_planning_router.router)
app.include_router(conflict_detection_router.router)
app.include_router(persona_router.router)

@app.get("/")
async def root():
    return {"message": "Hello from DreamAssist Backend!"}

@app.get("/api/health/scheduler")
async def get_scheduler_status():
    """
    Get the current status of the background job scheduler.
    
    Returns:
        Dictionary with scheduler status and list of scheduled jobs
    """
    return background_job_manager.get_scheduler_status()


@app.get("/api/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Returns:
        Health status of:
        - API server
        - MongoDB connection
        - Background job scheduler
    """
    db = await get_database()
    
    try:
        # Test database connection
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    scheduler_status = background_job_manager.get_scheduler_status()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "api": "operational",
        "database": db_status,
        "scheduler": scheduler_status["status"],
        "jobs": len(scheduler_status.get("jobs", [])),
    }


# ============================================================================
# Background Task Integration Complete
# ============================================================================
# APScheduler is now managing the adaptive_update_task
# - Runs daily at midnight UTC
# - Pre-generates tomorrow's study sessions
# - Checks for re-planning triggers
# - Detailed logging and error handling
# ============================================================================
# ============================================================================
# Background Task Integration Complete ✅
# ============================================================================
# APScheduler is now managing adaptive study plan updates.
# 
# Features:
# - Daily execution at midnight UTC
# - Pre-generates next day's study sessions
# - Checks for re-planning triggers based on performance/mood
# - Comprehensive logging and error handling
# - Graceful shutdown on app termination
#
# Status Monitoring:
# - GET /api/health/scheduler - Returns current scheduler status and jobs
# ============================================================================
