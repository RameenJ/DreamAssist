# backend/routers/ai_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.db import get_database
from core.security import get_current_user
from services import ai_service, book_service, ai_mentor_chat_service, activity_service, quiz_service
from models.user_schemas import UserInDB, PyObjectId
from bson import ObjectId
from models.ai_schemas import (
    TextForSummarization,
    SummarizationResponse,
    TextForFlashcards,
    FlashcardsResponse,
    Flashcard,
    FlashcardSetPublic,
    FlashcardPublic,
    TextForStudyNotes,
    StudyNotesResponse,
    TextForQuestionAnswer,
    QuestionAnswerResponse,
    QuizGenerationRequest,
    GeneratedQuiz,
    QuizEvaluationRequest,
    QuizEvaluationResponse,
    ChatRequest,
    ChatResponse,
    AIMentorMessagePublic,
    AIMentorConversationPublic,
    FlashcardSetInDB,
    FlashcardInDB
)
from datetime import datetime, timedelta

# --- Helper functions for persistent quiz storage ---
async def save_quiz_session(db: AsyncIOMotorDatabase, quiz: GeneratedQuiz, user_id: str):
    """Save quiz session to MongoDB with expiry and user_id for access control."""
    quiz_data = quiz.model_dump()
    quiz_data['user_id'] = ObjectId(user_id)  # Add user_id for access control
    quiz_data['created_at'] = datetime.utcnow()
    quiz_data['expires_at'] = datetime.utcnow() + timedelta(hours=2)  # Quiz expires in 2 hours
    await db['quiz_sessions'].insert_one(quiz_data)

async def get_quiz_session(db: AsyncIOMotorDatabase, quiz_id: str, user_id: str) -> Optional[GeneratedQuiz]:
    """Retrieve quiz session from MongoDB with user access verification."""
    quiz_data = await db['quiz_sessions'].find_one(
        {'quiz_id': quiz_id, 'user_id': ObjectId(user_id), 'expires_at': {'$gt': datetime.utcnow()}}
    )
    if not quiz_data:
        return None
    # Remove MongoDB specific fields
    quiz_data.pop('_id', None)
    quiz_data.pop('user_id', None)
    quiz_data.pop('created_at', None)
    quiz_data.pop('expires_at', None)
    return GeneratedQuiz(**quiz_data)

async def delete_quiz_session(db: AsyncIOMotorDatabase, quiz_id: str, user_id: str):
    """Delete quiz session from MongoDB with user verification."""
    await db['quiz_sessions'].delete_one({'quiz_id': quiz_id, 'user_id': ObjectId(user_id)})

router = APIRouter(
    prefix="/ai",
    tags=["AI Features"],
    dependencies=[Depends(get_current_user)]
)

# =========================================================================
# --- NEW ROUTE FOR AI MENTOR CHAT (Module 8) ---
# =========================================================================

@router.post("/chat/{book_id}", response_model=ChatResponse)
async def http_chat_with_book(
    book_id: str,
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Handles a chat query for a specific book using the RAG pipeline.
    """
    # 1. Verify user has access to the book
    book = await book_service.get_book_by_id_for_user(
        db=db, book_id_str=book_id, user_id=current_user.id
    )
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found or you do not have permission to access it."
        )

    # 2. Call the AI service to get the RAG-based answer
    try:
        response = await ai_service.get_rag_answer(
            book_id=book_id, 
            query=request.query, 
            user_id=current_user.id,
            db=db
        )
        
        # 3. Log activity for progress tracking
        await activity_service.log_activity(
            db=db,
            user_id=ObjectId(current_user.id),
            activity_type="chat",
            book_id=ObjectId(book_id)
        )
        
        return response
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"ERROR: API (/ai/chat/{book_id}) - Unexpected error: {type(e).__name__} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your chat request."
        )

# =========================================================================
# --- NEW ROUTES FOR AI MENTOR CHAT HISTORY ---
# =========================================================================

@router.get("/chat/{book_id}/history", response_model=List[AIMentorMessagePublic])
async def get_chat_history(
    book_id: str,
    limit: int = 50,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Retrieves chat history for a specific book.
    This history will be used for future sentiment analysis.
    """
    from bson import ObjectId
    
    # Verify user has access to the book
    book = await book_service.get_book_by_id_for_user(
        db=db, book_id_str=book_id, user_id=current_user.id
    )
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found or you do not have permission to access it."
        )
    
    try:
        # Get messages for this book
        messages = await ai_mentor_chat_service.get_messages_for_book(
            db=db,
            user_id=PyObjectId(str(current_user.id)),
            book_id=PyObjectId(book_id),
            limit=limit
        )
        return messages
    except Exception as e:
        print(f"ERROR: Failed to retrieve chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history."
        )

