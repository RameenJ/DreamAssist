# learn-ease-fyp/backend/services/ai_service.py

import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch 
import json
import os
import re
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status 
from langchain_groq import ChatGroq
from pydantic import SecretStr
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from . import vector_service
# COMMENTED OUT - torch/torchvision version mismatch: from sentence_transformers import SentenceTransformer
import numpy as np
# from scipy.spatial.distance import cosine  # COMMENTED OUT - unused, requires scipy with torch
import spacy
import nltk
from nltk.corpus import wordnet

# --- Google Gemini API ---
from google import genai

# --- MODIFICATION: ADDED IMPORTS FOR DB STORAGE ---
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from . import quiz_service
from . import ai_mentor_chat_service  # <<< IMPORT FOR AI MENTOR CHAT HISTORY
from . import sentiment_analysis_service  # <<< IMPORT FOR SENTIMENT ANALYSIS

# Import ALL relevant schemas
from models.ai_schemas import (
    QuestionAnswerPair,
    QuizGenerationRequest, GeneratedQuiz, QuizQuestion, 
    QuizEvaluationRequest, QuizEvaluationResponse, EvaluatedQuestionResult,
    ChatRequest, ChatResponse
)
from models.book_schemas import BookTopicInDB # <<< IMPORT FOR TOPICS

# Load configurations from environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "models/gemini-2.5-flash") 
BOOK_TOPICS_COLLECTION = "book_topics" # <<< COLLECTION NAME
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# =========================================================================
# --- AIService CLASS (Wrapper for AI operations) ---
# =========================================================================

class AIService:
    """Wrapper class for AI service operations including chat, embeddings, and quizzes"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.chat_model = None
        self._initialize_chat_model()
    
    def _initialize_chat_model(self):
        """Initialize Groq chat model for persona conversations"""
        try:
            if GROQ_API_KEY:
                self.chat_model = ChatGroq(
                    temperature=0.7, 
                    model="llama-3.3-70b-versatile", 
                    api_key=SecretStr(GROQ_API_KEY)
                )
                print("INFO: AIService - Groq Llama3 chat model initialized")
            else:
                print("WARNING: AIService - GROQ_API_KEY not found. Chat will be limited.")
        except Exception as e:
            print(f"ERROR: AIService - Failed to initialize chat model: {e}")
    
    async def chat(self, system_prompt: str, user_message: str) -> str:
        """Generate AI response using system prompt and user message"""
        if not self.chat_model:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI chat service is not available"
            )
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_message)
            ])
            
            chain = prompt | self.chat_model | StrOutputParser()
            response = chain.invoke({})
            return response
        except Exception as e:
            print(f"ERROR: AIService.chat - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Chat generation failed: {str(e)}"
            )

# --- New Configuration for Embeddings (Required for Evaluation) ---
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2") 

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Initialize Gemini client
gemini_client = None
if GOOGLE_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
        logger.info("Gemini client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
else:
    logger.warning("GOOGLE_API_KEY not found in environment. AI generation features will be limited.")


# =========================================================================
# --- EMBEDDING MODEL (For Quiz Evaluation - Module 4) ---
# =========================================================================
embedding_model: Optional[Any] = None

def load_embedding_model():
    """Loads the Sentence Transformer model for generating vector embeddings."""
    global embedding_model
    try:
        logger.info(f"Loading embedding model '{EMBEDDING_MODEL_NAME}'...")
        # SentenceTransformer commented out due to dependency conflicts
        # embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        logger.info(f"Embedding model '{EMBEDDING_MODEL_NAME}' skipped (dependency conflict).")
    except Exception as e:
        logger.error(f"Failed to load embedding model '{EMBEDDING_MODEL_NAME}': {e}")
        embedding_model = None

if embedding_model is None:
    load_embedding_model()

def get_sentence_embedding(text: str) -> np.ndarray:
    """Generates the vector embedding for a given text."""
    if not embedding_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding model is not available for evaluation."
        )
    clean_text = str(text).strip() or " "
    return embedding_model.encode(clean_text, convert_to_numpy=True)

# =========================================================================
# --- CORE QUIZ GENERATION (Module 4) ---
# =========================================================================

async def _call_gemini_for_quiz_json(prompt: str, num_questions: int = 5) -> List[Dict[str, str]]:
    """Helper function to call Gemini API to generate the quiz JSON."""
    if not gemini_client or not GEMINI_MODEL_NAME:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API is not configured (API Key or Model Name missing)."
        )

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.5,  # Reduced from 0.7 for more consistent JSON
                "max_output_tokens": 4096,
                "top_p": 0.8,  # More deterministic output
            }
        )

        if not response or not response.text:
            print(f"ERROR: AI Service (Quiz Generation) - Gemini API response is empty.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gemini API returned an empty response."
            )

        raw_generated_text = response.text.strip()
        print(f"DEBUG: Raw Gemini response (first 500 chars): {raw_generated_text[:500]}")
        
        # Clean markdown code blocks
        cleaned_text = raw_generated_text
        if "```json" in cleaned_text:
            cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned_text:
            cleaned_text = cleaned_text.split("```")[1].split("```")[0].strip()
        
        # Find JSON array bounds
        json_start = cleaned_text.find('[')
        json_end = cleaned_text.rfind(']')

        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_text = cleaned_text[json_start : json_end + 1]
        else:
            json_text = cleaned_text
        
        # Enhanced JSON cleaning
        import re
        # Remove trailing commas before closing brackets/braces
        json_text = re.sub(r',\s*}', '}', json_text)
        json_text = re.sub(r',\s*]', ']', json_text)
        # Add commas between adjacent objects/arrays if missing
        json_text = re.sub(r'\}\s*\{', '},{', json_text)
        json_text = re.sub(r'\]\s*\[', '],[', json_text)
        # Remove any control characters
        json_text = re.sub(r'[\x00-\x1f\x7f]', '', json_text)
        
        try:
            parsed_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"ERROR: First JSON parse failed: {str(e)}")
            print(f"ERROR: Failed JSON text (first 1500 chars):\n{json_text[:1500]}")
            
            # Try more aggressive cleaning
            # Fix missing commas between array elements
            json_text = re.sub(r'\}\s+\{', '},{', json_text)
            # Fix quotes in strings
            json_text = re.sub(r'(?<!\\)"(?![\s,:}\]])', '\\"', json_text)
            
            try:
                parsed_data = json.loads(json_text)
            except json.JSONDecodeError as e2:
                print(f"ERROR: Second JSON parse failed: {str(e2)}")
                print(f"ERROR: Error location: line {e2.lineno}, column {e2.colno}")
                
                # Last resort: manual extraction with nested object support
                parsed_data = []
                # Find all complete question objects
                pattern = r'\{\s*"question_text"\s*:\s*"[^"]*"\s*,\s*"correct_answer"\s*:\s*"[^"]*"\s*,\s*"answer_variants"\s*:\s*\[[^\]]*\]\s*,\s*"explanation"\s*:\s*"[^"]*"\s*\}'
                for match in re.finditer(pattern, json_text, re.DOTALL):
                    try:
                        obj_text = match.group()
                        obj = json.loads(obj_text)
                        if all(k in obj for k in ['question_text', 'correct_answer', 'explanation']):
                            parsed_data.append(obj)
                    except Exception as ex:
                        print(f"WARN: Failed to parse extracted object: {ex}")
                        continue
                
                if not parsed_data:
                    # If still no data, try Groq as fallback
                    print(f"⚠️  Gemini JSON parsing failed. Attempting fallback with Groq...")
                    try:
                        parsed_data = await _call_groq_for_quiz_json_fallback(json_text, num_questions=num_questions)
                        if parsed_data:
                            print(f"✅ Groq fallback successful! Generated {len(parsed_data)} questions")
                            return parsed_data
                    except Exception as groq_error:
                        print(f"⚠️  Groq fallback also failed: {groq_error}")
                    
                    # If still no data, log full response and fail
                    print(f"ERROR: Complete failed JSON text:\n{json_text}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to parse quiz JSON from Gemini. Error: {str(e2)}"
                    )

        if not isinstance(parsed_data, list):
            raise ValueError("Parsed data is not a list.")
            
        if not parsed_data:
            raise ValueError("No questions were generated.")
            
        return parsed_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: AI Service (Quiz Generation) - Unexpected error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quiz generation failed: {str(e)}"
        )


async def _call_groq_for_quiz_json_fallback(failed_json_text: str, num_questions: int = 5) -> List[Dict[str, str]]:
    """
    Fallback function: Use Groq Llama3 to parse or regenerate quiz JSON if Gemini fails.
    """
    from services.recommendation_service import get_groq_client
    
    try:
        groq_client = get_groq_client()
        if not groq_client:
            print("⚠️  Groq client not available for fallback")
            return []
        
        # Try to ask Groq to fix/regenerate the JSON
        repair_prompt = f"""You are a JSON repair specialist. The following text was supposed to be JSON but failed parsing.
