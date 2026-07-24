# backend/services/book_service.py
# 
# ARCHITECTURE NOTE:
# - AI models (HuggingFace embeddings, transformers) are loaded ONCE at module level
#   in ai_service.py and vector_service.py to avoid expensive re-initialization
# - Background tasks run asynchronously using FastAPI BackgroundTasks, NOT ProcessPoolExecutor
# - This prevents model reloading and CPU saturation while maintaining non-blocking API responses

import os
import uuid
import shutil
import fitz  # PyMuPDF
import logging
from fastapi import UploadFile, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from bson import ObjectId
from models.book_schemas import (
    BookCreateInternal, BookInDB, BookPublic, PyObjectId,
    BookTopicCreate, BookTopicInDB, BookTopicPublic
)
from models.user_schemas import UserInDB
from core.config import LOCAL_BOOK_UPLOAD_DIR, LOCAL_EXTRACTED_TEXT_DIR, LOCAL_VECTOR_STORE_DIR
from . import subject_service
from . import ai_service
from . import vector_service
import re
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure upload directories exist when the service module is loaded
try:
    os.makedirs(LOCAL_BOOK_UPLOAD_DIR, exist_ok=True)
    os.makedirs(LOCAL_EXTRACTED_TEXT_DIR, exist_ok=True)
    os.makedirs(LOCAL_VECTOR_STORE_DIR, exist_ok=True)
    logger.info(f"Directories initialized: {LOCAL_BOOK_UPLOAD_DIR}, {LOCAL_EXTRACTED_TEXT_DIR}, {LOCAL_VECTOR_STORE_DIR}")
except Exception as e:
    logger.error(f"Failed to create directories: {e}")
    raise

# --- COLLECTION NAMES ---
BOOKS_COLLECTION = "books"
BOOK_TOPICS_COLLECTION = "book_topics"
QUIZ_RESULTS_COLLECTION = "quiz_results"

# --- REGEX PATTERNS ---
# Matches: "1. Topic", "1.1. Subtopic", "1 Topic"
TOPIC_START_REGEX = re.compile(r"^\s*(\d+)(\.\d+)?\.?\s+([A-Za-z0-9].+)")
# Cleans junk off the end: "Topic ... 10" -> "Topic"
CLEAN_REGEX = re.compile(r"(.+?)\s*(\.{3,}|\s{2,})\s*\d+\s*$")

# --- JUNK TOPIC FILTER ---
JUNK_TOPIC_KEYWORDS = {
    "summary", "bibliography", "reading list",
    "suggestions for further reading", "references",
    "further reading", "index", "appendix",
    "acknowledgments", "preface", "table of contents",
    "list of figures", "list of tables"
}

# REMOVED: run_vector_creation_in_process
# Vector store creation now runs directly in background tasks to avoid model reloading

async def _extract_and_save_topics(
    db: AsyncIOMotorDatabase,
    book_id: PyObjectId,
    pdf_path: str
) -> None:
    """
    Extracts topics using a 5-step fallback approach:
    1. Try clickable TOC (PDF bookmarks/outline)
    2. Try clickable link TOC on printed pages
    3. Try printed TOC parsing with regex
    4. Fallback to heading detection
    5. Slide-style PDF per-page topics
    
    Filters junk topics and never blocks book processing.
    """
    logger.info(f"Starting topic extraction for book_id: {book_id}")
    doc: Optional[fitz.Document] = None
    
    try:
        doc = fitz.open(pdf_path)
        topics: List[Dict[str, Any]] = []
        
        # --- STEP 1: Try Metadata TOC (PDF Bookmarks) ---
        topics = _get_toc_from_metadata(doc)
        
        if not topics:
            logger.info(f"No metadata TOC found for book_id: {book_id}. Trying clickable link TOC...")
            # --- STEP 2: Try Clickable Links TOC ---
            topics = _get_toc_from_clickable_links(doc)
        
        if not topics:
            logger.info(f"No clickable TOC found for book_id: {book_id}. Trying printed TOC...")
            # --- STEP 3: Try Printed TOC (Regex Parsing) ---
            topics = _get_toc_from_regex(doc)
        
        if not topics:
            logger.info(f"No printed TOC found for book_id: {book_id}. Trying heading detection...")
            # --- STEP 4: Fallback to Heading Detection ---
            topics = _get_topics_from_headings(doc)
        
        if not topics:
            logger.info(f"No headings found for book_id: {book_id}. Checking for slide-style PDF...")
            # --- STEP 5: Slide Mode Detection (Presentation PDFs) ---
            if _detect_slide_mode(doc):
                logger.info(f"Slide-style PDF detected for book_id: {book_id}. Using per-page topics.")
                topics = _get_topics_from_slides(doc)

        if not topics:
            logger.info(f"No topics extracted for book_id: {book_id}. Book will be ready without topics.")
            return

        # --- Sort topics by (page, y_position) for proper ordering ---
        topics.sort(key=lambda t: (t["page_start"], t.get("y_start", 0)))

        logger.info(f"Found {len(topics)} potential topics for book_id: {book_id}")

        # --- Process Topics and Extract Content ---
        topics_to_create: List[BookTopicCreate] = []
        skipped_no_content = 0
        skipped_junk = 0
        
        for i, current_topic in enumerate(topics):
            try:
                next_topic = topics[i + 1] if i + 1 < len(topics) else None
                
                # Detect same-page topics
                if next_topic and next_topic.get("page_start") == current_topic["page_start"]:
                    logger.debug(f"Same-page topics detected: '{current_topic['title'][:40]}' and '{next_topic['title'][:40]}' (page {current_topic['page_start']})")
                
                # Extract content based on topic type
                content_slice, page_start, page_end = _extract_topic_content(
                    doc, current_topic, next_topic
                )
                
                if not content_slice:
                    logger.warning(f"No content found for topic '{current_topic['title']}'. Skipping.")
                    skipped_no_content += 1
                    continue

                # Filter junk topics
                title_lower = current_topic["title"].lower()
                if any(keyword in title_lower for keyword in JUNK_TOPIC_KEYWORDS):
                    logger.info(f"Skipping junk topic: {current_topic['title']}")
                    skipped_junk += 1
                    continue

                # Add valid topic
                topic_data = BookTopicCreate(
                    book_id=book_id,
                    topic_title=current_topic["title"],
                    page_start=page_start,
                    page_end=page_end,
                    content=content_slice
                )
                topics_to_create.append(topic_data)
                
            except Exception as e:
                logger.warning(f"Failed to process topic '{current_topic.get('title', 'UNKNOWN')}' for book_id: {book_id}. Error: {e}")
                continue

        # --- Log filtering summary ---
        logger.info(f"Topic extraction summary for book_id: {book_id}")
        logger.info(f"  - Potential topics found: {len(topics)}")
        logger.info(f"  - Valid topics saved: {len(topics_to_create)}")
        logger.info(f"  - Skipped (no content): {skipped_no_content}")
        logger.info(f"  - Skipped (junk): {skipped_junk}")
        logger.info(f"  - Failed to process: {len(topics) - len(topics_to_create) - skipped_no_content - skipped_junk}")

        # --- Batch insert all valid topics ---
        if topics_to_create:
            try:
                documents = [
                    BookTopicInDB(**t.model_dump()).model_dump(by_alias=True, mode='python')
                    for t in topics_to_create
                ]
                
                # CRITICAL: Ensure _id and book_id are stored as ObjectId, not strings
                for doc_data in documents:
                    # Force _id to be ObjectId (model_dump converts it to string via json_encoders)
                    if "_id" in doc_data:
                        if not isinstance(doc_data["_id"], ObjectId):
                            doc_data["_id"] = ObjectId(doc_data["_id"]) if isinstance(doc_data["_id"], str) else ObjectId()
                    else:
                        doc_data["_id"] = ObjectId()
                    
                    # Ensure book_id remains as ObjectId for proper querying
                    if "book_id" in doc_data:
                        if isinstance(doc_data["book_id"], str):
                            doc_data["book_id"] = ObjectId(doc_data["book_id"])
                        elif not isinstance(doc_data["book_id"], ObjectId):
                            # Convert PyObjectId or other types to ObjectId
                            doc_data["book_id"] = ObjectId(doc_data["book_id"])
                
                logger.info(f"DEBUG: Inserting topics with _id type: {type(documents[0]['_id'])}, book_id type: {type(documents[0]['book_id']) if documents else 'N/A'}")
                await db[BOOK_TOPICS_COLLECTION].insert_many(documents)
                logger.info(f"Successfully saved {len(topics_to_create)} topics for book_id: {book_id}")
            except Exception as e:
                logger.error(f"Failed to save topics to database for book_id: {book_id}. Error: {e}")
        else:
            logger.info(f"No valid topics with content found for book_id: {book_id}")

    except Exception as e:
        logger.error(f"Topic extraction failed for book_id: {book_id}. Error: {type(e).__name__} - {str(e)}")
    finally:
        if doc:
            doc.close()