@router.get("/chat/conversations", response_model=List[AIMentorConversationPublic])
async def get_all_conversations(
    book_id: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Retrieves all AI Mentor conversations for the current user.
    Optionally filtered by book_id.
    """
    from bson import ObjectId
    
    try:
        conversations = await ai_mentor_chat_service.get_user_ai_conversations(
            db=db,
            user_id=PyObjectId(str(current_user.id)),
            book_id=PyObjectId(book_id) if book_id else None
        )
        return conversations
    except Exception as e:
        print(f"ERROR: Failed to retrieve conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations."
        )

# =========================================================================
# --- EXISTING ROUTES (Summarization, Flashcards, Study Notes, Q&A) ---
# =========================================================================

@router.post("/summarize-text", response_model=SummarizationResponse)
async def http_summarize_text(
    request_data: TextForSummarization,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user),
):
    # Now using Gemini API - check is handled in ai_service.generate_summary()
    try:
        summary = await ai_service.generate_summary(request_data.text_to_summarize)
        
        # Log activity for progress tracking
        await activity_service.log_activity(
            db=db,
            user_id=ObjectId(current_user.id),
            activity_type="summarize"
        )
        
        return SummarizationResponse(summary=summary)
    except Exception as e:
        print(f"Error in /summarize-text endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )

@router.post("/generate-flashcards", response_model=FlashcardsResponse)
async def http_generate_flashcards(
    request_data: TextForFlashcards,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user),
):
    try:
        flashcards_list = await ai_service.generate_flashcards_from_text(request_data.text_to_generate_from)
        
        # Extract book_id and topic_id from request if available
        book_id = ObjectId(request_data.book_id) if hasattr(request_data, 'book_id') and request_data.book_id else None
        topic_id = ObjectId(request_data.topic_id) if hasattr(request_data, 'topic_id') and request_data.topic_id else None
        topic_name = request_data.topic_name if hasattr(request_data, 'topic_name') else None
        
        # Create flashcard set document
        from models.ai_schemas import FlashcardSetInDB, FlashcardInDB
        
        user_obj_id = ObjectId(current_user.id)
        flashcard_set = FlashcardSetInDB(
            user_id=PyObjectId(str(user_obj_id)),
            book_id=PyObjectId(str(book_id)) if book_id else PyObjectId(str(user_obj_id)),
            topic_id=PyObjectId(str(topic_id)) if topic_id else None,
            topic_name=topic_name,
            flashcard_count=len(flashcards_list),
            source_text=request_data.text_to_generate_from
        )
        
        # Save flashcard set
        set_doc = flashcard_set.model_dump(by_alias=True, mode='python')
        set_result = await db['flashcard_sets'].insert_one(set_doc)
        flashcard_set_id = set_result.inserted_id
        
        # Save individual flashcards
        flashcard_docs = []
        for card in flashcards_list:
            flashcard = FlashcardInDB(
                user_id=PyObjectId(str(user_obj_id)),
                book_id=PyObjectId(str(book_id)) if book_id else PyObjectId(str(user_obj_id)),
                topic_id=PyObjectId(str(topic_id)) if topic_id else None,
                front=card['front'],
                back=card['back']
            )
            doc = flashcard.model_dump(by_alias=True, mode='python')
            doc['flashcard_set_id'] = flashcard_set_id  # Link to set
            flashcard_docs.append(doc)
        
        if flashcard_docs:
            await db['flashcards'].insert_many(flashcard_docs)
        
        # Log activity for progress tracking
        await activity_service.log_activity(
            db=db,
            user_id=user_obj_id,
            activity_type="flashcards",
            book_id=book_id,
            topic_id=topic_id,
            metadata={"flashcard_count": len(flashcards_list), "set_id": str(flashcard_set_id)}
        )
        
        print(f"INFO: Saved {len(flashcards_list)} flashcards to database for user {user_obj_id}")
        return FlashcardsResponse(flashcards=[Flashcard(**card) for card in flashcards_list])
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"ERROR: /generate-flashcards endpoint - Unexpected error: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating flashcards. Please try again later."
        )

@router.post("/generate-study-notes", response_model=StudyNotesResponse)
async def http_generate_study_notes(
    request_data: TextForStudyNotes,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    (DEPRECATED - use /topic)
    Receives text input and generates structured study notes using the AI service.
    """
    try:
        notes_content = await ai_service.generate_study_notes_from_text(request_data.text_to_generate_notes_from)
        
        # Log activity for progress tracking
        await activity_service.log_activity(
            db=db,
            user_id=ObjectId(current_user.id),
            activity_type="study_notes"
        )
        
        return StudyNotesResponse(study_notes=notes_content)
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"ERROR: /generate-study-notes endpoint - Unexpected error: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating study notes."
            )