Either fix it or regenerate {num_questions} valid quiz questions in this exact JSON format:

[
    {{"question_text": "...", "correct_answer": "...", "answer_variants": ["...", "..."], "explanation": "..."}},
    ... ({num_questions} items)
]

Failed/Malformed JSON:
{failed_json_text[:2000]}

Output ONLY valid JSON array, no markdown, no explanations."""
        
        response = groq_client.messages.create(
            model="mixtral-8x7b-32768",  # or "llama2-70b-4096"
            messages=[{"role": "user", "content": repair_prompt}],
            max_tokens=2048,
            temperature=0.3  # Low temperature for reliable JSON
        )
        
        repaired_json = response.content[0].text.strip()
        print(f"📝 Groq repair attempt: {repaired_json[:300]}")
        
        # Try to parse the repaired JSON
        parsed = json.loads(repaired_json)
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed[:num_questions]
        
        return []
        
    except Exception as e:
        print(f"⚠️  Groq fallback error: {e}")
        return []

# --- (MODIFIED) Function signature and logic updated ---
async def generate_quiz_from_text(
    request: QuizGenerationRequest,
    db: AsyncIOMotorDatabase,
    user_id: ObjectId
) -> GeneratedQuiz:
    """
    Generates a quiz from a specific topic_id or book_id, verifying user access.
    """
    
    # 1. Determine whether we're using topic_id or book_id
    topic_id_to_use = request.topic_id
    
    if not topic_id_to_use and request.book_id:
        # If only book_id is provided, fetch a random topic from that book
        try:
            book_oid = ObjectId(request.book_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Book ID format."
            )
        
        # Verify user owns the book
        book_doc = await db["books"].find_one({"_id": book_oid, "user_id": user_id})
        if not book_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found or access denied."
            )
        
        # Get a random topic from this book
        # Try with both ObjectId and string since book_id might be stored either way
        pipeline = [
            {"$match": {"$or": [
                {"book_id": book_oid},
                {"book_id": request.book_id}
            ]}},
            {"$sample": {"size": 1}}
        ]
        cursor = db[BOOK_TOPICS_COLLECTION].aggregate(pipeline)
        topics = await cursor.to_list(length=1)
        
        if not topics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No topics found for this book. Please ensure the book has been processed."
            )
        
        topic_id_to_use = str(topics[0]["_id"])
    
    # 2. Fetch the topic content securely
    # Note: _id is stored as ObjectId in the database
    topic_id_str = topic_id_to_use
    
    # Convert string to ObjectId for querying
    try:
        topic_id_oid = ObjectId(topic_id_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Topic ID format."
        )
    
    print(f"DEBUG: Querying collection '{BOOK_TOPICS_COLLECTION}' for topic with _id: {topic_id_oid}")
    topic_doc = await db[BOOK_TOPICS_COLLECTION].find_one({"_id": topic_id_oid})
    
    if not topic_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found."
        )
    
    print(f"DEBUG: Topic found! book_id from topic: {topic_doc.get('book_id')} (type: {type(topic_doc.get('book_id')).__name__})")
    
    # Get book_id from topic - handle both string and ObjectId
    topic_book_id = topic_doc.get('book_id')
    if isinstance(topic_book_id, str):
        # If book_id is stored as string, try to convert to ObjectId for book lookup
        try:
            book_id_for_query = ObjectId(topic_book_id)
        except:
            book_id_for_query = topic_book_id
    else:
        book_id_for_query = topic_book_id
    
    print(f"DEBUG: Looking up book with _id: {book_id_for_query} (type: {type(book_id_for_query).__name__}) and user_id: {user_id}")

    # 3. Verify user ownership by checking the parent book
    book_doc = await db["books"].find_one(
        {"_id": book_id_for_query, "user_id": user_id}
    )
    
    if not book_doc:
        print(f"DEBUG: Book not found or access denied")
        # Try querying with string book_id if ObjectId didn't work
        if isinstance(book_id_for_query, ObjectId):
            book_doc = await db["books"].find_one(
                {"_id": topic_book_id, "user_id": user_id}
            )
            print(f"DEBUG: Retry with string book_id: {book_doc is not None}")
        
        if not book_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book for this topic not found or access denied."
            )
    
    print(f"DEBUG: Book access verified!")
    
    # Get topic content
    topic_content = topic_doc.get('content', '')
    print(f"DEBUG: Topic content length: {len(topic_content) if topic_content else 0}")

    # 4. Get the content and validate length
    if not topic_content or len(topic_content.strip()) < 100: # 100 is min_length from old schema
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected topic content is too short to generate a quiz."
        )

    # 5. Proceed with quiz generation using the fetched content
    num_questions = request.num_questions

    # --- Prioritize weak topics for the user ---
    from services.user_service import get_user_subject_profiles
    weak_topics = []
    book_subject = book_doc.get('subject')  # Get subject from the book
    if user_id and book_subject:
        profiles = await get_user_subject_profiles(db, user_id)
        for profile in profiles:
            if hasattr(profile, 'weak_topics') and profile.subject == book_subject:
                weak_topics = profile.weak_topics
                break

    weak_topics_str = ", ".join(weak_topics) if weak_topics else None

    prompt = f"""You are an expert educational assistant creating a study quiz.
Generate EXACTLY {num_questions} unique question-answer pairs based ONLY on the following content.