def _extract_topic_content(
    doc: fitz.Document,
    current_topic: Dict[str, Any],
    next_topic: Optional[Dict[str, Any]]
) -> Tuple[str, int, int]:
    """
    Extracts content using INTELLIGENT BOUNDARY DETECTION.
    
    Strategy:
    1. If same page with Y-coords: Use Y-coordinate clipping
    2. Otherwise: Search for next topic's title to find actual boundary
    3. Fall back to smart page-range heuristics if search fails
    4. Prioritize accuracy over arbitrary page boundaries
    
    Returns: (content, page_start, page_end)
    """
    try:
        current_page = current_topic["page_start"]
        current_y = current_topic.get("y_start")
        
        # Determine where this topic ends
        if next_topic:
            next_page = next_topic["page_start"]
            next_y = next_topic.get("y_start")
        else:
            # Last topic: extract to end of document
            next_page = doc.page_count + 1
            next_y = None
        
        # CASE 1: Same-page topics with Y-coordinates (precise slicing)
        if current_page == next_page and current_y is not None and next_y is not None:
            logger.debug(f"Same-page extraction: page {current_page}, Y {current_y}->{next_y}")
            return _extract_same_page_content(doc, current_page, current_y, next_y)
        
        # CASE 2: Search for actual boundary using next topic's title
        if next_topic:
            actual_end_page = _find_topic_boundary(
                doc, 
                next_topic["title"], 
                start_search_page=current_page,
                hint_page=next_page
            )
            
            if actual_end_page:
                # Found the actual boundary - extract up to but not including that page
                end_page = actual_end_page - 1
                logger.debug(f"Title-based boundary found: topic ends at page {end_page}")
            else:
                # Title search failed - use intelligent fallback
                end_page = _estimate_topic_end_page(current_page, next_page, doc.page_count)
                logger.debug(f"Using fallback estimation: pages {current_page}-{end_page}")
        else:
            # Last topic - extract to end of book
            end_page = doc.page_count
        
        logger.debug(f"Page-range extraction: pages {current_page}-{end_page}")
        return _extract_page_range_content(doc, current_page, end_page, current_y)
    
    except Exception as e:
        logger.error(f"Topic extraction failed for '{current_topic.get('title', 'UNKNOWN')}': {e}")
        return "", current_topic["page_start"], current_topic["page_start"]


def _find_topic_boundary(
    doc: fitz.Document,
    next_topic_title: str,
    start_search_page: int,
    hint_page: int,
    max_search_range: int = 30
) -> Optional[int]:
    """
    Searches forward from start_search_page to find where next_topic_title actually appears.
    Uses the hint_page as a starting point but searches nearby pages.
    
    Returns: 1-based page number where the title is found, or None if not found
    """
    try:
        # Clean the title for searching - remove numbering
        clean_title = re.sub(r"^\s*(\d+(\.\d+)?)\.?\s+", "", next_topic_title).strip()
        
        # Normalize for flexible matching
        clean_title_lower = clean_title.lower()
        
        # If title is too short, skip search (too many false positives)
        if len(clean_title) < 4:
            return None
        
        # Search window: prioritize hint_page but look ±15 pages around it
        search_start = max(start_search_page, hint_page - 5)
        search_end = min(doc.page_count, hint_page + max_search_range)
        
        logger.debug(f"Searching for title '{clean_title[:40]}' in pages {search_start}-{search_end}")
        
        # Search pages in order of likelihood: hint_page first, then expand outward
        pages_to_check = [hint_page]
        for offset in range(1, max_search_range):
            if hint_page + offset <= search_end:
                pages_to_check.append(hint_page + offset)
            if hint_page - offset >= search_start:
                pages_to_check.append(hint_page - offset)
        
        for page_num in pages_to_check:
            if page_num < start_search_page or page_num > doc.page_count:
                continue
            
            try:
                page_idx = page_num - 1
                page = doc.load_page(page_idx)
                page_text = page.get_text("text")  # type: ignore
                
                # Check if title appears at the start of the page (strong signal)
                first_lines = "\n".join(page_text.split("\n")[:5]).lower()
                
                if clean_title_lower in first_lines:
                    logger.info(f"Found topic boundary: '{clean_title[:40]}' on page {page_num}")
                    return page_num
                
                # Also check full page text (weaker signal, but useful)
                if clean_title_lower in page_text.lower():
                    # Verify it's near the top of the page (not mid-content)
                    title_position = page_text.lower().index(clean_title_lower)
                    if title_position < len(page_text) * 0.2:  # Top 20% of page
                        logger.info(f"Found topic boundary: '{clean_title[:40]}' on page {page_num}")
                        return page_num
                
            except Exception as e:
                logger.debug(f"Error checking page {page_num}: {e}")
                continue
        
        logger.debug(f"Could not find title '{clean_title[:40]}' in search range")
        return None
    
    except Exception as e:
        logger.warning(f"Title boundary search failed: {e}")
        return None