# --- (NEW) ENDPOINT FOR TOPIC-BASED NOTES ---

class TopicStudyNotesRequest(BaseModel):
    """Request model for generating notes from a topic ID."""
    topic_id: str

@router.post("/generate-study-notes/topic", response_model=StudyNotesResponse)
async def http_generate_study_notes_from_topic(
    request_data: TopicStudyNotesRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generates study notes from a specific, user-selected topic ID
    by fetching the topic's content from the database.
    """
    try:
        notes_content = await ai_service.generate_study_notes_from_topic(
            db=db,
            topic_id_str=request_data.topic_id,
            user_id=current_user.id
        )
        
        # Log activity for progress tracking
        await activity_service.log_activity(
            db=db,
            user_id=ObjectId(current_user.id),
            activity_type="study_notes",
            topic_id=ObjectId(request_data.topic_id)
        )
        
        return StudyNotesResponse(study_notes=notes_content)
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"ERROR: /generate-study-notes/topic endpoint - Unexpected error: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating study notes from the topic."
        )

# --- END OF NEW CODE ---


@router.post("/generate-qna", response_model=QuestionAnswerResponse)
async def http_generate_question_answers(
    request_data: TextForQuestionAnswer,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Receives text input and generates question and answer pairs.
    """
    try:
        qna_pairs_list = await ai_service.generate_qna_from_text(request_data.text_to_generate_from)
        
        # Log activity for progress tracking
        await activity_service.log_activity(
            db=db,
            user_id=ObjectId(current_user.id),
            activity_type="qna",
            metadata={"qna_count": len(qna_pairs_list)}
        )
        
        return QuestionAnswerResponse(qna_pairs=qna_pairs_list)
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"ERROR: /generate-qna endpoint - Unexpected error: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating questions and answers."
        )

# =========================================================================
# --- ROUTES FOR RETRIEVING SAVED FLASHCARDS ---
# =========================================================================