### Instructions:
1. **Question Goal:** Your primary goal is to create questions that test **conceptual understanding**, not simple fact memorization. Questions should require the user to explain **'why'** or **'how'** something works, **compare/contrast** concepts, or state the **implications** of a fact.
* **AVOID:** Simple questions like "What is X?" or "List the two types of Y."
* **PREFER:** Analytical questions like "How does X differ from Y?" or "What is the main advantage of using X?"
2.  **Correct Answer:** Must be a **complete but concise sentence** that fully answers the question. For example, instead of just 'Routers,' the answer should be 'The nodes in a graph represent routers.' This creates a fair target for vector comparison.
3.  **Acceptable Answer Variants:** Provide a JSON array of 2-3 alternative, concise phrases or keywords that are also correct. These will be used to evaluate differently phrased user answers. For example, if the main answer is 'A logically centralized controller,' a variant could be 'An SDN controller.'
4.  **Explanation:** Must be a brief, one-sentence explanation providing context or detail for the correct answer.
5.  **Format:** Output STRICTLY as a JSON array of objects. Do NOT include any code block syntax (e.g., ```json) or any introductory/explanatory text outside the array.

### PRIORITIZE THESE TOPICS IF POSSIBLE:
{weak_topics_str if weak_topics_str else 'None'}

### JSON Structure:
[
    {{
        "question_text": "...",
        "correct_answer": "...",
        "answer_variants": ["...", "..."],
        "explanation": "..."
    }},
    ... ({num_questions} items)
]

### Content to use:
---
{topic_content} 
---
"""
    raw_quiz_data = await _call_gemini_for_quiz_json(prompt, num_questions=num_questions)
    
    questions: List[QuizQuestion] = []
    for item in raw_quiz_data:
        try:
            # Ensure answer_variants is always a list
            answer_variants = item.get('answer_variants', [])
            if not isinstance(answer_variants, list):
                answer_variants = [answer_variants] if answer_variants else []
            
            questions.append(QuizQuestion(
                question_text=item['question_text'],
                correct_answer=item['correct_answer'],
                answer_variants=answer_variants,
                explanation=item['explanation']
            ))
        except (KeyError, ValueError) as e:
            print(f"WARN: Quiz Generation - Skipping invalid question item: {item}. Error: {e}")
            
    if not questions:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI failed to generate any valid quiz questions.")

    import uuid
    quiz_id = str(uuid.uuid4())
    
    # Convert book_id to string for response
    book_id_str = str(book_doc["_id"])
    topic_name_str = topic_doc.get('topic_title', book_doc.get('subject', 'Unknown'))
    
    return GeneratedQuiz(quiz_id=quiz_id, book_id=book_id_str, topic_name=topic_name_str, questions=questions)
# --- End of modification ---


# backend/services/ai_service.py

# =========================================================================
# --- CORE QUIZ EVALUATION (Module 4) ---
# =========================================================================

async def evaluate_quiz_attempt(
    request: QuizEvaluationRequest,
    generated_quiz: GeneratedQuiz,
    db: AsyncIOMotorDatabase,  # For DB storage
    user_id: ObjectId  # For DB storage
) -> QuizEvaluationResponse:
    """
    Evaluates the user's short-answer quiz attempt using cosine similarity of embeddings
    and saves the result to the DB, providing the explanation.
    """
    if not embedding_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Evaluation service is unavailable (Embedding model not loaded)."
        )

    # 1. Map generated quiz questions for easy lookup by question text
    quiz_map = {q.question_text: q for q in generated_quiz.questions}
    
    total_similarity_score = 0.0
    results: List[EvaluatedQuestionResult] = []
    num_evaluated_questions = 0

    # 2. Process each user answer
    for user_attempt in request.attempted_answers:
        question_text = user_attempt.question_text
        user_answer = user_attempt.user_answer.strip()
        
        if question_text not in quiz_map:
            print(f"WARN: Evaluation - Skipping answer for unknown question: {question_text}")
            continue

        ai_question = quiz_map[question_text]
        correct_answer = ai_question.correct_answer.strip()
        correct_explanation = ai_question.explanation.strip() # Get the explanation!
        
        similarity_score = 0.0
        
        # --- INTEGRATED LOGIC TO CHECK ALL ANSWER VARIANTS ---
        try:
            # 3. Get user answer embedding once
            user_embedding = get_sentence_embedding(user_answer)

            # Create a list of all possible correct answers
            all_correct_answers = [correct_answer] + ai_question.answer_variants
            
            highest_score = 0.0
            
            # 4. Loop through all correct answers and find the best match
            for answer_text in all_correct_answers:
                if user_answer and answer_text:
                    correct_embedding = get_sentence_embedding(answer_text.strip())
                    cos_distance = cosine(user_embedding, correct_embedding)
                    current_score = 1.0 - cos_distance
                    
                    if current_score > highest_score:
                        highest_score = current_score
            
            similarity_score = highest_score
            # Clamp score between 0.0 and 1.0
            similarity_score = max(0.0, min(1.0, similarity_score))

        except Exception as e:
            print(f"ERROR: Evaluation - Failed to calculate similarity for question '{question_text}': {e}")
            similarity_score = 0.0
            
        total_similarity_score += similarity_score
        num_evaluated_questions += 1
        
        # 5. Compile result
        results.append(EvaluatedQuestionResult(
            question_text=question_text,
            user_answer=user_answer,
            correct_answer=correct_answer,
            correct_explanation=correct_explanation, # <-- INCLUDED FOR FE-3
            similarity_score=round(similarity_score, 4), 
        ))

    # 6. Final Evaluation (Total Score)
    if num_evaluated_questions == 0:
        avg_score = 0.0
    else:
        # Sum of similarity scores divided by number of questions
        avg_score = total_similarity_score / num_evaluated_questions 
    
    # 7. Determine Grade (Using your updated, more lenient scale)
    def get_grade(score: float) -> str:
        if score >= 0.75: return "Excellent (A+)"
        if score >= 0.70: return "Very Good (A)"
        if score >= 0.60: return "Good (B+)"
        if score >= 0.50: return "Fair (B)"
        if score >= 0.40: return "Average (C+)"
        if score >= 0.35: return "Needs Improvement (C)"
        return "Poor (D)"

    final_response = QuizEvaluationResponse(
        quiz_id=request.quiz_id,
        book_id=request.book_id,
        total_score=round(avg_score, 4),
        total_grade=get_grade(avg_score),
        results=results
    )

    # 8. Save result to DB
    try:
        await quiz_service.create_quiz_result(
            db=db,
            user_id=user_id,
            book_id=ObjectId(request.book_id),
            topic_name=request.topic_name,
            eval_response=final_response
        )
        print(f"INFO: Quiz result saved to DB for user {user_id}.")
    except Exception as e:
        # Log the error but don't fail the request.
        print(f"ERROR: Failed to save quiz result to DB for user {user_id}. Error: {e}")

    return final_response

# =========================================================================
# --- AI MENTOR: STUDY RECOMMENDATIONS (NEW) ---
# =========================================================================

async def generate_study_recommendations(
    evaluation: QuizEvaluationResponse,
    topic_name: str
) -> dict:
    """
    Analyzes quiz results and generates personalized study plan using Gemini AI.
    """
    if not gemini_client:
        print("WARN: Gemini client not available, skipping study recommendations")
        return {}
    
    try:
        # Analyze performance
        wrong_questions = []
        partial_questions = []
        correct_questions = []
        
        for result in evaluation.results:
            if result.similarity_score >= 0.7:
                correct_questions.append(result)
            elif result.similarity_score >= 0.5:
                partial_questions.append(result)
            else:
                wrong_questions.append(result)
        
        # Build prompt for Gemini
        prompt = f"""You are an expert educational mentor analyzing a student's quiz performance.

**Topic:** {topic_name}
**Overall Score:** {evaluation.total_score * 100:.0f}% (Grade: {evaluation.total_grade})
**Questions Analyzed:** {len(evaluation.results)}

### Performance Breakdown:
- ✅ Correct Answers: {len(correct_questions)}
- ⚠️ Partial Understanding: {len(partial_questions)}
- ❌ Incorrect Answers: {len(wrong_questions)}

### Detailed Results:
"""
        
        # Add wrong questions (most important)
        if wrong_questions:
            prompt += "\n**❌ Struggled With:**\n"
            for r in wrong_questions[:3]:  # Limit to 3 for brevity
                prompt += f"- Q: {r.question_text}\n"
                prompt += f"  Student Answer: {r.user_answer or 'No answer'}\n"
                prompt += f"  Correct Answer: {r.correct_answer}\n"
                prompt += f"  Score: {r.similarity_score:.0%}\n\n"
        
        # Add partial questions
        if partial_questions:
            prompt += "\n**⚠️ Partial Understanding:**\n"
            for r in partial_questions[:2]:  # Limit to 2
                prompt += f"- Q: {r.question_text}\n"
                prompt += f"  Student Answer: {r.user_answer or 'No answer'}\n"
                prompt += f"  Score: {r.similarity_score:.0%}\n\n"
        
        prompt += """
### Your Task:
Provide a personalized study plan in JSON format:

{
  "overall_assessment": "2-3 sentences summarizing performance",
  "weak_topics": ["specific concept 1", "specific concept 2"],
  "strong_topics": ["concept student knows well"],
  "study_recommendations": "One detailed paragraph with specific, actionable advice on what to study and how",
  "next_steps": [
    "Specific action item 1",
    "Specific action item 2",
    "Specific action item 3"
  ]
}

Be encouraging but honest. Focus on HOW to improve weak areas with concrete steps.
Output ONLY valid JSON, no markdown formatting."""
        
        # Call Gemini
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.7,
                "max_output_tokens": 1024,
            }
        )
        
        # Parse response
        text = response.text.strip()
        
        # Clean markdown if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Find JSON object
        json_start = text.find('{')
        json_end = text.rfind('}')
        if json_start != -1 and json_end != -1:
            text = text[json_start:json_end + 1]
        
        recommendations = json.loads(text)
        
        print(f"INFO: AI Mentor - Generated study recommendations for topic: {topic_name}")
        return recommendations
        
    except Exception as e:
        print(f"ERROR: AI Mentor - Failed to generate recommendations: {type(e).__name__}: {str(e)}")
        return {}

# =========================================================================
# --- EXISTING / OTHER AI MODULES (Unchanged) ---
# =========================================================================

# --- Summarization using Gemini API (Replaced T5 Model) ---
# Old T5 Model Implementation Commented Out - Now Using Gemini for Better Quality
# MODEL_NAME_SUMMARIZE = "mohsinnyz/Booksum-Edu"
# tokenizer_summarize: Any = None 
# model_summarize: Any = None 
# device_summarize: Any = None 

async def generate_summary(text_to_summarize: str) -> str:
    """
    Generate a concise summary of the provided text using Gemini API.
    This replaces the previous T5 model implementation for better quality and reliability.
    """
    if not gemini_client:
        print("ERROR: AI Service (generate_summary) - Gemini client is not available.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Summarization service is currently unavailable (Gemini API not configured)."
        )

    if not text_to_summarize or len(text_to_summarize.strip()) < 20:
        return "Input text is too short to summarize effectively."

    try:
        # Prepare the prompt for Gemini
        prompt = f"""Please provide a concise and informative summary of the following text. 
Focus on the main ideas and key points. Keep the summary clear and well-structured.

Text to summarize:
{text_to_summarize}

Summary:"""

        # Generate summary using Gemini with proper config
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.3,  # Low temperature for consistent, focused summaries
                "max_output_tokens": 2048,  # Sufficient for summaries
                "top_p": 0.8  # More deterministic output
            }
        )
        
        if not response.parts:
            print(f"ERROR: AI Service (generate_summary) - Gemini API response has no parts. Full response: {response}")
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Gemini API call blocked for summary: {response.prompt_feedback.block_reason_message}"
                )
            raise ValueError("Gemini API returned empty response")
        
        summary = response.text.strip()
        
        if not summary:
            raise ValueError("Gemini returned an empty summary")
            
        return summary
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"ERROR: AI Service - Error during summarization with Gemini API: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )

# --- Question Generation Model (Fine-tuned Hugging Face - mohsinnyz/Flan-SQuAD) ---
MODEL_NAME_QNA_QUESTIONS = "mohsinnyz/Flan-SQuAD"
tokenizer_qna_questions: Any = None
model_qna_questions: Any = None
device_qna_questions: Any = None

def load_qna_question_model():
    global tokenizer_qna_questions, model_qna_questions, device_qna_questions
    try:
        print(f"INFO: AI Service - Loading Q&A Question model '{MODEL_NAME_QNA_QUESTIONS}'...")
        tokenizer_qna_questions = AutoTokenizer.from_pretrained(MODEL_NAME_QNA_QUESTIONS)
        model_qna_questions = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME_QNA_QUESTIONS)
        device_qna_questions = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model_qna_questions.to(device_qna_questions)
        print(f"INFO: AI Service - Q&A Question model '{MODEL_NAME_QNA_QUESTIONS}' loaded successfully on {device_qna_questions}.")
    except Exception as e:
        print(f"ERROR: AI Service - Failed to load Q&A Question model '{MODEL_NAME_QNA_QUESTIONS}': {e}")
        tokenizer_qna_questions = None
        model_qna_questions = None
        device_qna_questions = None

if model_qna_questions is None: 
    load_qna_question_model()

async def _generate_questions_from_hf_model(text_content: str, num_questions: int = 5) -> List[str]:
    if not model_qna_questions or not tokenizer_qna_questions:
        print("ERROR: AI Service (_generate_questions_from_hf_model) - Q&A Question model/tokenizer is not available.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Question generation service is currently unavailable (HF model not loaded)."
        )

    print(f"INFO: AI Service - Generating questions using Hugging Face model '{MODEL_NAME_QNA_QUESTIONS}'.")
    
    passage_for_prompt = text_content

    question_format_lines = "\n".join([f"{i+1}. <question>?" for i in range(min(num_questions, 5))])

    prompt = f"""
Generate exactly only {min(num_questions, 5)} distinct and clear questions based ONLY on the passage below.
Format strictly as a numbered list like this:

{question_format_lines}

Do NOT generate answers or any extra text.

Passage:
\"\"\"{passage_for_prompt}\"\"\"
"""
    try:
        inputs = tokenizer_qna_questions(prompt, return_tensors="pt", truncation=True, max_length=1024).to(device_qna_questions)

        outputs = model_qna_questions.generate(
            inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.95,
            repetition_penalty=1.1,
            num_return_sequences=1,
        )

        generated_text = tokenizer_qna_questions.decode(outputs[0], skip_special_tokens=True)
        
        print(f"DEBUG: AI Service (_generate_questions_from_hf_model) - Raw Output from HF Q&A Model: {generated_text}")

        questions = re.findall(r"\d+\.\s*(.+?\?)", generated_text)

        seen = set()
        unique_questions = []
        for q_text in questions:
            q_clean = q_text.strip()
            if q_clean not in seen:
                seen.add(q_clean)
                unique_questions.append(q_clean)
        
        print(f"DEBUG: AI Service (_generate_questions_from_hf_model) - Extracted {len(unique_questions)} unique questions.")
        return unique_questions[:num_questions]

    except Exception as e:
        print(f"ERROR: AI Service - Error during question generation with model {MODEL_NAME_QNA_QUESTIONS}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating questions from HF model: {str(e)}"
        )

async def _generate_answer_with_gemini(question: str, context_text: str) -> str:
    if not GOOGLE_API_KEY or not GEMINI_MODEL_NAME:
        print("ERROR: AI Service (_generate_answer_with_gemini) - API Key or Model Name is not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer generation service is not configured (API Key or Model Name missing)."
        )

    prompt = f"""Given the following context text and a question, provide a concise and accurate answer based *only* on the information available in the context.

Context:
---
{context_text}
---

Question: {question}

Answer:"""

    try:
        print(f"INFO: AI Service (_generate_answer_with_gemini) - Calling Gemini API ({GEMINI_MODEL_NAME}) for answer.")
        
        if not gemini_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gemini client is not initialized."
            )
        
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.3,
                "max_output_tokens": 256
            }
        )

        if not response.parts:
            print(f"ERROR: AI Service (_generate_answer_with_gemini) - Gemini API response has no parts. Full response: {response}")
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Gemini API call for answer blocked: {response.prompt_feedback.block_reason_message}"
                )
            return "The AI could not generate an answer (empty response parts from Gemini)."

        answer_text = (response.text or "").strip()
        if not answer_text:
            return "The AI could not formulate an answer based on the provided context (empty text from Gemini)."
        return answer_text

    except HTTPException as he: 
        raise he
    except Exception as e:
        print(f"ERROR: AI Service (_generate_answer_with_gemini) - Error during Gemini API call: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while generating an answer with Gemini: {str(e)}"
        )

async def generate_qna_from_text(text_to_generate_from: str) -> List[QuestionAnswerPair]:
    if not text_to_generate_from or len(text_to_generate_from.strip()) < 20:
        print("WARN: AI Service (Q&A) - Input text for Q&A is too short.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text too short for Q&A generation.")

    try:
        generated_questions = await _generate_questions_from_hf_model(text_to_generate_from, num_questions=5) 

        if not generated_questions:
            print("INFO: AI Service (Q&A) - No questions were generated by the HF model.")
            return []

        qna_pairs: List[QuestionAnswerPair] = []
        for question_text in generated_questions:
            answer_text = await _generate_answer_with_gemini(question_text, text_to_generate_from)
            qna_pairs.append(QuestionAnswerPair(question=question_text, answer=answer_text))
        
        if not qna_pairs and generated_questions: 
            print("WARN: AI Service (Q&A) - Questions were generated, but no Q&A pairs were formed (all answers might have been empty).")
        
        return qna_pairs

    except HTTPException as he: 
        raise he
    except Exception as e:
        print(f"ERROR: AI Service (generate_qna_from_text) - Unexpected error: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during Q&A generation."
        )
    
# --- Helper function to call Gemini API and parse JSON list output (for Flashcards) ---
async def _call_gemini_for_json_list(prompt: str, error_context: str) -> List[Dict[str, str]]:
    if not GOOGLE_API_KEY or not GEMINI_MODEL_NAME:
        print(f"ERROR: AI Service ({error_context}) - API Key or Model Name is not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{error_context} service is not configured (API Key or Model Name missing)."
        )

    raw_generated_text = ""
    parsed_data: List[Dict[str,str]] = [] 
    json_string_to_parse = "" # Initialize for logging in case of error
    cleaned_text = "" # Initialize to avoid unbound variable

    try:
        print(f"INFO: AI Service ({error_context}) - Calling Gemini API ({GEMINI_MODEL_NAME}).")
        
        if not gemini_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gemini client is not initialized."
            )
        
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.2,
                "max_output_tokens": 3072  # Increased to allow complete flashcard JSON generation
            }
        )

        if not response.parts:
            print(f"ERROR: AI Service ({error_context}) - Gemini API response has no parts. Full response: {response}")
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail=f"Gemini API call blocked for {error_context}: {response.prompt_feedback.block_reason_message}"
                )
            return []

        raw_generated_text = (response.text or "").strip()
        cleaned_text = raw_generated_text
        
        # Robust JSON cleaning
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[len("```json"):]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[len("```"):]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-len("```")]

        cleaned_text = cleaned_text.strip()

        if not cleaned_text:
            print(f"ERROR: AI Service ({error_context}) - Content became empty after cleaning attempts.")
            return []

        # Find the array bounds [..] for robust parsing
        json_string_to_parse = cleaned_text 
        json_start_index = cleaned_text.find('[')
        json_end_index = cleaned_text.rfind(']')

        if json_start_index != -1 and json_end_index != -1 and json_end_index > json_start_index:
            json_string_to_parse = cleaned_text[json_start_index : json_end_index+1]
        
        parsed_data = json.loads(json_string_to_parse)

        if not isinstance(parsed_data, list):
            raise ValueError("Parsed data is not a list.")

        validated_items: List[Dict[str,str]] = []
        for item in parsed_data: # Validation specific to flashcards
            if isinstance(item, dict) and "front" in item and "back" in item: 
                validated_items.append({"front": str(item["front"]), "back": str(item["back"])})
            else:
                print(f"WARN: AI Service ({error_context}) - Skipping invalid item: {item}")

        if not validated_items and parsed_data: 
            raise ValueError("No valid items found after validation, though initial parse was a list.")
        return validated_items

    except json.JSONDecodeError as e:
        text_that_failed_parsing = json_string_to_parse or cleaned_text
        print(f"ERROR: AI Service ({error_context}) - Failed to decode JSON. Text attempted for parsing was: '{text_that_failed_parsing}'. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse {error_context} data from Gemini API (JSONDecodeError)."
        )
    except ValueError as e: 
        print(f"ERROR: AI Service ({error_context}) - Data structure validation failed or invalid JSON. Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{error_context} data from Gemini API has incorrect structure or is invalid JSON: {e}"
        )
    except HTTPException as he: 
        raise he
    except Exception as e:
        print(f"ERROR: AI Service ({error_context}) - Error during Gemini API call: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while generating {error_context} with Gemini: {str(e)}"
        )
# --- Flashcard Generation using Gemini ---
async def generate_flashcards_from_text(text_to_generate_from: str) -> List[Dict[str, str]]:
    if not text_to_generate_from or len(text_to_generate_from.strip()) < 10:
        print("WARN: AI Service - Input text for flashcards is too short.")
        return []

    prompt = f"""From the following text, generate a concise list of flashcards focusing on the most essential concepts.

Guidelines:
- Output only a *JSON array* (no code block, no markdown, no extra text).
- Each flashcard must be a JSON object with:
  - "front": a question or term
  - "back": the correct answer or explanation
- For short text (under 300 words), return only 3 flashcards.
- For long text (300+ words), return a *maximum of 5 flashcards*.
- Prioritize uniqueness, depth, and relevance of the concepts.

Only output valid JSON, no markdown formatting or introductory/explanatory text.

Text to process:
---
{text_to_generate_from}
---
"""
    return await _call_gemini_for_json_list(prompt, "flashcards")


# --- Study Notes Generation (from Topic ID) ---

async def generate_study_notes_from_topic(
    db: AsyncIOMotorDatabase,
    topic_id_str: str,
    user_id: ObjectId
) -> str:
    """
    Fetches topic content from the DB and generates study notes.
    This function is called by the router.
    """
    try:
        topic_oid = ObjectId(topic_id_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Topic ID format."
        )

    # 1. Fetch the topic
    topic_doc = await db[BOOK_TOPICS_COLLECTION].find_one({"_id": topic_oid})
    if not topic_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found."
        )
    
    topic = BookTopicInDB(**topic_doc)

    # 2. Verify user ownership by checking the parent book
    book_doc = await db["books"].find_one(
        {"_id": topic.book_id, "user_id": user_id}
    )
    if not book_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book for this topic not found or access denied."
        )

    # 3. If ownership is verified, generate notes from the topic's content
    if not topic.content or len(topic.content.strip()) < 20:
        return "The selected topic content is too short to generate study notes."
        
    return await generate_study_notes_from_text(topic.content)