def _estimate_topic_end_page(
    current_page: int,
    next_topic_toc_page: int,
    total_pages: int
) -> int:
    """
    Provides intelligent fallback estimation when title search fails.
    
    Heuristics:
    - If topics are far apart (5+ pages): trust TOC, extract up to next_page - 1
    - If topics are close (1-4 pages): assume TOC points to chapter starts, extend range
    - If topics are consecutive (1 page apart): extend by several pages for content
    
    Returns: Estimated end page (1-based)
    """
    page_gap = next_topic_toc_page - current_page
    
    if page_gap >= 5:
        # Topics far apart - TOC is likely accurate
        return next_topic_toc_page - 1
    
    elif page_gap == 1:
        # Consecutive pages - likely chapter markers, extend significantly
        # Assume average chapter is ~8 pages
        estimated_end = current_page + 8
        # But don't go past TOC's next topic + some margin
        safe_end = min(estimated_end, next_topic_toc_page + 10)
        return min(safe_end, total_pages)
    
    elif page_gap <= 4:
        # Close topics - extend moderately (assume 5 page average)
        estimated_end = current_page + 5
        safe_end = min(estimated_end, next_topic_toc_page + 3)
        return min(safe_end, total_pages)
    
    else:
        # Default: trust TOC
        return next_topic_toc_page - 1


def _extract_same_page_content(
    doc: fitz.Document,
    page_num: int,
    start_y: float,
    end_y: float
) -> Tuple[str, int, int]:
    """
    Extracts content from a single page using Y-coordinate clipping.
    This is used when multiple topics are on the same page.
    """
    try:
        page_idx = page_num - 1  # Convert to 0-based index
        page = doc.load_page(page_idx)
        page_rect = page.rect  # type: ignore
        
        # Create clipping rectangle from start_y to end_y
        clip_rect = fitz.Rect(
            0,                  # Left edge
            start_y,            # Top (start of topic)
            page_rect.width,    # Right edge
            end_y               # Bottom (start of next topic)
        )
        
        content = page.get_text("text", clip=clip_rect, sort=True).strip()  # type: ignore
        
        if content:
            logger.debug(f"Same-page Y-slicing successful: page {page_num}, Y {start_y:.1f}->{end_y:.1f}")
            return content, page_num, page_num
        else:
            logger.warning(f"Same-page Y-slicing returned empty content on page {page_num}")
            # Fallback: extract full page (better than nothing)
            return _extract_page_range_content(doc, page_num, page_num, None)
    
    except Exception as e:
        logger.warning(f"Same-page Y-slicing failed on page {page_num}: {e}. Falling back to full page.")
        return _extract_page_range_content(doc, page_num, page_num, None)


def _extract_page_range_content(
    doc: fitz.Document,
    start_page: int,
    end_page: int,
    start_y: Optional[float] = None
) -> Tuple[str, int, int]:
    """
    Extracts content from a page range (inclusive).
    
    Args:
        doc: PyMuPDF document
        start_page: Starting page number (1-based)
        end_page: Ending page number (1-based, inclusive)
        start_y: Optional Y-coordinate to start from on first page
    
    Returns: (content, page_start, page_end)
    """
    try:
        # Validate and clamp page range
        start_page = max(1, min(start_page, doc.page_count))
        end_page = max(start_page, min(end_page, doc.page_count))
        
        content_parts: List[str] = []
        
        for page_num in range(start_page, end_page + 1):
            try:
                page_idx = page_num - 1  # Convert to 0-based
                page = doc.load_page(page_idx)
                page_rect = page.rect  # type: ignore
                
                # Special handling for first page with Y-coordinate
                if page_num == start_page and start_y is not None:
                    # Start from Y-coordinate on first page
                    clip_rect = fitz.Rect(
                        0,
                        start_y,
                        page_rect.width,
                        page_rect.height
                    )
                    page_text = page.get_text("text", clip=clip_rect, sort=True)  # type: ignore
                    logger.debug(f"First page with Y-start: page {page_num}, Y {start_y:.1f}")
                else:
                    # Extract full page
                    page_text = page.get_text("text", sort=True)  # type: ignore
                
                if page_text.strip():
                    content_parts.append(page_text)
            
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num}: {e}")
                continue
        
        # Join all page content with double newlines for readability
        content = "\n\n".join(content_parts).strip()
        
        if not content:
            logger.warning(f"Page range extraction returned empty content: pages {start_page}-{end_page}")
        
        return content, start_page, end_page
    
    except Exception as e:
        logger.error(f"Page range extraction failed for pages {start_page}-{end_page}: {e}")
        return "", start_page, end_page

# --- Helper 1: Get TOC from PDF Metadata ---

def _get_toc_from_metadata(doc: fitz.Document) -> List[Dict[str, Any]]:
    """
    Extracts TOC from PDF metadata (bookmarks/outline).
    Filters to only include numbered topics (e.g., "1. Topic" or "1.1 Subtopic").
    """
    try:
        raw_toc = doc.get_toc()  # type: ignore
        if not raw_toc:
            return []

        topics: List[Dict[str, Any]] = []
        for level, title, page_start in raw_toc:
            # Filter by level (main topic or one sub-level)
            if level > 2:
                continue
            
            cleaned_title = title.strip()
            if not cleaned_title:
                continue

            # Filter by number pattern (e.g., "1. Topic" or "1 Topic")
            match = TOPIC_START_REGEX.match(cleaned_title)
            
            if match:
                topics.append({
                    "title": cleaned_title,
                    "page_start": page_start
                })
        
        logger.info(f"Extracted {len(topics)} topics from PDF metadata TOC")
        return topics
    
    except Exception as e:
        logger.warning(f"Failed to extract metadata TOC: {e}")
        return []

# --- Helper 2: Get TOC from Clickable Links ---