@router.get("/flashcards/sets/{book_id}", response_model=List[FlashcardSetPublic])
async def get_flashcard_sets(
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Retrieve all flashcard sets for a specific book that belong to the current user.
    """
    try:
        book_id_obj = ObjectId(book_id)
        user_id_obj = ObjectId(current_user.id)
        
        # Get flashcard sets created by this user for this book
        cursor = db['flashcard_sets'].find({
            'user_id': user_id_obj,
            'book_id': book_id_obj
        }).sort('created_at', -1)
        
        sets = []
        async for set_doc in cursor:
            sets.append(FlashcardSetPublic(
                id=str(set_doc['_id']),
                topic_name=set_doc.get('topic_name'),
                flashcard_count=set_doc.get('flashcard_count', 0),
                created_at=set_doc.get('created_at', datetime.utcnow()),
                flashcards=[]
            ))
        
        return sets
    except Exception as e:
        print(f"ERROR: /flashcards/sets/{book_id} - {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve flashcard sets"
        )


@router.get("/flashcards/{set_id}", response_model=List[FlashcardPublic])
async def get_flashcards_from_set(
    set_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Retrieve all flashcards from a specific set (user access verified).
    """
    try:
        set_id_obj = ObjectId(set_id)
        user_id_obj = ObjectId(current_user.id)
        
        # Verify user owns this flashcard set
        set_doc = await db['flashcard_sets'].find_one({
            '_id': set_id_obj,
            'user_id': user_id_obj
        })
        
        if not set_doc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this flashcard set"
            )
        
        # Get flashcards from this set
        cursor = db['flashcards'].find({
            'flashcard_set_id': set_id_obj,
            'user_id': user_id_obj
        }).sort('created_at', 1)
        
        flashcards = []
        async for card_doc in cursor:
            flashcards.append(FlashcardPublic(
                id=str(card_doc['_id']),
                front=card_doc.get('front', ''),
                back=card_doc.get('back', ''),
                created_at=card_doc.get('created_at', datetime.utcnow())
            ))
        
        return flashcards
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"ERROR: /flashcards/{set_id} - {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve flashcards"
        )

# =========================================================================
# --- ROUTES FOR RETRIEVING QUIZ HISTORY ---
# =========================================================================