# --- Study Notes Generation using Gemini ---
async def generate_study_notes_from_text(text_to_generate_from: str) -> str:
    if not text_to_generate_from or len(text_to_generate_from.strip()) < 20:
        print("WARN: AI Service - Input text for study notes is too short.")
        return "Input text is too short to generate effective study notes."

    # <<< (NEW, CLEANER MARKDOWN PROMPT) >>>
    prompt = f"""
You are an expert academic instructor. 
Generate **comprehensive, well-structured, deeply detailed study notes** from the input text.

## OUTPUT FORMAT RULES (STRICT MARKDOWN)
- Use standard Markdown headers (`#`, `##`, `###`).
- **DO NOT** write "H1", "H2", "H3", "Title", or "Overview" as labels inside the text unless they are the actual headers.
- **DO NOT** number the sections (e.g., avoid "1. Overview"). Use headers instead.

## STRUCTURE

# [Create an Academic Title Here]

## Overview
[Write 4–6 sentences explaining the text's significance and themes]

## Key Concepts 
- [Concept 1]
- [Concept 2]

## Detailed Notes
(Structure the body using clear Markdown headers)

### [Main Idea 1]
- Full explanation...

#### [Sub-point or Component]
- Details...

### [Main Idea 2]
...

## Conclusion
- [Summary point 1]
...

## WRITING STYLE
- Use academic but simple language.
- No fluff.
- No repeated sentences.
- Rewrite everything clearly.
- Output all content in **one markdown block**.

---

### TEXT TO PROCESS:
{text_to_generate_from}

---
"""
    # <<< (END OF NEW PROMPT) >>>

    if not GOOGLE_API_KEY or not GEMINI_MODEL_NAME:
        print("ERROR: AI Service (Study Notes) - API Key or Model Name is not configured.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Study notes generation service is not configured (API Key or Model Name missing)."
        )

    raw_generated_text_notes = ""

    try:
        print(f"INFO: AI Service (Study Notes) - Calling Gemini API ({GEMINI_MODEL_NAME}).")
        
        if not gemini_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gemini client is not initialized."
            )
        
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.5,
                "max_output_tokens": 4096
            }
        )

        if not response.parts:
            print(f"ERROR: AI Service (Study Notes) - Gemini API response has no parts. Full response: {response}")
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Gemini API call blocked for Study Notes: {response.prompt_feedback.block_reason_message}"
                )
            return "The AI could not generate study notes (empty response parts)."

        raw_generated_text_notes = (response.text or "").strip()
        print(f"DEBUG: AI Service (Study Notes) - Gemini API Raw Response Text: {raw_generated_text_notes}")

        if not raw_generated_text_notes:
            print("ERROR: AI Service (Study Notes) - Gemini API returned empty content.")
            return "The AI could not generate study notes from the selected text."

        return raw_generated_text_notes
    except HTTPException as he: 
        raise he
    except Exception as e:
        print(f"ERROR: AI Service (Study Notes) - Error during Gemini API call: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while generating study notes with Gemini: {str(e)}"
        )