def _get_toc_from_clickable_links(doc: fitz.Document) -> List[Dict[str, Any]]:
    """
    Extracts topics from clickable links on a printed 'Contents' page.
    Works for PDFs where the TOC is clickable but not in metadata.
    Detects and corrects page number offsets (printed vs PDF pages).
    """
    topics: List[Dict[str, Any]] = []
    toc_pages_found = []
    
    try:
        for page_num in range(min(doc.page_count, 20)):  # TOC usually in first 20 pages
            try:
                page = doc.load_page(page_num)
                text = page.get_text().lower()  # type: ignore

                if "contents" not in text and "table of contents" not in text:
                    continue

                links = page.get_links()  # type: ignore
                if not links:
                    continue

                page_topics = []
                for link in links:
                    try:
                        # Extract target page and Y-coordinate
                        target_page: Optional[int] = None
                        y_position: Optional[float] = None
                        
                        if "page" in link:
                            target_page = int(link["page"]) + 1  # 0-based → 1-based
                            
                            # Capture Y-coordinate for same-page slicing
                            if "to" in link:
                                to_dest = link["to"]
                                if hasattr(to_dest, "y"):
                                    y_position = float(to_dest.y)
                                elif isinstance(to_dest, dict) and "y" in to_dest:
                                    y_position = float(to_dest["y"])
                        
                        elif "to" in link and isinstance(link.get("to"), dict):
                            to_dict = link["to"]
                            if "page" in to_dict:
                                target_page = int(to_dict["page"]) + 1
                                if "y" in to_dict:
                                    y_position = float(to_dict["y"])
                        
                        if not target_page:
                            continue

                        # Extract text from clickable area
                        rect = link.get("from")
                        if not rect:
                            continue

                        title = page.get_textbox(rect).strip()  # type: ignore
                        if not title:
                            continue

                        # Clean whitespace and newlines
                        title = re.sub(r"\s+", " ", title)
                        
                        # Remove page numbers from the end
                        title = re.sub(r"[\.\s]+((\d+)|([ivxlcdm]+))[\s\.]*$", "", title, flags=re.IGNORECASE).strip()
                        
                        # Filter out malformed entries
                        if re.search(r"\d+\.\d+.*\d+\s+\d+\.\d+", title):
                            continue

                        # Ignore too short or too long titles
                        if len(title) < 3 or len(title) > 120:
                            continue

                        page_topics.append({
                            "title": title,
                            "page_start": target_page,
                            "y_start": y_position
                        })
                        
                    except (KeyError, TypeError, ValueError) as e:
                        logger.debug(f"Skipping malformed link: {e}")
                        continue

                if page_topics:
                    topics.extend(page_topics)
                    toc_pages_found.append(page_num + 1)
                    logger.info(f"Found {len(page_topics)} clickable links on page {page_num + 1}")
                    
            except Exception as e:
                logger.debug(f"Error processing page {page_num} for clickable TOC: {e}")
                continue
        
        # Apply page offset correction once after collecting all topics
        if topics:
            logger.info(f"Total clickable links found: {len(topics)} across pages {toc_pages_found}")
            _apply_page_offset_correction(doc, topics)
    
    except Exception as e:
        logger.warning(f"Failed to extract clickable TOC: {e}")
    
    return topics


def _apply_page_offset_correction(doc: fitz.Document, topics: List[Dict[str, Any]]) -> None:
    """
    Detects and corrects page number offsets between printed and PDF page numbers.
    Modifies topics list in-place.
    """
    try:
        # Find first numbered chapter/section
        first_chapter_link: Optional[Dict[str, Any]] = None
        for topic in topics:
            if re.match(r"^(\d+\.?\d*|Chapter\s+\d+)", topic["title"], re.IGNORECASE):
                first_chapter_link = topic
                break
        
        if first_chapter_link:
            claimed_page = first_chapter_link["page_start"]
            actual_page = _find_page_by_title(doc, first_chapter_link["title"], claimed_page)
            
            if actual_page and abs(actual_page - claimed_page) > 2:
                offset = actual_page - claimed_page
                logger.info(f"Detected page offset: {offset} (printed page {claimed_page} is PDF page {actual_page})")
                
                # Apply offset to all topics
                for topic in topics:
                    topic["page_start"] = max(1, topic["page_start"] + offset)
                
                logger.info(f"Adjusted all page numbers by offset {offset}")
    
    except Exception as e:
        logger.debug(f"Page offset correction failed: {e}")

# --- Helper: Find Actual Page by Title ---

def _find_page_by_title(doc: fitz.Document, title: str, hint_page: int, search_range: int = 10) -> Optional[int]:
    """
    Searches for a topic title near the hinted page to find its actual location.
    This helps detect page number offsets (printed vs PDF pages).
    """
    try:
        # Create clean version of title for searching
        clean_title = re.sub(r"^\s*(\d+(\.\d+)?)\.?\s+", "", title).strip()
        
        # Search window: hint_page ± search_range
        start_page = max(0, hint_page - search_range - 1)
        end_page = min(doc.page_count, hint_page + search_range)
        
        for page_idx in range(start_page, end_page):
            try:
                page = doc.load_page(page_idx)
                text = page.get_text()  # type: ignore
                
                # Check if title appears on this page
                if clean_title in text or title in text:
                    return page_idx + 1  # Return 1-based page number
                    
            except Exception as e:
                logger.debug(f"Error searching page {page_idx}: {e}")
                continue
        
    except Exception as e:
        logger.debug(f"Failed to find page by title '{title}': {e}")
    
    return None

# --- Helper 3: Get TOC using Regex Fallback ---

def _get_toc_from_regex(doc: fitz.Document) -> List[Dict[str, Any]]:
    """
    Manually scans the first 20 pages for lines matching topic patterns.
    Extracts actual page numbers from the printed TOC.
    """
    topics: List[Dict[str, Any]] = []
    found_toc_page = False
    
    try:
        # Only scan the first 20 pages (common for TOC)
        for page_num in range(min(doc.page_count, 20)):
            try:
                page = doc.load_page(page_num)
                text = page.get_text()  # type: ignore
                
                # Look for the start of the TOC
                if not found_toc_page:
                    text_lower = text.lower()
                    if "contents" in text_lower or "table of contents" in text_lower:
                        found_toc_page = True

                if not found_toc_page:
                    continue

                for line in text.split('\n'):
                    line = line.strip()
                    match = TOPIC_START_REGEX.match(line)
                    
                    if match:
                        main_num = match.group(1)
                        sub_num = match.group(2) or ""
                        title_text = match.group(3)

                        # Clean off dots and page numbers from the title
                        clean_match = CLEAN_REGEX.match(title_text)
                        if clean_match:
                            title_text = clean_match.group(1).strip()
                        
                        # Extract actual page number from the end of the line
                        page_match = re.search(r"(\d+)\s*$", line)
                        actual_page = int(page_match.group(1)) if page_match else page_num + 1
                        
                        # Rebuild clean title
                        full_title = f"{main_num}{sub_num} {title_text}"
                        topics.append({
                            "title": full_title,
                            "page_start": actual_page
                        })

                # If we found the TOC and see a chapter, we're probably done
                if found_toc_page:
                    text_lower = text.lower()
                    if "chapter 1" in text_lower or any(topics):
                        break
            
            except Exception as e:
                logger.debug(f"Error processing page {page_num} for regex TOC: {e}")
                continue
        
        if topics:
            logger.info(f"Extracted {len(topics)} topics using regex from printed TOC")
        
        return topics
    
    except Exception as e:
        logger.warning(f"Failed to extract regex TOC: {e}")
        return []

# --- Helper 4: Get Topics from Heading Detection ---

