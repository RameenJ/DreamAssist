from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from datetime import datetime

# Import models
from models.user_schemas import PyObjectId
from models.ai_schemas import (
    AIMentorConversationInDB, AIMentorConversationPublic,
    AIMentorMessageInDB, AIMentorMessagePublic
)

# --- Collection Constants ---
AI_MENTOR_CONVERSATIONS_COLLECTION = "ai_mentor_conversations"
AI_MENTOR_MESSAGES_COLLECTION = "ai_mentor_messages"

# --- Service Functions ---

async def get_or_create_ai_conversation(
    db: AsyncIOMotorDatabase, 
    user_id: PyObjectId, 
    book_id: PyObjectId
) -> AIMentorConversationInDB:
    """
    Finds an existing AI Mentor conversation for this user+book, or creates a new one.
    """
    # Look for existing conversation
    conversation_doc = await db[AI_MENTOR_CONVERSATIONS_COLLECTION].find_one({
        "user_id": user_id,
        "book_id": book_id
    })
    
    if conversation_doc:
        return AIMentorConversationInDB(**conversation_doc)  # type: ignore
        
    # No conversation found, create a new one
    new_convo = AIMentorConversationInDB(
        user_id=user_id,  # type: ignore
        book_id=book_id   # type: ignore
    )
    
    # Convert to dict for MongoDB insertion
    doc_to_insert = new_convo.model_dump(by_alias=True, mode='python')
    
    # Ensure ObjectIds are preserved (not converted to strings)
    if "_id" in doc_to_insert and isinstance(doc_to_insert["_id"], str):
        doc_to_insert["_id"] = ObjectId(doc_to_insert["_id"])
    if "user_id" in doc_to_insert and isinstance(doc_to_insert["user_id"], str):
        doc_to_insert["user_id"] = ObjectId(doc_to_insert["user_id"])
    if "book_id" in doc_to_insert and isinstance(doc_to_insert["book_id"], str):
        doc_to_insert["book_id"] = ObjectId(doc_to_insert["book_id"])
    
    result = await db[AI_MENTOR_CONVERSATIONS_COLLECTION].insert_one(doc_to_insert)
    
    created_doc = await db[AI_MENTOR_CONVERSATIONS_COLLECTION].find_one({"_id": result.inserted_id})
    return AIMentorConversationInDB(**created_doc)  # type: ignore

async def save_ai_mentor_message(
    db: AsyncIOMotorDatabase,
    conversation_id: PyObjectId,
    user_id: PyObjectId,
    book_id: PyObjectId,
    sender_type: str,  # "user" or "ai"
    content: str,
    sources: Optional[List[str]] = None
) -> AIMentorMessageInDB:
    """
    Saves a new AI Mentor message (either from user or AI) to the database.
    """
    # DEBUG: Print types and values
    print(f"DEBUG: Saving message - conversation_id type: {type(conversation_id)}, value: {conversation_id}")
    print(f"DEBUG: Searching for conversation with _id: {conversation_id}")
    
    # Verify the conversation exists - use PyObjectId directly
    convo = await db[AI_MENTOR_CONVERSATIONS_COLLECTION].find_one({"_id": conversation_id})
    print(f"DEBUG: Found conversation: {convo is not None}")
    if not convo:
        # Try to find all conversations to see what's actually there
        all_convos = await db[AI_MENTOR_CONVERSATIONS_COLLECTION].find({}).to_list(length=10)
        print(f"DEBUG: Total conversations in DB: {len(all_convos)}")
        if all_convos:
            print(f"DEBUG: First conversation _id type: {type(all_convos[0]['_id'])}, value: {all_convos[0]['_id']}")
        raise HTTPException(status_code=404, detail="AI Mentor conversation not found")
    
    # Create the message
    message_in_db = AIMentorMessageInDB(
        conversation_id=conversation_id,  # type: ignore
        user_id=user_id,  # type: ignore
        book_id=book_id,  # type: ignore
        sender_type=sender_type,  # type: ignore
        content=content,
        sources=sources
    )
    
    # Convert to dict for MongoDB insertion
    doc_to_insert = message_in_db.model_dump(by_alias=True, mode='python')
    
    # Ensure ObjectIds are preserved (not converted to strings)
    if "_id" in doc_to_insert and isinstance(doc_to_insert["_id"], str):
        doc_to_insert["_id"] = ObjectId(doc_to_insert["_id"])
    if "conversation_id" in doc_to_insert and isinstance(doc_to_insert["conversation_id"], str):
        doc_to_insert["conversation_id"] = ObjectId(doc_to_insert["conversation_id"])
    if "user_id" in doc_to_insert and isinstance(doc_to_insert["user_id"], str):
        doc_to_insert["user_id"] = ObjectId(doc_to_insert["user_id"])
    if "book_id" in doc_to_insert and isinstance(doc_to_insert["book_id"], str):
        doc_to_insert["book_id"] = ObjectId(doc_to_insert["book_id"])
    
    # Insert the message
    result = await db[AI_MENTOR_MESSAGES_COLLECTION].insert_one(doc_to_insert)
    
    # Update the conversation's last_activity and message_count
    await db[AI_MENTOR_CONVERSATIONS_COLLECTION].update_one(
        {"_id": conversation_id},
        {
            "$set": {"last_activity": message_in_db.created_at},
            "$inc": {"message_count": 1}
        }
    )
    
    created_doc = await db[AI_MENTOR_MESSAGES_COLLECTION].find_one({"_id": result.inserted_id})
    return AIMentorMessageInDB(**created_doc)  # type: ignore

