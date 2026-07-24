# backend/routers/book_router.py

import logging
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Path, Form, BackgroundTasks, Query
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Annotated, Optional
from pydantic import BaseModel
# <<< MODIFIED IMPORT: Added BookTopicPublic >>>
from models.book_schemas import BookPublic, BookSubjectUpdate, BookTopicPublic
from models.user_schemas import UserInDB
from services import book_service, ai_service, quiz_service
from core.db import get_database
from core.security import get_current_user

logger = logging.getLogger(__name__) 

router = APIRouter(
    prefix="/books",
    tags=["Books"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/upload", response_model=BookPublic, status_code=status.HTTP_202_ACCEPTED)
async def api_upload_book(
    background_tasks: BackgroundTasks, 
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    file: UploadFile = File(..., description="The PDF book file to upload"),
    title: Optional[str] = Form(None, description="Optional title for the book"),
    subject_id: Optional[str] = Form(None, description="Optional subject ID for the book"),
    subject: Optional[str] = Form(None, description="Subject of the book (e.g., Mathematics, Physics)")
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided.")
    if not file.content_type == "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only PDF files are allowed.")
    
    try:
        book_db_obj = await book_service.process_and_save_book(
            db=db, 
            file=file, 
            current_user=current_user,
            title_from_user=title,
            subject_id_str=subject_id,
            subject=subject
        )

        background_tasks.add_task(
            book_service.process_book_in_background,
            db=db,
            book_id=book_db_obj.id,
            pdf_path=book_db_obj.file_path_local,
            text_save_path=book_db_obj.extracted_text_path_local or ""
        )

        return BookPublic.from_db_model(book_db_obj)
    
    except HTTPException as e:
        raise e 
    except Exception as e:
        logger.error(f"Unhandled error in /upload endpoint: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during book upload.")

@router.put("/{book_id}/subject", response_model=BookPublic)
async def api_update_book_category(
    book_id: Annotated[str, Path(description="The ID of the book to update")],
    book_subject_update: BookSubjectUpdate,
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    try:
        updated_book_db = await book_service.update_book_category(
            db=db, 
            book_id_str=book_id, 
            new_category_id_str=book_subject_update.subject_id, 
            user_id=current_user.id
        )
        if not updated_book_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found or you do not have permission to update it.")
        return BookPublic.from_db_model(updated_book_db)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error updating subject for book {book_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update book subject.")


@router.get("", response_model=List[BookPublic])
async def api_list_user_books(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    try:
        return await book_service.get_user_books(db=db, user_id=current_user.id)
    except Exception as e:
        logger.error(f"Unhandled error in GET /api/books endpoint: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve books.")

@router.get("/{book_id}", response_model=BookPublic)
async def api_get_book_details(
    book_id: Annotated[str, Path(description="The ID of the book to retrieve")],
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    logger.debug(f"Getting book {book_id} for user_id: {current_user.id} (type: {type(current_user.id)})")
    
    book_db = await book_service.get_book_by_id_for_user(db=db, book_id_str=book_id, user_id=current_user.id)
    if not book_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found or access denied.")
    return BookPublic.from_db_model(book_db)


@router.get("/{book_id}/pdf", response_class=FileResponse)
async def api_serve_book_pdf(
    book_id: Annotated[str, Path(description="The ID of the book PDF to retrieve")],
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    pdf_filepath = await book_service.get_book_pdf_filepath(db=db, book_id_str=book_id, user_id=current_user.id)
    if not pdf_filepath:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF file not found or access denied.")
    
    filename = os.path.basename(pdf_filepath)
    
    return FileResponse(
        path=pdf_filepath, 
        media_type='application/pdf', 
        filename=filename
    )

class BookTextContentResponse(BaseModel):
    id: str
    title: str
    content: str

@router.get("/{book_id}/extracted-text", response_model=BookTextContentResponse)
async def api_get_book_extracted_text(
    book_id: Annotated[str, Path(description="The ID of the book whose extracted text to retrieve")],
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    book_db = await book_service.get_book_by_id_for_user(db=db, book_id_str=book_id, user_id=current_user.id)
    if not book_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found or access denied.")

    extracted_text = await book_service.get_book_extracted_text(db=db, book_id_str=book_id, user_id=current_user.id)
    if extracted_text is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extracted text not found for this book.")
        
    return BookTextContentResponse(
        id=str(book_db.id),
        title=book_db.title,
        content=extracted_text
    )
    
@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_book(
    book_id: Annotated[str, Path(description="The ID of the book to delete")],
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    try:
        success = await book_service.delete_book_for_user(
            db=db, book_id_str=book_id, user_id=current_user.id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Book not found or you do not have permission to delete it."
            )
        return None 
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"/books/{book_id} DELETE endpoint - Unexpected error: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while trying to delete the book."
        )
    
# --- (MODIFIED) ---
# This endpoint now fetches pre-processed topics from the database.
@router.get(
    "/{book_id}/topics",
    response_model=List[BookTopicPublic], 
    summary="Get saved topic titles for a book"
)
async def http_get_book_topics( 
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Retrieves a list of main topic titles (and their IDs) 
    from the database that were extracted from the book's ToC.
    """
    try:
        if not current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not authenticated")

        topics = await book_service.get_topics_for_book(
            db=db, book_id_str=book_id, user_id=current_user.id
        )
        
        if not topics:
            logger.warning(f"No topics found in DB for book {book_id}.")

        return topics
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to get topics for book {book_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve topics from the database.")

@router.get(
    "/{book_id}/topics/{topic_id}/text",
    summary="Get the text content of a specific topic"
)
async def http_get_topic_text(
    book_id: str,
    topic_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Retrieves the full text content of a specific topic for summarization/flashcard generation.
    """
    logger.debug(f"GET TOPIC TEXT REQUEST: book_id={book_id}, topic_id={topic_id}, user={current_user.id if current_user else 'None'}")
    try:
        if not current_user.id:
            logger.error("User not authenticated")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not authenticated")

        logger.debug("Calling get_topic_content_by_id service...")
        content = await book_service.get_topic_content_by_id(
            db=db,
            book_id_str=book_id,
            topic_id_str=topic_id,
            user_id=current_user.id
        )
        
        if content is None:
            logger.error("Topic content is None")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic content not found."
            )
        
        logger.debug(f"Successfully returning content of length {len(content)}")
        return {"content": content}
        
    except HTTPException as he:
        logger.debug(f"HTTPException: {he.status_code} - {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Failed to get topic text for book {book_id}, topic {topic_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve topic content."
        )

# --- NEW SEARCH ENDPOINT ---

class BookSearchResult(BaseModel):
    page_number: int
    snippet: str

@router.get("/{book_id}/search", response_model=List[BookSearchResult])
async def api_search_book_content(
    book_id: Annotated[str, Path(description="The ID of the book")],
    query: Annotated[str, Query(min_length=1, description="Text to search for")],
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    """
    Searches for text within the book PDF and returns matching pages with snippets.
    """
    # Ensure the service function 'search_book_pdf' exists in book_service.py
    results = await book_service.search_book_pdf(
        db=db, 
        book_id_str=book_id, 
        query=query, 
        user_id=current_user.id
    )
    return results

# --- QUIZ RESULTS ENDPOINTS ---

@router.get("/results")
async def api_get_all_quiz_results(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    """
    Retrieves all quiz results for the authenticated user.
    """
    logger.debug(f"Getting book results for user_id: {current_user.id} (type: {type(current_user.id)})")
    
    try:
        results = await quiz_service.get_all_quiz_results_for_user(
            db=db, 
            user_id=current_user.id
        )
        return results
    except Exception as e:
        logger.error(f"Failed to get quiz results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to retrieve quiz results."
        )


@router.get("/results/topics")
async def api_get_quiz_results_by_topic(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
):
    """
    Retrieves quiz results grouped by topic for the authenticated user.
    """
    try:
        results = await quiz_service.get_quiz_results_by_topic(
            db=db, 
            user_id=current_user.id
        )
        return results
    except Exception as e:
        logger.error(f"Failed to get quiz results by topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to retrieve quiz results by topic."
        )
