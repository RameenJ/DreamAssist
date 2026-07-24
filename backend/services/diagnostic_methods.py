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
    
    prompt = f"""Analyze quiz responses for "{subject}" and return a JSON object.

Responses: {answers_text}

Classify level based on correctness:
- beginner: 0-2 correct
- intermediate: 3 correct  
- advanced: 4-5 correct

Return this exact JSON structure:
{{
  "level": "beginner",
  "study_pace": "moderate",
  "study_style": "mixed",
  "break_preference": "5 min after 30 min"
}}

Valid values:
level: beginner, intermediate, advanced
study_pace: slow, moderate, fast
study_style: theory-focused, practice-focused, mixed, visual, problem-solving
break_preference: any text"""
    raw_text = None
    
    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
            config={
                "temperature": 0.3,
                "max_output_tokens": 256,
                "response_mime_type": "application/json"
            }
        )

        if not response.parts:
            print(f"ERROR: AI Service (Diagnostic Evaluation) - No response parts")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get evaluation from Gemini API."
            )

        raw_text = (response.text or "").strip()
        print(f"DEBUG: Gemini raw evaluation response:\n{raw_text}")
        
        # Since we use response_mime_type="application/json", Gemini returns clean JSON
        result = json.loads(raw_text)
        
        print(f"DEBUG: Parsed evaluation: {result}")
        
        # Validate required fields
        required_fields = ["level", "study_pace", "study_style", "break_preference"]
        if not all(field in result for field in required_fields):
            raise ValueError(f"Missing required fields in evaluation result")
        
        return result

    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to decode Gemini evaluation response as JSON: {e}")
        print(f"ERROR: Raw response was: {raw_text if 'raw_text' in locals() else 'N/A'}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse evaluation result from Gemini API. Error: {str(e)}"
        )
    except Exception as e:
        print(f"ERROR: AI Service (Diagnostic Evaluation) - Unexpected error: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating diagnostic quiz: {str(e)}"
        )
