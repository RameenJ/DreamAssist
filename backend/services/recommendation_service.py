import os
import json
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from langchain_groq import ChatGroq
from pydantic import SecretStr
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic.v1 import BaseModel as PydanticV1BaseModel, Field as PydanticV1Field, constr, conlist

# Import the main Pydantic schemas from our models
from models.ai_schemas import (
    AIRecommendationResponse, 
    AIStudyRecommendation, 
    RecommendationPriority, 
    RecommendedAction
)
from models.progress_schemas import ChartDataPoint # We get this from progress_service

# --- Groq Llama3 Configuration (Copied from ai_service.py) ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found in environment. Recommendation feature will not work.")
    chat_model = None
else:
    try:
        # Using a slightly higher temperature for more creative recommendations
        chat_model = ChatGroq(temperature=0.4, model="llama-3.3-70b-versatile", api_key=SecretStr(GROQ_API_KEY)) # Upped temperature slightly
        print("INFO: Groq Llama3 chat model loaded successfully for Recommendation Service.")
    except Exception as e:
        print(f"ERROR: Failed to load Groq chat model for Recommendation Service: {e}")
        chat_model = None

# --- Pydantic V1 Models for LangChain Parser ---
# ... (this part is unchanged)
class AIStudyRecommendation_v1(PydanticV1BaseModel):
    priority: RecommendationPriority
    topic_name: str = PydanticV1Field(..., min_length=1)
    score: float
    action: RecommendedAction
    recommendation_text: str = PydanticV1Field(..., min_length=10)

class AIRecommendationResponse_v1(PydanticV1BaseModel):
    recommendations: List[AIStudyRecommendation_v1] = PydanticV1Field(..., min_items=1, max_items=3)
    strength_message: Optional[str] = PydanticV1Field(None, description="An encouraging message about the user's strongest topic")
# --- End of Pydantic V1 Models ---