def _get_topics_from_headings(doc: fitz.Document) -> List[Dict[str, Any]]:
    """
    Fallback: Scans the entire book for potential headings based on:
    - Font size (larger than surrounding text)
    - Bold text
    - Lines that look like chapter/section headings
    
    Used for books with no TOC.
    """
    topics: List[Dict[str, Any]] = []
    seen_titles: set = set()
    
    # Common heading patterns
    HEADING_PATTERNS = [
        re.compile(r"^(Chapter|CHAPTER)\s+(\d+|[IVX]+)[:\s]\s*(.+)", re.IGNORECASE),
        re.compile(r"^(Section|SECTION)\s+(\d+)[:\s]\s*(.+)", re.IGNORECASE),
        re.compile(r"^(\d+)[.:]\s+([A-Z][A-Za-z\s]+)$"),
        re.compile(r"^([A-Z][A-Z\s]{3,})$")  # All caps, 4+ chars
    ]
    
    logger.info(f"Scanning for headings across {doc.page_count} pages...")
    
    try:
        for page_num in range(doc.page_count):
            try:
                page = doc.load_page(page_num)
                
                # Get text with formatting info
                blocks = page.get_text("dict")["blocks"]  # type: ignore
                
                for block in blocks:
                    if block.get("type") != 0:  # type 0 = text block
                        continue
                        
                    for line in block.get("lines", []):
                        line_text = ""
                        max_font_size = 0
                        is_bold = False
                        
                        # Analyze each span (text with same formatting)
                        for span in line.get("spans", []):
                            span_text = span.get("text", "").strip()
                            font_size = span.get("size", 0)
                            font_name = span.get("font", "").lower()
                            
                            if span_text:
                                line_text += span_text + " "
                                max_font_size = max(max_font_size, font_size)
                                if "bold" in font_name:
                                    is_bold = True
                        
                        line_text = line_text.strip()
                        
                        # Skip invalid lines
                        if not line_text or len(line_text) < 3 or len(line_text) > 100:
                            continue
                        
                        # Check if line matches heading patterns
                        is_heading = False
                        heading_title = line_text
                        
                        for pattern in HEADING_PATTERNS:
                            match = pattern.match(line_text)
                            if match:
                                is_heading = True
                                if len(match.groups()) >= 3:
                                    heading_title = f"{match.group(1)} {match.group(2)}: {match.group(3)}"
                                break
                        
                        # Font size check (headings typically 14pt+)
                        if max_font_size >= 14 and len(line_text.split()) <= 10:
                            is_heading = True
                        
                        # Bold AND all caps check
                        if is_bold and line_text.isupper() and 4 <= len(line_text) <= 50:
                            is_heading = True
                        
                        # Add valid, unique heading
                        if is_heading and heading_title not in seen_titles:
                            topics.append({
                                "title": heading_title,
                                "page_start": page_num + 1
                            })
                            seen_titles.add(heading_title)
                            
                            # Limit to avoid too much junk
                            if len(topics) >= 500:
                                logger.info("Heading detection limit reached (500 topics)")
                                return topics
            
            except Exception as e:
                logger.debug(f"Error processing page {page_num} for heading detection: {e}")
                continue
        
        logger.info(f"Heading detection found {len(topics)} potential topics")
        return topics
    
    except Exception as e:
        logger.warning(f"Heading detection failed: {e}")
        return []

# --- Helper 5: Detect Slide-Style PDFs ---

def _detect_slide_mode(doc: fitz.Document) -> bool:
    """
    Detects if a PDF is a presentation/slide deck based on:
    - Low average word count per page
    - Presence of bullet points
    - No structured TOC
    """
    try:
        sample_size = min(20, doc.page_count)
        total_words = 0
        bullet_count = 0
        
        BULLET_CHARS = {'•', '●', '◦', '▪', '▫', '■', '□', '·', '-', '→', '⇒', '➔'}
        
        for page_num in range(sample_size):
            try:
                page = doc.load_page(page_num)
                text = page.get_text()  # type: ignore
                
                if not text:
                    continue
                
                # Count words
                words = text.split()
                total_words += len(words)
                
                # Count bullet points
                for char in text:
                    if char in BULLET_CHARS:
                        bullet_count += 1
            
            except Exception as e:
                logger.debug(f"Error processing page {page_num} for slide detection: {e}")
                continue
        
        if sample_size == 0:
            return False
        
        avg_words_per_page = total_words / sample_size
        avg_bullets_per_page = bullet_count / sample_size
        
        # Criteria: < 200 words per page AND at least 2 bullets per page
        is_slide_mode = avg_words_per_page < 200 and avg_bullets_per_page >= 2
        
        if is_slide_mode:
            logger.info(f"Slide mode detected - Avg words/page: {avg_words_per_page:.1f}, Bullets/page: {avg_bullets_per_page:.1f}")
        
        return is_slide_mode
    
    except Exception as e:
        logger.warning(f"Slide detection failed: {e}")
        return False


# --- Helper 6: Get Topics from Slides (Per-Page) ---

def _get_topics_from_slides(doc: fitz.Document) -> List[Dict[str, Any]]:
    """
    Treats each page as a separate topic for slide-style PDFs.
    Extracts the first meaningful line as the topic title.
    """
    topics: List[Dict[str, Any]] = []
    
    try:
        for page_num in range(doc.page_count):
            try:
                page = doc.load_page(page_num)
                text = page.get_text()  # type: ignore
                
                if not text or len(text.strip()) < 5:
                    continue
                
                # Extract the first non-empty line as the title
                lines = text.split('\n')
                title: Optional[str] = None
                
                for line in lines:
                    clean_line = line.strip()
                    # Skip very short lines, page numbers, bullets
                    if len(clean_line) < 3 or clean_line.isdigit():
                        continue
                    if clean_line and clean_line[0] in {'•', '●', '◦', '▪', '▫', '■', '□', '·', '-'}:
                        continue
                    
                    title = clean_line
                    break
                
                # Fallback if no good title found
                if not title:
                    title = f"Slide {page_num + 1}"
                
                # Truncate long titles
                if len(title) > 80:
                    title = title[:77] + "..."
                
                topics.append({
                    "title": title,
                    "page_start": page_num + 1,
                    "y_start": 0  # Start from top of page
                })
            
            except Exception as e:
                logger.debug(f"Error processing page {page_num} as slide: {e}")
                continue
        
        logger.info(f"Created {len(topics)} page-based topics for slide-style PDF")
        return topics
    
    except Exception as e:
        logger.warning(f"Failed to extract slide topics: {e}")
        return []

# --- Background Processing Functions ---