async def get_ai_conversation_messages(
    db: AsyncIOMotorDatabase,
    conversation_id: PyObjectId,
    user_id: PyObjectId,
    limit: Optional[int] = None
) -> List[AIMentorMessagePublic]:
    """
    Gets all messages for a specific AI Mentor conversation.
    """
    # Verify user owns this conversation
    convo = await db[AI_MENTOR_CONVERSATIONS_COLLECTION].find_one({"_id": conversation_id})
    if not convo or convo["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this conversation")
        
    # Fetch messages
    query = {"conversation_id": conversation_id}
    cursor = db[AI_MENTOR_MESSAGES_COLLECTION].find(query).sort("created_at", 1)  # Oldest first
    
    if limit:
        cursor = cursor.limit(limit)
    
    messages = []
    async for msg_doc in cursor:
        msg = AIMentorMessageInDB(**msg_doc)  # type: ignore
        
        messages.append(
            AIMentorMessagePublic(
                id=str(msg.id),
                conversation_id=str(msg.conversation_id),
                sender_type=msg.sender_type,
                content=msg.content,
                sources=msg.sources,
                created_at=msg.created_at,
                user_emotion=msg.user_emotion,
                sentiment_score=msg.sentiment_score
            )
        )
        
    return messages

async def get_user_ai_conversations(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    book_id: Optional[PyObjectId] = None
) -> List[AIMentorConversationPublic]:
    """
    Gets all AI Mentor conversations for a user, optionally filtered by book.
    """
    query = {"user_id": user_id}
    if book_id:
        query["book_id"] = book_id
    
    convos_cursor = db[AI_MENTOR_CONVERSATIONS_COLLECTION].find(query).sort("last_activity", -1)
    
    convo_list = []
    async for convo_doc in convos_cursor:
        convo = AIMentorConversationInDB(**convo_doc)  # type: ignore
        
        # Get book title (optional - if book service has a function for this)
        book_title = None
        book_doc = await db["books"].find_one({"_id": convo.book_id})
        if book_doc:
            book_title = book_doc.get("title", "Unknown Book")
        
        # Get last message preview
        last_message_doc = await db[AI_MENTOR_MESSAGES_COLLECTION].find_one(
            {"conversation_id": convo.id},
            sort=[("created_at", -1)]
        )
        
        last_message_preview = None
        if last_message_doc:
            content = last_message_doc["content"]
            last_message_preview = content[:100] + "..." if len(content) > 100 else content
        
        convo_list.append(
            AIMentorConversationPublic(
                id=str(convo.id),
                book_id=str(convo.book_id),
                book_title=book_title,
                created_at=convo.created_at,
                last_activity=convo.last_activity,
                message_count=convo.message_count,
                last_message_preview=last_message_preview
            )
        )
        
    return convo_list

async def get_messages_for_book(
    db: AsyncIOMotorDatabase,
    user_id: PyObjectId,
    book_id: PyObjectId,
    limit: Optional[int] = 50
) -> List[AIMentorMessagePublic]:
    """
    Gets recent messages for a specific user+book combination.
    Useful for displaying chat history when user opens AI Mentor for a book.
    """
    # Find the conversation
    convo = await get_or_create_ai_conversation(db, user_id, book_id)
    
    # Get messages
    return await get_ai_conversation_messages(db, convo.id, user_id, limit)