# --- Groq Llama3 Configuration for RAG Chat ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found in environment. AI Mentor feature will not work.")
    chat_model = None
else:
    try:
        chat_model = ChatGroq(temperature=0, model="llama-3.3-70b-versatile", api_key=SecretStr(GROQ_API_KEY))
        print("INFO: Groq Llama3 chat model loaded successfully.")
    except Exception as e:
        print(f"ERROR: Failed to load Groq chat model: {e}")
        chat_model = None

# =========================================================================
# --- RAG CHAT FOR AI MENTOR (Module 8) ---
# =========================================================================

async def get_rag_answer(
    book_id: str, 
    query: str, 
    user_id: ObjectId,
    db: AsyncIOMotorDatabase
) -> ChatResponse:
    """
    Handles a user's query using the RAG pipeline for a specific book.
    """
    if not chat_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Mentor service is currently unavailable (Chat model not loaded)."
        )

    # 1. Retrieve relevant context from the vector store
    # This is a synchronous call, but FastAPI will run it in a thread pool
    relevant_docs = vector_service.search_in_vector_store(book_id, query)

    if not relevant_docs:
        # If no context is found, provide a graceful fallback response
        return ChatResponse(
            answer="I couldn't find any information about that in this book. Please try rephrasing your question or asking something else.",
            sources=[]
        )

    # 2. Format the retrieved documents into a context string
    context_string = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])
    source_chunks = [doc.page_content for doc in relevant_docs]

    # 3. Fetch user's subject profile for personalization
    personalization_instructions = ""
    try:
        # Get the book's subject
        book_doc = await db["books"].find_one({"_id": ObjectId(book_id)})
        if book_doc and book_doc.get("subject"):
            subject = book_doc["subject"]
            
            # Fetch user's subject profile
            subject_profile = await db["subject_profiles"].find_one({
                "user_id": user_id,
                "subject": subject
            })
            
            if subject_profile:
                level = subject_profile.get("level", "intermediate")
                study_style = subject_profile.get("study_style", "mixed")
                study_pace = subject_profile.get("study_pace", "moderate")
                
                # Build personalization instructions based on level
                if level == "beginner":
                    personalization_instructions = """
**Teaching Style for Beginner:**
- Use simple, clear language without technical jargon
- Explain concepts step-by-step
- Provide analogies and real-world examples
- Define any technical terms you must use
- Break down complex ideas into smaller parts
"""
                elif level == "advanced":
                    personalization_instructions = """
**Teaching Style for Advanced Learner:**
- Use technical language appropriately
- Be concise and direct
- Focus on deeper concepts and nuances
- Assume foundational knowledge
- Provide detailed analysis
"""
                else:  # intermediate
                    personalization_instructions = """
**Teaching Style for Intermediate Learner:**
- Balance technical depth with clarity
- Mix theory with practical examples
- Build on foundational concepts
- Introduce some technical terminology with brief explanations
"""
                
                # Add study style preferences
                if study_style == "visual":
                    personalization_instructions += "\n- Use descriptive language and analogies that help visualize concepts\n- Suggest how diagrams or charts might represent the information"
                elif study_style == "kinesthetic":
                    personalization_instructions += "\n- Emphasize practical applications and real-world examples\n- Suggest hands-on ways to apply the concepts"
                elif study_style == "reading_writing":
                    personalization_instructions += "\n- Use well-structured text with clear bullet points\n- Organize information hierarchically"
                
    except Exception as e:
        print(f"INFO: Could not fetch subject profile for personalization: {e}")
        # Continue without personalization if profile fetch fails

    # 3.2 Fetch user's daily mood to enhance teaching adaptation
    mood_instructions = ""
    user_mood = None
    try:
        from services import user_service
        from datetime import date
        
        today_str = datetime.utcnow().date().isoformat()
        user = await user_service.get_user_by_id(db, user_id)
        
        if user and user.mood_logs:
            # Find today's mood
            for mood_log in user.mood_logs:
                if mood_log.date == today_str:
                    user_mood = mood_log.mood
                    break
            
            if user_mood:
                # Generate mood-specific teaching instructions
                mood_map = {
                    "confused": """
**Student's Current Mood: Confused 😕**
- The student is feeling confused, so break down concepts into very simple steps
- Use clear examples and analogies
- Check for understanding frequently
- Be patient and encouraging
- Avoid overwhelming with too much information at once
""",
                    "frustrated": """
**Student's Current Mood: Frustrated 😤**
- The student is frustrated, so be extra patient and supportive
- Acknowledge the difficulty and normalize struggle
- Offer alternative explanations or approaches
- Keep responses concise and actionable
- Use encouragement and positive reinforcement
""",
                    "stressed": """
**Student's Current Mood: Stressed 😰**
- The student is stressed, so keep your tone calm and reassuring
- Simplify explanations and avoid adding complexity
- Focus on one concept at a time
- Offer study strategies to reduce overwhelm
- Be brief and clear
""",
                    "motivated": """
**Student's Current Mood: Motivated 💪**
- The student is motivated, so feel free to challenge them appropriately
- Provide deeper insights and connections
- Encourage exploration and curiosity
- Suggest additional topics or extensions
- Match their energy with enthusiasm
""",
                    "engaged": """
**Student's Current Mood: Engaged 😊**
- The student is engaged and ready to learn
- Provide balanced, clear explanations
- Encourage active thinking with questions
- Build on their interest with interesting details
- Maintain good momentum
""",
                    "bored": """
**Student's Current Mood: Bored 😑**
- The student is bored, so make the content more engaging
- Use interesting examples and real-world applications
- Vary your explanation style
- Inject some enthusiasm and energy
- Connect to relevant, practical uses
""",
                    "neutral": """
**Student's Current Mood: Neutral 😐**
- The student has a neutral mood, so maintain a balanced approach
- Provide clear, organized information
- Use standard teaching strategies
- Adapt based on their responses
""",
                    "confident": """
**Student's Current Mood: Confident 😎**
- The student is feeling confident
- You can use more technical language where appropriate
- Provide comprehensive explanations
- Challenge them to think critically
- Encourage them to make connections
"""
                }
                
                mood_instructions = mood_map.get(user_mood, "")
                print(f"INFO: User's daily mood: {user_mood}")
                
    except Exception as e:
        print(f"INFO: Could not fetch user mood: {e}")
        # Continue without mood-based personalization

    # 3.5 Analyze conversation sentiment to adapt teaching style emotionally
    emotion_instructions = ""
    detected_emotion = "neutral"
    emotion_confidence = 0.0
    
    try:
        # Get or create conversation to get conversation_id
        book_id_obj = ObjectId(book_id)
        conversation = await ai_mentor_chat_service.get_or_create_ai_conversation(
            db, user_id, book_id_obj
        )
        
        # Analyze sentiment from conversation history
        detected_emotion, emotion_confidence = await sentiment_analysis_service.analyze_conversation_sentiment(
            db, conversation.id
        )
        
        # Get emotion-specific teaching instructions
        emotion_instructions = sentiment_analysis_service.get_emotion_teaching_style(detected_emotion)
        
        print(f"INFO: Detected student emotion: {detected_emotion} (confidence: {emotion_confidence:.2f})")
        
    except Exception as e:
        print(f"WARNING: Could not analyze sentiment, using neutral: {e}")
        # Continue with neutral emotion if sentiment analysis fails

    # 4. Define the prompt template with personalization, mood, AND emotion-aware teaching
    template = """

    You are an expert AI assistant, the 'Book Mentor'. Your primary goal is to help the student learn effectively by adapting to their emotional state and daily mood.

{personalization}

{mood_context}

{emotion_style}

    🚨 **CRITICAL INSTRUCTION - YOU MUST FOLLOW THIS:**
    - STRICTLY FOLLOW the word limits and teaching strategies specified above
    - ADAPT your teaching based on the student's CURRENT MOOD (logged today) and conversation sentiment
    - If the student is confused/stressed/frustrated/bored: Keep response VERY SHORT (under 100 words)
    - DO NOT write long paragraphs when student needs simplicity
    - ACTUALLY IMPLEMENT the emotional adaptations - don't just acknowledge them
    - Your response LENGTH and COMPLEXITY must match the student's emotional state

    **Content Instructions:**
    1. Answer the QUESTION using ONLY the CONTEXT below
    2. If CONTEXT is incomplete, give a brief partial answer from what's available
    3. Do NOT use external knowledge

    CONTEXT:
    {context}

    QUESTION:
    {question}

    ANSWER (Follow the word limit and emotional teaching style requirements above):
    """
    prompt = ChatPromptTemplate.from_template(template)
    
    # 5. Create and invoke the RAG chain with emotion-aware teaching
    try:
        rag_chain = (
            {
                "context": lambda x: context_string, 
                "question": RunnablePassthrough(), 
                "personalization": lambda x: personalization_instructions,
                "mood_context": lambda x: mood_instructions,
                "emotion_style": lambda x: emotion_instructions
            }
            | prompt
            | chat_model
            | StrOutputParser()
        )
        
        # We pass the original query to the chain
        answer = rag_chain.invoke(query)
        
        # --- Save chat history to database with detected emotion ---
        try:
            # Convert book_id to ObjectId (already done above for sentiment analysis)
            # book_id_obj = ObjectId(book_id)  # Already exists from sentiment analysis
            
            # Get or create the AI Mentor conversation (already done above)
            # conversation = await ai_mentor_chat_service.get_or_create_ai_conversation(
            #     db, user_id, book_id_obj
            # )
            # Reuse the conversation object from sentiment analysis step
            
            # Save user's question with detected emotion
            user_message = await ai_mentor_chat_service.save_ai_mentor_message(
                db=db,
                conversation_id=conversation.id,
                user_id=user_id,
                book_id=book_id_obj,
                sender_type="user",
                content=query,
                sources=None
            )
            
            # Update user message with detected emotion and sentiment score
            if user_message:
                await sentiment_analysis_service.update_message_emotion(
                    db=db,
                    message_id=user_message.id,
                    emotion=detected_emotion,
                    sentiment_score=emotion_confidence
                )
            
            # Save AI's response (no emotion for AI messages)
            await ai_mentor_chat_service.save_ai_mentor_message(
                db=db,
                conversation_id=conversation.id,
                user_id=user_id,
                book_id=book_id_obj,
                sender_type="ai",
                content=answer,
                sources=source_chunks
            )
            
            print(f"INFO: AI Mentor chat history saved with emotion: {detected_emotion}")
        except Exception as e:
            # Don't fail the request if history saving fails
            print(f"WARNING: Failed to save AI Mentor chat history: {e}")
        
        return ChatResponse(answer=answer, sources=source_chunks)

    except Exception as e:
        print(f"ERROR: AI Service (RAG Chain) - An error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the chat response."
        )