async def process_book_in_background(
    db: AsyncIOMotorDatabase,
    book_id: PyObjectId,
    pdf_path: str,
    text_save_path: str
) -> None:
    """
    Background processing: extracts text, creates vector store,
    and updates book status.
    """
    logger.info(f"Starting background processing for book_id: {book_id}")
    chatbot_text_parts: List[str] = []
    
    MIN_WORDS_PER_PAGE = 75
    doc: Optional[fitz.Document] = None

    try:
        # Extract and save topics (non-blocking)
        try:
            await _extract_and_save_topics(db, book_id, pdf_path)
        except Exception as topic_error:
            logger.warning(f"Topic extraction failed for book_id: {book_id}. Error: {topic_error}")
            logger.info("Continuing with book processing. Book will be ready without topics.")

        # Extract text
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                try:
                    page = doc.load_page(page_num)
                    text = page.get_text()  # type: ignore
                    
                    word_count = len(text.split())
                    if word_count < MIN_WORDS_PER_PAGE:
                        continue

                    chatbot_text_parts.append(text)
                
                except Exception as page_error:
                    logger.warning(f"Failed to process page {page_num + 1}: {page_error}")
                    continue
            
            doc.close()
            doc = None
        
        except Exception as extract_error:
            logger.error(f"Text extraction failed for book_id: {book_id}. Error: {extract_error}")
            raise

        # Save extracted text
        try:
            full_chatbot_text = "\n\n".join(chatbot_text_parts)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(text_save_path), exist_ok=True)
            
            with open(text_save_path, "w", encoding="utf-8") as text_f:
                text_f.write(full_chatbot_text)
            
            logger.info(f"Saved extracted text to {text_save_path}")
        except Exception as save_error:
            logger.error(f"Failed to save extracted text for book_id: {book_id}. Error: {save_error}")
            raise
        
        # Create vector store directly (models already loaded globally)
        if full_chatbot_text.strip():
            try:
                logger.info(f"Starting vector store creation for book_id: {book_id}")
                
                vector_creation_success = await vector_service.create_vector_store_for_book(
                    str(book_id),
                    full_chatbot_text
                )
                
                if vector_creation_success:
                    logger.info(f"Vector store created successfully for book_id: {book_id}")
                else:
                    logger.warning(f"Vector store creation failed for book_id: {book_id}. AI Mentor will not work.")
            
            except Exception as vector_error:
                logger.error(f"Vector store creation error for book_id: {book_id}. Error: {vector_error}")
        else:
            logger.warning(f"Skipping vector store creation for book_id: {book_id} due to empty text content")

        # Update book status to 'ready'
        try:
            await db[BOOKS_COLLECTION].update_one(
                {"_id": book_id},
                {"$set": {"status": "completed"}}
            )
            logger.info(f"Successfully finished background processing for book_id: {book_id}")
        except Exception as update_error:
            logger.error(f"Failed to update book status for book_id: {book_id}. Error: {update_error}")
            raise

    except Exception as e:
        logger.error(f"Background processing failed for book_id: {book_id}. Error: {type(e).__name__} - {str(e)}")
        try:
            await db[BOOKS_COLLECTION].update_one(
                {"_id": book_id},
                {"$set": {"status": "failed"}}
            )
        except Exception as status_error:
            logger.error(f"Failed to update book status to 'failed': {status_error}")
    
    finally:
        if doc:
            doc.close()


async def process_and_save_book(
    db: AsyncIOMotorDatabase,
    file: UploadFile,
    current_user: UserInDB,
    title_from_user: Optional[str] = None,
    subject_id_str: Optional[str] = None,
    subject: Optional[str] = None
) -> BookInDB:
    """
    Saves uploaded PDF book to database and starts background processing.
    """
    if not current_user.id or not isinstance(current_user.id, ObjectId):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User ID is invalid or not available for book association."
        )
    
    # Validate and get subject if provided
    subject_oid: Optional[PyObjectId] = None
    if subject_id_str:
        try:
            subject_obj = await subject_service.get_subject_by_id_for_user(
                db, subject_id_str, current_user.id
            )
            if not subject_obj:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Subject ID '{subject_id_str}' not found or does not belong to user."
                )
            subject_oid = subject_obj.id
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except Exception as e:
            logger.error(f"Error validating subject: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Subject ID format: {subject_id_str}"
            )

    # Sanitize filename and validate file type
    user_id_for_path = str(current_user.id)
    original_filename_sanitized = "".join(
        c if c.isalnum() or c in ['.', '_', '-'] else '_'
        for c in (file.filename or "unknown_file")
    )
    file_extension = os.path.splitext(original_filename_sanitized)[1]
    
    if not file_extension.lower() == ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF is allowed."
        )

    # Generate unique filenames
    unique_filename_stem = f"{user_id_for_path}_{uuid.uuid4()}"
    stored_pdf_filename = f"{unique_filename_stem}{file_extension}"
    pdf_save_path = os.path.join(LOCAL_BOOK_UPLOAD_DIR, stored_pdf_filename)
    stored_text_filename = f"{unique_filename_stem}.txt"
    text_save_path = os.path.join(LOCAL_EXTRACTED_TEXT_DIR, stored_text_filename)
    
    # Save PDF file
    try:
        # Ensure directory exists
        os.makedirs(LOCAL_BOOK_UPLOAD_DIR, exist_ok=True)
        
        with open(pdf_save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size_bytes = os.path.getsize(pdf_save_path)
        logger.info(f"Saved PDF file: {pdf_save_path} ({file_size_bytes} bytes)")
    
    except Exception as e:
        logger.error(f"Failed to save PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save PDF: {str(e)}"
        )
    finally:
        await file.close()

    # Create book document for database
    try:
        book_meta = BookCreateInternal(
            title=title_from_user or file.filename or "Untitled Book",
            original_filename=file.filename,
            content_type=file.content_type,
            file_size_bytes=file_size_bytes,
            user_id=current_user.id,
            stored_filename=stored_pdf_filename,
            file_path_local=pdf_save_path,
            extracted_text_path_local=text_save_path,
            category_id=subject_oid,
            subject=subject
        )
        
        book_doc_for_db = BookInDB(**book_meta.model_dump()).model_dump(by_alias=True, mode='python')
        
        # Ensure _id is set as ObjectId
        if "_id" not in book_doc_for_db:
            book_doc_for_db["_id"] = ObjectId()
        
        # CRITICAL: Pydantic's json_encoders converts ObjectId to string during model_dump()
        # We must convert critical fields BACK to ObjectId for MongoDB
        if "_id" in book_doc_for_db and isinstance(book_doc_for_db["_id"], str):
            book_doc_for_db["_id"] = ObjectId(book_doc_for_db["_id"])
        if "user_id" in book_doc_for_db and isinstance(book_doc_for_db["user_id"], str):
            book_doc_for_db["user_id"] = ObjectId(book_doc_for_db["user_id"])
        if "category_id" in book_doc_for_db and book_doc_for_db["category_id"] and isinstance(book_doc_for_db["category_id"], str):
            book_doc_for_db["category_id"] = ObjectId(book_doc_for_db["category_id"])

        # Debug logging
        logger.info(f"DEBUG: Creating book with user_id: {book_doc_for_db.get('user_id')} (type: {type(book_doc_for_db.get('user_id'))})")
        
        result = await db[BOOKS_COLLECTION].insert_one(book_doc_for_db)
        logger.info(f"Created book record with ID: {result.inserted_id}")
        
        created_book_doc = await db[BOOKS_COLLECTION].find_one({"_id": result.inserted_id})
        if not created_book_doc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create initial book record."
            )
            
        return BookInDB(**created_book_doc)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create book record: {e}")
        # Clean up saved PDF file
        try:
            if os.path.exists(pdf_save_path):
                os.remove(pdf_save_path)
        except Exception as cleanup_error:
            logger.error(f"Failed to clean up PDF file: {cleanup_error}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create book record: {str(e)}"
        )