@router.get("/quiz/history", response_model=List[Dict])
async def get_quiz_history(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Retrieve all quiz results for the current user (allows retaking past quizzes).
    """
    try:
        user_id_obj = ObjectId(current_user.id)
        
        quiz_results = await quiz_service.get_all_quiz_results_for_user(db, user_id_obj)
        
        return quiz_results
    except Exception as e:
        print(f"ERROR: /quiz/history - {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quiz history"
        )


@router.get("/quiz/history/{book_id}", response_model=List[Dict])
async def get_quiz_history_by_book(
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Retrieve quiz results for a specific book (allows retaking for specific book topics).
    """
    try:
        user_id_obj = ObjectId(current_user.id)
        book_id_obj = ObjectId(book_id)
        
        cursor = db['quiz_results'].find({
            'user_id': user_id_obj,
            'book_id': book_id_obj
        }).sort('attempted_at', -1)
        
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["user_id"] = str(doc["user_id"])
            doc["book_id"] = str(doc["book_id"])
            results.append(doc)
        
        return results
    except Exception as e:
        print(f"ERROR: /quiz/history/{book_id} - {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quiz history"
        )

# =========================================================================
# --- ROUTES FOR QUIZ GENERATION AND EVALUATION (Module 4) ---
# =========================================================================

# --- (MODIFIED) This endpoint now requires db and user ---
@router.post("/quiz/generate", response_model=GeneratedQuiz)
async def http_generate_quiz(
    request: QuizGenerationRequest,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Generates the quiz from a topic_id or book_id and stores it temporarily.
    """
    # Validate that at least one ID is provided
    if not request.topic_id and not request.book_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either topic_id or book_id must be provided"
        )
    
    print(f"INFO: API - Received quiz generation request - topic_id: {request.topic_id}, book_id: {request.book_id}")
    try:
        # --- (MODIFIED) Pass db and user_id to the service ---
        generated_quiz = await ai_service.generate_quiz_from_text(
            request=request,
            db=db,
            user_id=current_user.id
        )

        # Save quiz session to MongoDB with user_id
        await save_quiz_session(db, generated_quiz, str(current_user.id))
        
        # Log activity for progress tracking
        book_id_obj = ObjectId(request.book_id) if request.book_id else None
        topic_id_obj = ObjectId(request.topic_id) if request.topic_id else None
        await activity_service.log_activity(
            db=db,
            user_id=ObjectId(current_user.id),
            activity_type="quiz_generate",
            book_id=book_id_obj,
            topic_id=topic_id_obj,
            metadata={"question_count": len(generated_quiz.questions)}
        )

        print(f"INFO: API - Quiz generated and stored with ID: {generated_quiz.quiz_id}")
        return generated_quiz
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"ERROR: API (/ai/quiz/generate) - Unexpected error: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate quiz: {str(e)}")
# --- End of modification ---


    """
    Evaluates the user's attempt and saves the result to the database.
    Also generates AI mentor study recommendations.
    """
    quiz_id = request.quiz_id
    
    # Retrieve quiz session from MongoDB with user access verification
    generated_quiz = await get_quiz_session(db, quiz_id, current_user.id)
    if not generated_quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz session with ID '{quiz_id}' not found or has expired. Please generate a new quiz."
        )

    try:
        evaluation_result = await ai_service.evaluate_quiz_attempt(
            request=request,
            generated_quiz=generated_quiz,
            db=db,
            user_id=current_user.id
        )

        # NEW - Generate AI Mentor study recommendations
        try:
            print(f"INFO: Generating AI Mentor recommendations for topic: {request.topic_name}")
            recommendations = await ai_service.generate_study_recommendations(
                evaluation=evaluation_result,
                topic_name=request.topic_name
            )
            
            # Add recommendations to evaluation result
            if recommendations and recommendations.get("study_recommendations"):
                evaluation_result.study_recommendations = recommendations.get("study_recommendations")
                evaluation_result.weak_topics = recommendations.get("weak_topics", [])
                evaluation_result.strong_topics = recommendations.get("strong_topics", [])
                evaluation_result.next_steps = recommendations.get("next_steps", [])
                print(f"INFO: AI Mentor recommendations added successfully")
                print(f"DEBUG: Recommendations = {evaluation_result.study_recommendations[:100]}...")
            else:
                print(f"WARN: No recommendations generated, providing default feedback")
                # Provide basic feedback even if AI fails
                score_percent = evaluation_result.total_score * 100
                if score_percent >= 80:
                    evaluation_result.study_recommendations = f"Great job on this {request.topic_name} quiz! You demonstrated strong understanding. Keep practicing to maintain this level."
                elif score_percent >= 60:
                    evaluation_result.study_recommendations = f"Good effort on {request.topic_name}. Review the questions you missed and focus on understanding the core concepts better."
                else:
                    evaluation_result.study_recommendations = f"This {request.topic_name} topic needs more attention. Review the material carefully, focusing on the questions you struggled with, and try the quiz again."
                evaluation_result.weak_topics = []
                evaluation_result.strong_topics = []
                evaluation_result.next_steps = ["Review incorrect answers", "Re-read the material", "Try the quiz again"]
                
        except Exception as e:
            print(f"ERROR: Failed to generate AI Mentor recommendations: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            # Provide basic feedback even if AI fails
            score_percent = evaluation_result.total_score * 100
            evaluation_result.study_recommendations = f"You scored {score_percent:.0f}% on this quiz. Review the questions you missed and keep practicing!"
            evaluation_result.weak_topics = []
            evaluation_result.strong_topics = []
            evaluation_result.next_steps = ["Review incorrect answers", "Practice more"]

        # IMPORTANT: Save quiz result to database BEFORE deleting the session
        try:
            book_id_obj = ObjectId(generated_quiz.book_id) if generated_quiz.book_id else None
            await quiz_service.create_quiz_result(
                db=db,
                user_id=ObjectId(current_user.id),
                book_id=book_id_obj,
                topic_name=request.topic_name,
                eval_response=evaluation_result
            )
            print(f"INFO: Quiz result saved to database for user {current_user.id}")
        except Exception as e:
            print(f"ERROR: Failed to save quiz result: {type(e).__name__}: {str(e)}")
            # Don't fail the entire evaluation if result saving fails
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")

        # Clean up quiz session from MongoDB (only if user owns it)
        await delete_quiz_session(db, quiz_id, current_user.id)
        print(f"INFO: API - Quiz ID {quiz_id} evaluated and removed from storage.")

        return evaluation_result
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"ERROR: API (/ai/quiz/evaluate) - Unexpected error: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to evaluate quiz: {str(e)}")