# =========================================================================
# --- DIAGNOSTIC QUIZ GENERATION & EVALUATION ---
# =========================================================================

# Diagnostic Quiz Methods to be added to ai_service.py

import json
from typing import List, Dict, Any
from fastapi import HTTPException, status

async def generate_diagnostic_quiz(gemini_client, GEMINI_MODEL_NAME, subject: str) -> List[Dict[str, Any]]:
    """
    Generate 5 subject-specific diagnostic questions using Gemini API.
    
    Args:
        subject: The subject name (e.g., "Data Structures", "Calculus")
    
    Returns:
        List of question dictionaries
    """
    if not gemini_client or not GEMINI_MODEL_NAME:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API is not configured (API Key or Model Name missing)."
        )
    
    prompt = f"""You are an educational assessment expert. Generate EXACTLY 5 diagnostic multiple-choice questions for the subject: "{subject}".

CRITICAL REQUIREMENTS:
1. Questions MUST be strictly related to {subject}
2. NO generic or motivational questions
3. Questions should assess understanding at different difficulty levels (basic, intermediate, advanced)
4. Each question must have 4 options (A, B, C, D)
5. Options should be plausible and realistic

RESPONSE FORMAT (JSON ONLY):
Return ONLY a JSON array with this EXACT structure:
[
  {{
    "question": "Question text here?",
    "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"]
  }},
  ...
]

EXAMPLE for "Data Structures":
[
  {{
    "question": "What is the time complexity of accessing an element in an array by index?",
    "options": ["A) O(1)", "B) O(n)", "C) O(log n)", "D) O(n^2)"]
  }},
  {{
    "question": "Which data structure uses LIFO (Last In First Out) principle?",
    "options": ["A) Queue", "B) Stack", "C) Tree", "D) Graph"]
  }}
]

Generate 5 questions for: {subject}
Return ONLY the JSON array, no explanations."""

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.7,
                "max_output_tokens": 2048
            }
        )

        if not response.parts:
            print(f"ERROR: AI Service (Diagnostic Quiz) - Gemini API response has no parts.")
            return []

        raw_text = (response.text or "").strip()
        
        # Clean markdown formatting
        cleaned_text = raw_text
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[len("```json"):]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[len("```"):]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-len("```")]
        cleaned_text = cleaned_text.strip()
        
        # Extract JSON array
        json_start = cleaned_text.find('[')
        json_end = cleaned_text.rfind(']')
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_string = cleaned_text[json_start:json_end+1]
        else:
            json_string = cleaned_text
        
        parsed_data = json.loads(json_string)
        
        if not isinstance(parsed_data, list):
            raise ValueError("Parsed data is not a list.")
        
        return parsed_data

    except json.JSONDecodeError as e:
        print(f"ERROR: AI Service (Diagnostic Quiz) - JSON decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse diagnostic quiz from Gemini API."
        )
    except Exception as e:
        print(f"ERROR: AI Service (Diagnostic Quiz) - Unexpected error: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating diagnostic quiz: {str(e)}"
        )