async def update_book_category(
    db: AsyncIOMotorDatabase,
    book_id_str: str,
    new_category_id_str: Optional[str],
    user_id: PyObjectId
) -> Optional[BookInDB]:
    book_to_update = await get_book_by_id_for_user(db, book_id_str, user_id)
    if not book_to_update:
        return None
    new_subject_oid: Optional[PyObjectId] = None
    if new_subject_id_str:
        subject_obj = await subject_service.get_subject_by_id_for_user(db, new_subject_id_str, user_id)
        if not subject_obj:
            raise ValueError(f"Target subject ID '{new_category_id_str}' not found or does not belong to user.")
        new_subject_oid = subject_obj.id
    
    # Ensure user_id is actual ObjectId for MongoDB query
    user_oid = ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id
    
    update_result = await db[BOOKS_COLLECTION].update_one(
        {"_id": book_to_update.id, "user_id": user_oid},
        {"$set": {"category_id": new_subject_oid}}
    )
    if update_result.modified_count == 1:
        updated_book_doc = await db[BOOKS_COLLECTION].find_one({"_id": book_to_update.id})
        if updated_book_doc:
            return BookInDB(**updated_book_doc)
    current_book_doc_after_attempt = await db[BOOKS_COLLECTION].find_one({"_id": book_to_update.id})
    if current_book_doc_after_attempt:
        return BookInDB(**current_book_doc_after_attempt)
    return None

async def get_user_books(
    db: AsyncIOMotorDatabase, 
    user_id: PyObjectId
) -> List[BookPublic]:
    # Ensure user_id is actual ObjectId for MongoDB query
    user_oid = ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id
    
    books_cursor = db[BOOKS_COLLECTION].find({"user_id": user_oid}).sort("upload_date", -1)
    db_books = await books_cursor.to_list(length=None)
    return [BookPublic.from_db_model(BookInDB(**book_doc)) for book_doc in db_books]

async def get_book_by_id_for_user(
    db: AsyncIOMotorDatabase, 
    book_id_str: str, 
    user_id: PyObjectId
) -> Optional[BookInDB]:
    try:
        book_oid = ObjectId(book_id_str)
    except Exception as e:
        logger.debug(f"Invalid book_id format: {book_id_str}. Error: {e}")
        return None
    
    # Ensure user_id is actual ObjectId for MongoDB query
    user_oid = ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id
    
    # Debug logging
    logger.info(f"DEBUG: Querying book - book_id: {book_oid} (type: {type(book_oid)}), user_id: {user_oid} (type: {type(user_oid)})")
    
    book_doc = await db[BOOKS_COLLECTION].find_one({"_id": book_oid, "user_id": user_oid})
    
    if book_doc:
        logger.info(f"DEBUG: Book found! doc._id={book_doc.get('_id')}, doc.user_id={book_doc.get('user_id')}")
        return BookInDB(**book_doc)
    else:
        logger.warning(f"DEBUG: Book NOT found in database. Checking if book exists at all...")
        # Check if book exists regardless of user
        any_book = await db[BOOKS_COLLECTION].find_one({"_id": book_oid})
        if any_book:
            logger.error(f"DEBUG: Book EXISTS but user_id mismatch! DB user_id: {any_book.get('user_id')} (type: {type(any_book.get('user_id'))}), Query user_id: {user_oid} (type: {type(user_oid)})")
        else:
            logger.error(f"DEBUG: Book does NOT exist in database at all!")
    
    return None

async def get_book_pdf_filepath(
    db: AsyncIOMotorDatabase, 
    book_id_str: str, 
    user_id: PyObjectId
) -> Optional[str]:
    book = await get_book_by_id_for_user(db, book_id_str, user_id)
    if book and book.file_path_local and os.path.exists(book.file_path_local):
        return book.file_path_local
    return None

