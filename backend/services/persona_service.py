# backend/services/persona_service.py

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
from typing import List, Optional, Dict
from models.persona_schemas import PERSONA_DEFINITIONS, PersonaPublic, PersonaChat, PersonaChatResponse
from services.ai_service import AIService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PersonaService:
    """Manages AI personas and their interactions"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.personas_collection: AsyncIOMotorCollection = db.personas
        self.users_collection: AsyncIOMotorCollection = db.users
        self.conversations_collection: AsyncIOMotorCollection = db.ai_mentor_conversations
        self.messages_collection: AsyncIOMotorCollection = db.ai_mentor_messages
        self.ai_service = AIService(db)
    
    # ========================================================================
    # PERSONA MANAGEMENT
    # ========================================================================
    
    async def initialize_personas(self):
        """Initialize default personas in database (run once)"""
        try:
            count = await self.personas_collection.count_documents({})
            if count == 0:
                logger.info("Initializing personas collection...")
                for persona_id, persona_data in PERSONA_DEFINITIONS.items():
                    await self.personas_collection.insert_one({
                        "_id": persona_id,
                        **persona_data,
                        "created_at": datetime.utcnow(),
                        "is_default": persona_id == "newton"  # Newton is default
                    })
                logger.info("✅ Personas initialized successfully")
        except Exception as e:
            logger.error(f"❌ Error initializing personas: {str(e)}")
    
    async def get_all_personas(self, user_id: str) -> List[PersonaPublic]:
        """Get all personas with unlock status for user"""
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            unlocked = user.get("unlocked_personas", []) if user else []
            
            personas = []
            # Use PERSONA_DEFINITIONS from code (source of truth)
            for persona_id, persona_data in PERSONA_DEFINITIONS.items():
                # Persona is unlocked if:
                # 1. It's in user's unlocked_personas list
                # 2. It's marked as default (Newton)
                # 3. unlock_condition is "Always unlocked"
                is_unlocked = (
                    persona_id in unlocked or 
                    persona_id == "newton" or
                    persona_data.get("unlock_condition") == "Always unlocked"
                )
                personas.append(PersonaPublic(
                    persona_id=persona_id,
                    name=persona_data["name"],
                    description=persona_data["description"],
                    emoji=persona_data["emoji"],
                    color=persona_data["color"],
                    tone_style=persona_data["tone_style"],
                    speaking_style=persona_data["speaking_style"],
                    unlock_condition=persona_data["unlock_condition"],
                    system_prompt=persona_data["system_prompt"],
                    is_unlocked=is_unlocked
                ))
            return personas
        except Exception as e:
            logger.error(f"Error getting personas: {str(e)}")
            return []
    
    async def get_unlocked_personas(self, user_id: str) -> List[PersonaPublic]:
        """Get only user's unlocked personas"""
        all_personas = await self.get_all_personas(user_id)
        return [p for p in all_personas if p.is_unlocked]
    
    async def select_persona(self, user_id: str, persona_id: str) -> bool:
        """Select persona for user (with validation)"""
        try:
            # Verify persona exists and is unlocked
            personas = await self.get_all_personas(user_id)
            persona = next((p for p in personas if p.persona_id == persona_id), None)
            
            if not persona:
                logger.warning(f"Persona {persona_id} not found for user {user_id}")
                return False
            
            if not persona.is_unlocked:
                logger.warning(f"Persona {persona_id} not unlocked for user {user_id}")
                return False
            
            # Convert user_id to ObjectId
            try:
                user_object_id = ObjectId(user_id)
            except Exception as e:
                logger.error(f"Invalid user_id format: {user_id}, error: {str(e)}")
                return False
            
            # Check if user exists first
            user = await self.users_collection.find_one({"_id": user_object_id})
            if not user:
                logger.error(f"User {user_id} not found in database")
                return False
            
            # Update user's selected persona
            # Use upsert=False and check matched_count instead of modified_count
            # This handles both creating and updating the field
            result = await self.users_collection.update_one(
                {"_id": user_object_id},
                {"$set": {"selected_persona": persona_id}}
            )
            
            # Return True if either matched (and possibly modified) or if this was already set
            success = result.matched_count > 0
            if success:
                logger.info(f"✅ Persona {persona_id} selected for user {user_id}")
            else:
                logger.error(f"Failed to select persona: no user matched")
            
            return success
        except Exception as e:
            logger.error(f"Error selecting persona: {str(e)}")
            return False
    
    async def get_user_selected_persona(self, user_id: str) -> str:
        """Get user's currently selected persona"""
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            return user.get("selected_persona", "newton") if user else "newton"
        except Exception as e:
            logger.error(f"Error getting selected persona: {str(e)}")
            return "newton"  # Default to Newton
    
    async def unlock_persona(self, user_id: str, persona_id: str) -> bool:
        """Unlock a persona for user"""
        try:
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$addToSet": {"unlocked_personas": persona_id}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error unlocking persona: {str(e)}")
            return False
    
    # ========================================================================
    # CONTEXT BUILDING FOR PERSONA RESPONSES
    # ========================================================================
    
    async def build_persona_context(self, user_id: str) -> Dict[str, any]:
        """Build context for persona response (weak topics, recent activity, etc)"""
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {}
            
            # Extract weak topics from subject_profiles collection
            weak_topics = []
            try:
                subject_profiles = await self.db.subject_profiles.find(
                    {"user_id": ObjectId(user_id)}
                ).to_list(None)
                for subject in subject_profiles:
                    weak_topics.extend(subject.get("weak_topics", []))
            except:
                weak_topics = []
            
            # Get latest mood from mood_logs collection
            mood = "neutral"
            try:
                latest_mood = await self.db.mood_logs.find_one(
                    {"user_id": ObjectId(user_id)},
                    sort=[("logged_at", -1)]
                )
                if latest_mood:
                    mood = latest_mood.get("mood", "neutral")
            except:
                mood = "neutral"
            
            # Get recent activity
            recent_activity = []
            try:
                activities = await self.db.user_activities.find(
                    {"user_id": ObjectId(user_id)}
                ).sort("timestamp", -1).limit(5).to_list(5)
                
                for activity in activities:
                    activity_type = activity.get('activity_type', 'unknown')
                    subject = activity.get('subject', '')
                    if subject:
                        recent_activity.append(f"{activity_type}: {subject}")
            except:
                recent_activity = []
            
            # Get study pace from subject profile
            study_pace = "moderate"
            try:
                first_subject = await self.db.subject_profiles.find_one(
                    {"user_id": ObjectId(user_id)}
                )
                if first_subject:
                    study_pace = first_subject.get("study_pace", "moderate")
            except:
                study_pace = "moderate"
            
            return {
                "weak_topics": weak_topics[:3],  # Top 3 weak topics
                "recent_activity": recent_activity,
                "mood": mood,
                "study_pace": study_pace
            }
        except Exception as e:
            logger.error(f"Error building context: {str(e)}")
            return {}
    
    # ========================================================================
    # PERSONA CHAT
    # ========================================================================
    
    async def chat_with_persona(
        self, 
        user_id: str, 
        message: str, 
        persona_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> PersonaChatResponse:
        """
        Main chat function: Get persona response with context
        """
        try:
            # Get persona
            if not persona_id:
                persona_id = await self.get_user_selected_persona(user_id)
            
            persona = await self.personas_collection.find_one({"_id": persona_id})
            if not persona:
                raise ValueError(f"Persona {persona_id} not found")
            
            # Build context for the persona
            context = await self.build_persona_context(user_id)
            
            # Create or get conversation
            if not conversation_id:
                conv_result = await self.conversations_collection.insert_one({
                    "user_id": ObjectId(user_id),
                    "persona_id": persona_id,
                    "message_count": 0,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                conversation_id = str(conv_result.inserted_id)
            else:
                await self.conversations_collection.update_one(
                    {"_id": ObjectId(conversation_id)},
                    {"$inc": {"message_count": 1}, "$set": {"updated_at": datetime.utcnow()}}
                )
            
            # Build the system prompt with context
            full_system_prompt = self._build_system_prompt_with_context(
                persona["system_prompt"],
                context
            )
            
            # Get AI response using chat method
            response = await self.ai_service.chat(
                system_prompt=full_system_prompt,
                user_message=message
            )
            
            # Save message to database
            await self.messages_collection.insert_one({
                "conversation_id": ObjectId(conversation_id),
                "sender": "user",
                "content": message,
                "persona_id": persona_id,
                "created_at": datetime.utcnow()
            })
            
            await self.messages_collection.insert_one({
                "conversation_id": ObjectId(conversation_id),
                "sender": "assistant",
                "content": response,
                "persona_id": persona_id,
                "created_at": datetime.utcnow()
            })
            
            return PersonaChatResponse(
                response=response,
                persona_name=persona["name"],
                persona_emoji=persona["emoji"],
                persona_color=persona["color"],
                conversation_id=conversation_id
            )
        except Exception as e:
            logger.error(f"Error in chat_with_persona: {str(e)}")
            raise
    
    # ========================================================================
    # PROMPT ENGINEERING
    # ========================================================================
    
    def _build_system_prompt_with_context(
        self, 
        base_system_prompt: str, 
        context: Dict
    ) -> str:
        """
        Enhance system prompt with user context
        This is where prompt engineering happens!
        """
        
        context_section = ""
        
        if context.get("weak_topics"):
            context_section += f"\n\n⚠️ USER'S WEAK TOPICS: {', '.join(context['weak_topics'])}"
            context_section += "\nTry to incorporate explanations related to these topics if relevant."
        
        if context.get("mood") and context["mood"] != "neutral":
            mood_message = {
                "stressed": "The user is feeling stressed. Be especially encouraging and take a calm approach.",
                "frustrated": "The user is frustrated. Break things down more clearly and offer reassurance.",
                "confused": "The user is confused. Start from basics and be extra patient.",
                "motivated": "The user is motivated! You can challenge them with deeper concepts.",
                "engaged": "The user is engaged and excited to learn. Keep the energy high!",
                "confident": "The user is confident. You can dive into complex topics."
            }
            if context["mood"] in mood_message:
                context_section += f"\n\n💭 MOOD CONTEXT: {mood_message[context['mood']]}"
        
        if context.get("study_pace"):
            pace_message = {
                "slow": "Take your time with explanations. Use more examples and go step-by-step.",
                "moderate": "Use a balanced pace with clear examples.",
                "fast": "You can move quickly through concepts. The user prefers efficient explanations."
            }
            if context["study_pace"] in pace_message:
                context_section += f"\n\n⏱️ LEARNING PACE: {pace_message[context['study_pace']]}"
        
        full_prompt = base_system_prompt + context_section
        return full_prompt
    
    # ========================================================================
    # CHAT HISTORY
    # ========================================================================
    
    async def get_chat_history(self, user_id: str, persona_id: str) -> Optional[Dict]:
        """
        Get most recent conversation with a persona for user
        Returns conversation_id and all messages in chronological order
        """
        try:
            # Get most recent conversation with this persona
            conversation = await self.conversations_collection.find_one(
                {
                    "user_id": ObjectId(user_id),
                    "persona_id": persona_id
                },
                sort=[("updated_at", -1)]
            )
            
            if not conversation:
                return None
            
            # Fetch all messages for this conversation
            messages = await self.messages_collection.find(
                {"conversation_id": conversation["_id"]},
                sort=[("created_at", 1)]  # Chronological order
            ).to_list(None)
            
            # Get persona details
            persona = await self.personas_collection.find_one({"_id": persona_id})
            if not persona:
                return None
            
            # Format messages for response
            formatted_messages = [
                {
                    "sender": msg["sender"],
                    "content": msg["content"],
                    "created_at": msg["created_at"]
                }
                for msg in messages
            ]
            
            return {
                "conversation_id": str(conversation["_id"]),
                "persona_id": persona_id,
                "persona_name": persona["name"],
                "persona_emoji": persona["emoji"],
                "persona_color": persona["color"],
                "messages": formatted_messages
            }
        except Exception as e:
            logger.error(f"Error fetching chat history: {str(e)}")
            return None