async def evaluate_diagnostic_quiz(gemini_client, GEMINI_MODEL_NAME, subject: str, answers: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Evaluate user's answers and determine learning profile.
    
    Args:
        subject: The subject name
        answers: List of {"question": "...", "user_answer": "..."}
    
    Returns:
        Dict with profile recommendations
    """
    if not gemini_client or not GEMINI_MODEL_NAME:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API is not configured."
        )
    
    # Format answers for the prompt
    answers_text = "\n\n".join([
        f"Q: {ans['question']}\nUser's Answer: {ans['user_answer']}"
        for ans in answers
    ])
    
    prompt = f"""You are an educational assessment expert. Analyze the following quiz responses for the subject: "{subject}".

USER'S RESPONSES:
{answers_text}

YOUR TASK:
1. Evaluate the correctness and depth of understanding shown in the answers
2. Classify the learner's level: beginner, intermediate, or advanced
3. Recommend appropriate learning parameters

CLASSIFICATION CRITERIA:
- beginner: 0-2 correct answers OR shallow understanding
- intermediate: 3 correct answers OR moderate understanding
- advanced: 4-5 correct answers OR deep understanding

RECOMMENDATIONS:
- study_pace: slow (needs more time), moderate (average pace), fast (quick learner)
- study_style: theory-focused, practice-focused, mixed, visual, problem-solving based
- break_preference: Suggest break interval (e.g., "10 min after 45 min", "5 min after 30 min")

RESPONSE FORMAT (JSON ONLY):
Return ONLY this JSON structure, no explanations:
{{
  "level": "beginner|intermediate|advanced",
  "study_pace": "slow|moderate|fast",
  "study_style": "theory-focused|practice-focused|mixed|visual|problem-solving based",
  "break_preference": "X min after Y min"
}}

Analyze and return the JSON:"""

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.5,
                "max_output_tokens": 512
            }
        )

        if not response.parts:
            print(f"ERROR: AI Service (Diagnostic Evaluation) - No response parts")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get evaluation from Gemini API."
            )

        raw_text = (response.text or "").strip()
        
        # Clean markdown formatting
        cleaned_text = raw_text
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[len("```json"):]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[len("```"):]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-len("```")]
        cleaned_text = cleaned_text.strip()
        
        # Extract JSON object
        json_start = cleaned_text.find('{')
        json_end = cleaned_text.rfind('}')
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_string = cleaned_text[json_start:json_end+1]
        else:
            json_string = cleaned_text
        
        result = json.loads(json_string)
        
        # Validate required fields
        required_fields = ["level", "study_pace", "study_style", "break_preference"]
        if not all(field in result for field in required_fields):
            raise ValueError(f"Missing required fields in evaluation result")
        
        return result

    except json.JSONDecodeError as e:
        print(f"ERROR: AI Service (Diagnostic Evaluation) - JSON decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse evaluation result from Gemini API."
        )
    except Exception as e:
        print(f"ERROR: AI Service (Diagnostic Evaluation) - Unexpected error: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating diagnostic quiz: {str(e)}"
        )