async def get_book_extracted_text(
    db: AsyncIOMotorDatabase, 
    book_id_str: str, 
    user_id: PyObjectId
) -> Optional[str]:
    book = await get_book_by_id_for_user(db, book_id_str, user_id)
    if book and book.extracted_text_path_local and os.path.exists(book.extracted_text_path_local):
        try:
            with open(book.extracted_text_path_local, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading extracted text file {book.extracted_text_path_local}: {e}")
            return None
    return None

async def delete_book_for_user(
    db: AsyncIOMotorDatabase,
    book_id_str: str,
    user_id: PyObjectId
) -> bool:
    """
    Deletes a book and all associated data (topics, quizzes, files, vector store).
    """
    try:
        book_to_delete = await get_book_by_id_for_user(db, book_id_str, user_id)
        if not book_to_delete:
            return False
        
        book_obj_id = book_to_delete.id
        logger.info(f"Starting deletion process for book_id: {book_id_str}")

        # Delete associated MongoDB data
        
        # Delete topics
        try:
            result = await db[BOOK_TOPICS_COLLECTION].delete_many({"book_id": book_obj_id})
            logger.info(f"Deleted {result.deleted_count} topics for book_id: {book_id_str}")
        except Exception as e:
            logger.warning(f"Failed to delete topics for book {book_id_str}: {e}")

        # Delete quiz results
        try:
            result = await db[QUIZ_RESULTS_COLLECTION].delete_many({"book_id": book_obj_id})
            logger.info(f"Deleted {result.deleted_count} quiz results for book_id: {book_id_str}")
        except Exception as e:
            logger.warning(f"Failed to delete quiz results for book {book_id_str}: {e}")

        # Delete local files
        
        # Delete PDF file
        if book_to_delete.file_path_local and os.path.exists(book_to_delete.file_path_local):
            try:
                os.remove(book_to_delete.file_path_local)
                logger.info(f"Deleted PDF file: {book_to_delete.file_path_local}")
            except OSError as e:
                logger.warning(f"Error removing PDF file {book_to_delete.file_path_local}: {e}")
                
        # Delete extracted text file
        if book_to_delete.extracted_text_path_local and os.path.exists(book_to_delete.extracted_text_path_local):
            try:
                os.remove(book_to_delete.extracted_text_path_local)
                logger.info(f"Deleted text file: {book_to_delete.extracted_text_path_local}")
            except OSError as e:
                logger.warning(f"Error removing text file {book_to_delete.extracted_text_path_local}: {e}")
                
        # Delete vector store directory
        vector_store_path = os.path.join(LOCAL_VECTOR_STORE_DIR, f"{book_id_str}.faiss")
        
        if os.path.exists(vector_store_path):
            try:
                shutil.rmtree(vector_store_path)
                logger.info(f"Deleted vector store: {vector_store_path}")
            except OSError as e:
                logger.warning(f"Error removing vector store directory {vector_store_path}: {e}")
        else:
            logger.debug(f"Vector store path not found (skipping): {vector_store_path}")

        # Finally, delete the book record itself
        user_oid = ObjectId(user_id) if not isinstance(user_id, ObjectId) else user_id
        delete_result = await db[BOOKS_COLLECTION].delete_one(
            {"_id": book_obj_id, "user_id": user_oid}
        )
        
        if delete_result.deleted_count == 1:
            logger.info(f"Successfully deleted book_id: {book_id_str}")
            return True
        else:
            logger.warning(f"Book record not deleted for book_id: {book_id_str}")
            return False
    
    except Exception as e:
        logger.error(f"Error deleting book {book_id_str}: {e}")
        return False

async def get_topics_for_book(
    db: AsyncIOMotorDatabase,
    book_id_str: str,
    user_id: PyObjectId
) -> List[BookTopicPublic]:
    """
    Retrieves the list of topics (title and ID, no content) for a specific book
    that the user owns. Uses projection to avoid loading large content fields.
    """
    try:
        # Verify user has access to the book
        book = await get_book_by_id_for_user(db, book_id_str, user_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found or access denied."
            )
        
        # Define projection to fetch only needed fields
        projection = {
            "_id": 1,
            "book_id": 1,
            "topic_title": 1,
            "page_start": 1
        }
        
        # Convert book.id to ObjectId for proper query matching
        book_obj_id = ObjectId(book.id) if not isinstance(book.id, ObjectId) else book.id
        
        # Fetch topics using projection
        topics_cursor = db[BOOK_TOPICS_COLLECTION].find(
            {"book_id": book_obj_id},
            projection=projection
        ).sort("page_start", 1)
        
        db_topics = await topics_cursor.to_list(length=None)
        
        logger.info(f"DEBUG: Found {len(db_topics)} topics in database for book_id: {book_obj_id}")
        if db_topics:
            logger.info(f"DEBUG: Sample topic IDs: {[str(t['_id']) for t in db_topics[:3]]}")
            logger.info(f"DEBUG: Last topic ID: {str(db_topics[-1]['_id'])}")
        
        # Convert to public models
        result_topics = [
            BookTopicPublic(
                id=str(topic_doc["_id"]),
                book_id=str(topic_doc["book_id"]),
                topic_title=topic_doc["topic_title"],
                page_start=topic_doc["page_start"]
            )
            for topic_doc in db_topics
        ]
        
        logger.info(f"DEBUG: Returning {len(result_topics)} topics to frontend")
        logger.info(f"DEBUG: First returned ID: {result_topics[0].id if result_topics else 'NONE'}")
        logger.info(f"DEBUG: Last returned ID: {result_topics[-1].id if result_topics else 'NONE'}")
        return result_topics
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve topics for book_id: {book_id_str}. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve topics: {str(e)}"
        )


async def get_topic_content_by_id(
    db: AsyncIOMotorDatabase,
    book_id_str: str,
    topic_id_str: str,
    user_id: PyObjectId
) -> Optional[str]:
    """
    Retrieves the content of a specific topic for a book that the user owns.
    Returns the topic content text or None if not found.
    """
    try:
        # Verify user has access to the book
        book = await get_book_by_id_for_user(db, book_id_str, user_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found or access denied."
            )
        
        # Convert topic_id to ObjectId
        try:
            topic_obj_id = ObjectId(topic_id_str)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid topic ID format."
            )
        
        # Convert book.id to ObjectId for proper query matching
        book_obj_id = ObjectId(book.id) if not isinstance(book.id, ObjectId) else book.id
        
        # Fetch the topic
        logger.info(f"Fetching topic - topic_id: {topic_obj_id}, book_id: {book_obj_id}")
        topic_doc = await db[BOOK_TOPICS_COLLECTION].find_one({
            "_id": topic_obj_id,
            "book_id": book_obj_id
        })
        
        if not topic_doc:
            # Debug: Check if topic exists without book_id filter
            any_topic = await db[BOOK_TOPICS_COLLECTION].find_one({"_id": topic_obj_id})
            if any_topic:
                logger.error(f"Topic exists but book_id mismatch! Topic book_id: {any_topic.get('book_id')}, Expected: {book_obj_id}")
            else:
                logger.error(f"Topic does not exist in database: {topic_obj_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found for this book."
            )
        
        # Return the content field
        return topic_doc.get("content", "")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve topic content. topic_id: {topic_id_str}, Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve topic content: {str(e)}"
        )


async def search_book_pdf(
    db: AsyncIOMotorDatabase,
    book_id_str: str,
    query: str,
    user_id: PyObjectId
) -> List[Dict[str, Any]]:
    """
    Searches the PDF content of a book for a specific query string.
    Returns a list of dictionaries containing page number and a snippet of text.
    """
    try:
        # Get PDF path (security check included)
        pdf_path = await get_book_pdf_filepath(db, book_id_str, user_id)
        if not pdf_path:
            logger.warning(f"PDF path not found for book_id: {book_id_str}")
            return []

        results: List[Dict[str, Any]] = []
        query_lower = query.lower()
        doc: Optional[fitz.Document] = None

        try:
            doc = fitz.open(pdf_path)
            
            # Iterate through all pages
            for page_num, page in enumerate(doc):  # type: ignore
                try:
                    text = page.get_text()  # type: ignore
                    if not text:
                        continue

                    text_lower = text.lower()
                    start_idx = 0
                    
                    # Find all occurrences on this page
                    while True:
                        idx = text_lower.find(query_lower, start_idx)
                        if idx == -1:
                            break

                        # Extract snippet (40 chars before and after)
                        snippet_start = max(0, idx - 40)
                        snippet_end = min(len(text), idx + len(query) + 40)
                        
                        raw_snippet = text[snippet_start:snippet_end].replace('\n', ' ').strip()
                        formatted_snippet = "..." + raw_snippet + "..."

                        results.append({
                            "page_number": page_num + 1,
                            "snippet": formatted_snippet
                        })

                        # Safety limit: Stop if too many results (50)
                        if len(results) >= 50:
                            logger.info(f"Search result limit reached (50) for book_id: {book_id_str}")
                            doc.close()
                            return results

                        # Move past this match
                        start_idx = idx + len(query)
                
                except Exception as page_error:
                    logger.debug(f"Error searching page {page_num + 1}: {page_error}")
                    continue

            doc.close()
        
        except Exception as search_error:
            logger.error(f"Error searching PDF for book {book_id_str}: {search_error}")
            if doc:
                doc.close()
            
        return results
    
    except Exception as e:
        logger.error(f"Search failed for book_id: {book_id_str}. Error: {e}")
        return []