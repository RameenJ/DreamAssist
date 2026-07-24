# backend/routers/persona_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from core.db import get_database
from models.persona_schemas import PersonaSelection, PersonaChat, PersonaChatResponse, PersonaPublic
from services.persona_service import PersonaService
from core.security import get_current_user_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/personas", tags=["personas"])

# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_persona_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> PersonaService:
    """Get PersonaService instance"""
    service = PersonaService(db)
    await service.initialize_personas()  # Initialize on first use
    return service

# ============================================================================
# PERSONA ENDPOINTS
# ============================================================================

@router.get("", response_model=list[PersonaPublic])
async def get_all_personas(
    user_id: str = Depends(get_current_user_id),
    persona_service: PersonaService = Depends(get_persona_service)
):
    """
    Get all available personas with unlock status
    
    Returns list of personas with:
    - name, description, emoji, color
    - tone_style, speaking_style
    - unlock_condition
    - is_unlocked (user-specific)
    """
    try:
        personas = await persona_service.get_all_personas(user_id)
        
        # Log unlock status for debugging
        for p in personas:
            logger.debug(f"Persona {p.persona_id}: unlocked={p.is_unlocked}, condition='{p.unlock_condition}'")
        
        logger.info(f"✅ Retrieved {len(personas)} personas for user {user_id}")
        return personas
    except Exception as e:
        logger.error(f"Error fetching personas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch personas"
        )

@router.get("/unlocked", response_model=list[PersonaPublic])
async def get_unlocked_personas(
    user_id: str = Depends(get_current_user_id),
    persona_service: PersonaService = Depends(get_persona_service)
):
    """
    Get only unlocked personas for current user
    """
    try:
        personas = await persona_service.get_unlocked_personas(user_id)
        return personas
    except Exception as e:
        logger.error(f"Error fetching unlocked personas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch unlocked personas"
        )

@router.post("/select")
async def select_persona(
    selection: PersonaSelection,
    user_id: str = Depends(get_current_user_id),
    persona_service: PersonaService = Depends(get_persona_service)
):
    """
    Select a persona for the user
    
    Request:
    {
        "persona_id": "einstein" | "marie_curie" | "newton"
    }
    """
    try:
        logger.info(f"Attempting to select persona {selection.persona_id} for user {user_id}")
        success = await persona_service.select_persona(user_id, selection.persona_id)
        
        if not success:
            logger.error(f"Persona selection failed for {selection.persona_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to select persona {selection.persona_id}. Check if persona exists and is unlocked."
            )
        
        logger.info(f"✅ Persona {selection.persona_id} successfully selected for user {user_id}")
        return {
            "success": True,
            "message": f"Persona {selection.persona_id} selected",
            "persona_id": selection.persona_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting persona: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to select persona: {str(e)}"
        )

# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@router.post("/chat", response_model=PersonaChatResponse)
async def chat_with_persona(
    chat_request: PersonaChat,
    user_id: str = Depends(get_current_user_id),
    persona_service: PersonaService = Depends(get_persona_service)
):
    """
    Chat with selected persona
    
    Request:
    {
        "message": "What is photosynthesis?",
        "persona_id": "marie_curie",  # optional, uses selected if not provided
        "conversation_id": "..."  # optional
    }
    
    Response:
    {
        "response": "AI response from persona",
        "persona_name": "Marie Curie",
        "persona_emoji": "🔬",
        "persona_color": "#FF69B4",
        "conversation_id": "..."
    }
    """
    try:
        result = await persona_service.chat_with_persona(
            user_id=user_id,
            message=chat_request.message,
            persona_id=chat_request.persona_id,
            conversation_id=chat_request.conversation_id
        )
        return result
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in chat_with_persona endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get persona response"
        )

@router.get("/chat-history/{persona_id}")
async def get_chat_history(
    persona_id: str,
    user_id: str = Depends(get_current_user_id),
    persona_service: PersonaService = Depends(get_persona_service)
):
    """
    Get chat history with a specific persona
    
    Returns:
    {
        "conversation_id": "...",
        "persona_id": "einstein",
        "persona_name": "Albert Einstein",
        "persona_emoji": "🧪",
        "persona_color": "#FFD700",
        "messages": [
            {
                "sender": "user",
                "content": "What is gravity?",
                "created_at": "2024-01-01T10:00:00"
            },
            ...
        ]
    }
    """
    try:
        history = await persona_service.get_chat_history(user_id, persona_id)
        if not history:
            return {
                "conversation_id": None,
                "persona_id": persona_id,
                "messages": []
            }
        return history
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chat history"
        )

@router.get("/{persona_id}")
async def get_persona_details(
    persona_id: str,
    user_id: str = Depends(get_current_user_id),
    persona_service: PersonaService = Depends(get_persona_service)
):
    """
    Get details of a specific persona
    """
    try:
        personas = await persona_service.get_all_personas(user_id)
        persona = next((p for p in personas if p.persona_id == persona_id), None)
        
        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona {persona_id} not found"
            )
        
        return persona
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching persona details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch persona details"
        )
