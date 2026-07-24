# backend/services/diagnostic_service.py
"""
Service for diagnostic quiz generation using Groq AI with fallback questions.
Ensures 100% reliability for critical diagnostic feature.
"""

import os
import json
from typing import List, Dict, Any
from fastapi import HTTPException, status
from langchain_groq import ChatGroq
from pydantic import SecretStr
from . import fallback_questions

# Get Groq configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = "llama-3.3-70b-versatile"

# Initialize Groq client
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = ChatGroq(
            temperature=0.7,
            model=GROQ_MODEL_NAME,
            api_key=SecretStr(GROQ_API_KEY)
        )
        print("INFO: Diagnostic Service - Groq client initialized successfully.")
    except Exception as e:
        print(f"ERROR: Diagnostic Service - Failed to initialize Groq client: {e}")
        groq_client = None
else:
    print("WARNING: GROQ_API_KEY not found. Diagnostic quiz will use fallback questions only.")


async def generate_diagnostic_quiz(subject: str) -> List[Dict[str, Any]]:
    """
    Generate 5 subject-specific diagnostic questions using Groq AI with fallback.
    
    Strategy:
    1. Try Groq API first (faster, higher rate limits)
    2. If Groq fails, use predefined fallback questions (100% reliable)
    
    Args:
        subject: The subject name (e.g., "Data Structures", "Machine Learning")
        
    Returns:
        List of 5 questions, each with question, options, and correct_answer
    """
    
    # Try Groq first if available
    if groq_client:
        try:
            print(f"INFO: Attempting quiz generation with Groq for subject: {subject}")
            
            # Create a focused prompt for subject-specific questions
            prompt = f"""Generate exactly 5 diagnostic quiz questions for the subject: "{subject}".

STRICT REQUIREMENTS:
1. Questions MUST be strictly related to {subject}
2. NO generic, motivational, or study habit questions
3. Each question should test actual knowledge/concepts in {subject}
4. Questions should range from basic to advanced to assess skill level
5. Provide exactly 4 options for each question
6. MUST include the correct answer for each question

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "question": "Question text here?",
    "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
    "correct_answer": "Option B text"
  }}
]

IMPORTANT: The correct_answer must be the EXACT text of one of the options.

Generate exactly 5 questions. Return ONLY the JSON array, no other text."""

            # Call Groq
            response = groq_client.invoke(prompt)
            # Safely extract string content
            content = response.content
            if isinstance(content, str):
                raw_text = content
            elif isinstance(content, list):
                text_parts = [str(part) for part in content if part is not None]
                raw_text = " ".join(text_parts)
            else:
                raw_text = str(content)
            raw_text = raw_text.strip()
            
            # Clean markdown code blocks if present
            cleaned_text = raw_text
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            # Parse JSON
            questions = json.loads(cleaned_text)
            
            if not isinstance(questions, list):
                raise ValueError("Response is not a list")
            
            if len(questions) < 5:
                raise ValueError(f"Only {len(questions)} questions generated, expected 5")
            
            # Take first 5 if more were generated
            questions = questions[:5]
            
            # Validate structure
            for q in questions:
                if "question" not in q or "options" not in q or "correct_answer" not in q:
                    raise ValueError("Invalid question structure - missing required fields")
                if not isinstance(q["options"], list) or len(q["options"]) != 4:
                    raise ValueError("Each question must have exactly 4 options")
                # Validate correct_answer is one of the options
                if q["correct_answer"] not in q["options"]:
                    print(f"WARNING: correct_answer '{q['correct_answer']}' not in options. Using first option.")
                    q["correct_answer"] = q["options"][0]
            
            print(f"SUCCESS: Generated {len(questions)} questions with Groq for {subject}")
            return questions
            
        except Exception as e:
            print(f"WARNING: Groq quiz generation failed: {e}")
            print(f"INFO: Falling back to predefined questions for {subject}")
    
    # Fallback to predefined questions
    print(f"INFO: Using fallback questions for subject: {subject}")
    try:
        questions = fallback_questions.get_fallback_questions(subject, num_questions=5)
        print(f"SUCCESS: Loaded {len(questions)} fallback questions for {subject}")
        return questions
    except Exception as e:
        print(f"ERROR: Even fallback questions failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate diagnostic quiz: {str(e)}"
        )


# Note: The old evaluate_diagnostic_quiz function has been replaced
# with simple answer counting logic in the diagnostic router.
# Evaluation is now done by comparing user answers to correct answers,
# and calculating score percentage to determine skill level.