async def get_study_recommendations_from_llm(
    performance_data: List[ChartDataPoint]
) -> AIRecommendationResponse:
    """
    Uses the Groq LLM to generate study recommendations from quiz performance data.
    """
    if not chat_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Recommendation service is currently unavailable (Chat model not loaded)."
        )

    if not performance_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate recommendations with no performance data."
        )

    performance_dict = {item.label: round(item.value, 1) for item in performance_data}
    performance_json = json.dumps(performance_dict)
    
    # This string is the source of our tool list
    available_tools_enum = ", ".join([
        f"'{action}'" for action in RecommendedAction.__args__
    ])

    # Initialize the JSON parser with our Pydantic V1 schema
    parser = JsonOutputParser(pydantic_object=AIRecommendationResponse_v1)

    # =====================================================================
    # --- THIS IS THE NEW, UPGRADED PROMPT ---
    # =====================================================================
    template = """
    You are an expert, encouraging, and practical AI study coach for the 'Learn-Ease' platform.
    Your goal is to provide a highly personalized, varied, and actionable study plan based on a student's quiz performance.

    [STUDENT PERFORMANCE DATA (Topic: Score %)]:
    {performance_json}

    [AVAILABLE_TOOLS]:
    - `AI_MENTOR`: Best for complex, "why" questions or deep conceptual confusion.
    - `VIEW_SUMMARY`: Best for getting a high-level overview of a broad topic.
    - `REVIEW_NOTES`: Best for re-learning the specific details of a topic.
    - `STUDY_FLASHCARDS`: Best for memorizing key terms, definitions, and facts.
    - `VIEW_QA_PAIRS`: Best for seeing examples of common questions and answers.
    - `TAKE_QUIZ`: Best for practicing and testing knowledge to find gaps.

    [YOUR TASK]:
    1.  Analyze the student's performance data.
    2.  Identify the **top 2-3 weakest topics** (scores below 60).
    3.  For EACH weak topic, assign a `priority` ('High' for scores < 45, 'Medium' for 45-60).
    4.  For EACH weak topic, choose the **single most appropriate tool** from [AVAILABLE_TOOLS].
        * **CRITICAL:** You MUST recommend **different tools** for each topic. Do NOT be repetitive.
        * *Hint:* If the score is very low (e.g., 15%), a foundational tool like `VIEW_SUMMARY` or `AI_MENTOR` is better. If the score is higher (e.g., 50%), a practice tool like `TAKE_QUIZ` or `STUDY_FLASHCARDS` is more appropriate.
    5.  Write a `recommendation_text` that is **specific, actionable, and encouraging**. 
        * **Bad:** "Use the AI Mentor."
        * **Good:** "Your score on 'Content Delivery' is low. Try asking the AI Mentor to 'explain what a CDN is in simple terms' to build a stronger foundation."
    6.  Identify the student's **single highest-scoring topic** (their "best effort").
    7.  Write an encouraging `strength_message` praising this topic. If their highest score is still low (e.g., < 60), acknowledge it as "a good starting point" or "your strongest area so far."
    8.  Return ONLY the JSON object matching the format.

    [JSON_FORMAT_INSTRUCTIONS]:
    {format_instructions}

    YOUR_JSON_RESPONSE:
    """
    # =====================================================================
    # --- END OF NEW PROMPT ---
    # =====================================================================
    
    prompt = ChatPromptTemplate.from_template(
        template,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # Create the chain
    chain = prompt | chat_model | parser

    try:
        # Invoke the chain
        response_data = await chain.ainvoke({
            "performance_json": performance_json
        })
        
        # Convert the v1-parsed data back to our main Pydantic v2 schemas
        return AIRecommendationResponse(**response_data)

    except Exception as e:
        print(f"ERROR: Recommendation Service - Failed to get LLM response or parse JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI recommendations."
        )
    
# (Add this to the end of backend/services/recommendation_service.py)

# Import the new schemas at the top of the file
from models.ai_schemas import (
    # ... your existing imports
    AIGlobalRecommendationResponse,
    AIGlobalStudyRecommendation,
    GlobalRecommendationAction
)
# Import the progress schema to get the type hint
from models.progress_schemas import GlobalProgressResponse

# We need a new Pydantic v1 model for the parser
class AIGlobalStudyRecommendation_v1(PydanticV1BaseModel):
    priority: RecommendationPriority
    action: GlobalRecommendationAction
    title: str = PydanticV1Field(..., min_length=5)
    recommendation_text: str = PydanticV1Field(..., min_length=10)

class AIGlobalRecommendationResponse_v1(PydanticV1BaseModel):
    recommendations: List[AIGlobalStudyRecommendation_v1] = PydanticV1Field(..., min_items=1, max_items=2)

# ... (rest of your file, including get_study_recommendations_from_llm) ...

# --- NEW FUNCTION FOR GLOBAL RECOMMENDATIONS ---

async def get_global_recommendations_from_llm(
    progress_data: GlobalProgressResponse
) -> AIGlobalRecommendationResponse:
    """
    Uses the Groq LLM to generate high-level global study recommendations.
    """
    if not chat_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Recommendation service is currently unavailable (Chat model not loaded)."
        )

    # Convert stats to a simple JSON string
    stats_json = progress_data.stats.model_dump_json()

    available_tools = [
        "REVIEW_WEAKEST_SUBJECT", "PRACTICE_NEW_SUBJECT",
        "VIEW_GLOBAL_PROGRESS", "TAKE_ANY_QUIZ"
    ]

    parser = JsonOutputParser(pydantic_object=AIGlobalRecommendationResponse_v1)

    template = """
    You are an expert, encouraging AI study coach. A student is looking at their global dashboard.
    Your goal is to provide 1-2 high-level, actionable recommendations based on their overall stats.

    [STUDENT'S GLOBAL STATS]:
    {stats_json}
    
    [AVAILABLE_ACTIONS]:
    - `REVIEW_WEAKEST_SUBJECT`: Recommend they focus on their weakest subject.
    - `PRACTICE_NEW_SUBJECT`: Recommend they try a new subject if their average is low (stuck) or high (bored).
    - `VIEW_GLOBAL_PROGRESS`: Recommend they review their full progress report.
    - `TAKE_ANY_QUIZ`: A general recommendation to keep practicing.

    [YOUR TASK]:
    1.  Analyze the student's stats.
    2.  If `average_score` is low (e.g., < 50) and `weakest_subject` exists, your **top priority** is to recommend `REVIEW_WEAKEST_SUBJECT`.
    3.  If `average_score` is high (e.g., > 75), recommend `PRACTICE_NEW_SUBJECT` to challenge them.
    4.  If `total_quizzes` is low (e.g., < 3), recommend `TAKE_ANY_QUIZ` to build up data.
    5.  Create a short, catchy `title` for the recommendation.
    6.  Write a `recommendation_text` that is encouraging and explains *why* you are suggesting this action.
    7.  Return 1 or 2 recommendations. Do NOT be repetitive.
    8.  Return ONLY the JSON object matching the format.

    [JSON_FORMAT_INSTRUCTIONS]:
    {format_instructions}

    YOUR_JSON_RESPONSE:
    """

    prompt = ChatPromptTemplate.from_template(
        template,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | chat_model | parser

    try:
        response_data = await chain.ainvoke({
            "stats_json": stats_json
        })
        return AIGlobalRecommendationResponse(**response_data)

    except Exception as e:
        print(f"ERROR: Global Recommendation Service - Failed to get LLM response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate global AI recommendations."
        )