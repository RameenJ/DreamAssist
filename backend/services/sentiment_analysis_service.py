"""
Sentiment Analysis Service for AI Mentor chat using fine-tuned DistilBERT model.
Analyzes student emotional state to adapt teaching style.
"""

from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
from typing import Optional, List, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

# Emotion labels that the model can detect
EMOTION_LABELS = [
    "confused",
    "frustrated",
    "stressed",
    "motivated",
    "engaged",
    "bored",
    "neutral",
    "confident"
]

class SentimentAnalyzer:
    """Singleton class to load and use the sentiment analysis model."""
    
    _instance = None
    _model: Optional[AutoModelForSequenceClassification] = None
    _tokenizer: Optional[AutoTokenizer] = None
    _model_name = "rameenj711/tutor-emotion-model"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SentimentAnalyzer, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance
    
    def _load_model(self):
        """Load the DistilBERT model and tokenizer."""
        if self._model is None:
            print(f"Loading sentiment analysis model: {self._model_name}")
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
                self._model = AutoModelForSequenceClassification.from_pretrained(self._model_name)
                self._model.eval()  # Set to evaluation mode
                print("✅ Sentiment analysis model loaded successfully")
            except Exception as e:
                print(f"❌ Error loading sentiment analysis model: {e}")
                raise
    
    def predict_emotion(self, text: str) -> Tuple[str, float]:
        """
        Predict emotion from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Tuple of (emotion_label, confidence_score)
        """
        if self._model is None or self._tokenizer is None:
            return "neutral", 0.0
            
        try:
            # Tokenize input
            inputs = self._tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                padding=True,
                max_length=512
            )
            
            # Get model prediction
            with torch.no_grad():
                outputs = self._model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=1)
                confidence, pred_idx = torch.max(probs, dim=1)
                
            emotion_label = EMOTION_LABELS[int(pred_idx.item())]
            confidence_score = float(confidence.item())
            
            return emotion_label, confidence_score
            
        except Exception as e:
            print(f"Error predicting emotion: {e}")
            return "neutral", 0.0


# Global sentiment analyzer instance
_sentiment_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get or create the global sentiment analyzer instance."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer


async def analyze_conversation_sentiment(
    db: AsyncIOMotorDatabase,
    conversation_id: ObjectId
) -> Tuple[str, float]:
    """
    Analyze the emotional sentiment of all user messages in a conversation.
    
    Args:
        db: Database connection
        conversation_id: The conversation to analyze
        
    Returns:
        Tuple of (detected_emotion, confidence_score)
    """
    try:
        # Fetch all user messages from this conversation
        messages = await db.ai_mentor_messages.find({
            "conversation_id": conversation_id,
            "sender_type": "user"
        }).sort("created_at", 1).to_list(length=None)
        
        if not messages:
            return "neutral", 1.0
        
        # Combine all user messages
        combined_text = " ".join([msg["content"] for msg in messages])
        
        # If combined text is too short, return neutral
        if len(combined_text.strip()) < 10:
            return "neutral", 1.0
        
        # Get sentiment analyzer and predict
        analyzer = get_sentiment_analyzer()
        emotion, confidence = analyzer.predict_emotion(combined_text)
        
        print(f"Detected emotion: {emotion} (confidence: {confidence:.2f})")
        
        return emotion, confidence
        
    except Exception as e:
        print(f"Error analyzing conversation sentiment: {e}")
        return "neutral", 0.0


def get_emotion_teaching_style(emotion: str) -> str:
    """
    Get teaching style instructions based on detected emotion.
    
    EMOTION-TO-TEACHING MAPPING (Mobile-Optimized):
    - confused → VERY SHORT (80-100 words), simple language, ONE concept, analogies
    - frustrated → SHORT (100-120 words), encouraging, start with success, small steps
    - stressed → ULTRA SHORT (60-80 words), calming tone, ONE thing only, reassuring
    - bored → SHORT (80-100 words), hook attention, surprising facts, make relevant
    - neutral → MEDIUM (100-120 words), balanced, structured, clear
    - engaged → MEDIUM (100-130 words), interesting examples, maintain momentum
    - motivated → MEDIUM (110-140 words), challenging, deeper content, enthusiasm
    - confident → MEDIUM-LONG (130-160 words), technical depth, advanced concepts, challenge
    
    All limits designed for mobile reading - no one wants 250 words on their phone!
    
    Args:
        emotion: The detected emotion label
        
    Returns:
        Teaching style instructions for the AI tutor
    """
    emotion_styles = {
        "confused": """
🚨 CRITICAL: The student is CONFUSED. YOU MUST drastically simplify:

**MANDATORY REQUIREMENTS:**
1. Keep your ENTIRE response under 100 words (about 5-6 short sentences)
2. Explain ONLY ONE concept - ignore other topics in the question if needed
3. Use ZERO technical jargon - explain like they're 10 years old
4. Give ONE simple analogy or example (everyday things: cooking, sports, phone)
5. Break into 2-3 tiny steps maximum
6. End with: "Does this part make sense?"

**TONE:** Patient, simple, clear
**LENGTH:** SHORT - maximum 100 words total
**FORBIDDEN:** Long paragraphs, multiple concepts, technical terms, complex explanations
""",
        
        "frustrated": """
🚨 CRITICAL: The student is FRUSTRATED. YOU MUST be extra supportive:

**MANDATORY REQUIREMENTS:**
1. Keep response under 120 words (about 6-7 sentences)
2. Start with ONE encouraging sentence acknowledging their effort
3. Explain ONE simple concept or ONE small step they can take
4. Use simple, warm language - be their supportive friend
5. End with encouragement: "You're doing great, let's tackle this together"
6. NO overwhelming information dumps

**TONE:** Warm, encouraging, patient, supportive
**LENGTH:** SHORT - maximum 120 words
**FORBIDDEN:** Long explanations, multiple topics, pressure, complex concepts
""",
        
        "stressed": """
🚨 CRITICAL: The student is STRESSED/OVERWHELMED. YOU MUST keep it minimal:

**MANDATORY REQUIREMENTS:**
1. Keep response under 80 words (about 4-5 sentences) - THIS IS CRITICAL
2. Focus on ONE single concept ONLY - ignore everything else
3. Use calming, reassuring tone: "Let's take this one step at a time"
4. Give ONE simple point with ONE quick example
5. End with: "Let's pause here. Ready to continue?"
6. Absolutely NO information overload

**TONE:** Calm, reassuring, gentle, slow-paced
**LENGTH:** VERY SHORT - maximum 80 words
**FORBIDDEN:** Long explanations, multiple concepts, any complexity, walls of text
""",
        
        "motivated": """
✅ GOOD: The student is MOTIVATED and eager! Give them more:

**MANDATORY REQUIREMENTS:**
1. Response length: 110-140 words (give more depth, but keep readable)
2. Match their enthusiasm - use exciting, energetic tone
3. Go deeper - explain key concepts and connections
4. Challenge them with a thought-provoking question
5. Connect to real-world applications
6. Add fascinating details: "Interestingly..." or "Here's something cool..."
7. Move at a faster pace - they can keep up

**TONE:** Enthusiastic, dynamic, challenging, inspiring
**LENGTH:** Medium (110-140 words) - enthusiastic but readable
**STYLE:** Deeper content, challenging, connect to bigger picture
**FORBIDDEN:** Being too basic, holding back content, being boring
""",
        
        "engaged": """
✅ GOOD: The student is ENGAGED and interested! Keep momentum:

**MANDATORY REQUIREMENTS:**
1. Response length: 100-130 words (keep them engaged, not overwhelmed)
2. Maintain energy with enthusiastic, dynamic tone
3. Provide interesting real-world connections and examples
4. Ask an interactive question to deepen engagement
5. Add fascinating related details that spark curiosity
6. Build on what's capturing their attention
7. Use vivid, engaging language

**TONE:** Enthusiastic, engaging, dynamic, interesting
**LENGTH:** Medium (100-130 words) - engaging but digestible
**STYLE:** Interesting examples, real-world connections, build curiosity
**FORBIDDEN:** Being dry or formal, losing momentum, boring explanations
""",
        
        "bored": """
⚠️ ALERT: The student is BORED! Need to capture attention:

**MANDATORY REQUIREMENTS:**
1. Response length: 80-100 words (short and punchy!)
2. START with a surprising fact, question, or interesting hook
3. Use compelling real-world examples they can relate to
4. Make it immediately relevant: "Here's why this matters..."
5. Use storytelling or unexpected angles
6. Connect to their life, technology, current events
7. End with an intriguing question

**TONE:** Engaging, surprising, relevant, creative
**LENGTH:** Short (80-100 words) - grab and keep attention
**STYLE:** Hook attention FIRST, make it relevant and surprising
**FORBIDDEN:** Dry facts, monotonous tone, irrelevant content, long paragraphs
""",
        
        "neutral": """
➡️ NEUTRAL: The student is in a neutral state. Use balanced approach:

**MANDATORY REQUIREMENTS:**
1. Response length: 100-120 words (balanced, not too long)
2. Provide clear, well-structured explanations
3. Use friendly but professional tone
4. Include practical examples and applications
5. Organize with clear structure (logical flow)
6. Balance depth with accessibility
7. Check for understanding: "Does this help?"

**TONE:** Friendly, professional, clear, balanced
**LENGTH:** Medium (100-120 words) - balanced and readable
**STYLE:** Well-structured, clear explanations, practical examples
**FORBIDDEN:** Being too casual or too formal, confusing structure
""",
        
        "confident": """
💪 EXCELLENT: The student is CONFIDENT! Challenge them:

**MANDATORY REQUIREMENTS:**
1. Response length: 130-160 words (more depth, still mobile-friendly)
2. Provide in-depth, detailed explanations with technical depth
3. Introduce advanced concepts and nuances
4. Challenge with complex applications and deeper analysis
5. Assume strong foundational knowledge - use technical terms
6. Ask thought-provoking questions: "What if..." "Consider..."
7. Explore exceptions and deeper implications

**TONE:** Professional, technical, challenging, analytical
**LENGTH:** Medium-Long (130-160 words) - depth without overwhelming
**STYLE:** Technical depth, advanced concepts, challenge understanding
**FORBIDDEN:** Over-simplifying, being too basic, holding back complexity
"""
    }
    
    return emotion_styles.get(emotion, emotion_styles["neutral"])


async def update_message_emotion(
    db: AsyncIOMotorDatabase,
    message_id: ObjectId,
    emotion: str,
    sentiment_score: float
):
    """
    Update a message with detected emotion and sentiment score.
    
    Args:
        db: Database connection
        message_id: The message to update
        emotion: The detected emotion
        sentiment_score: The confidence score
    """
    try:
        await db.ai_mentor_messages.update_one(
            {"_id": message_id},
            {
                "$set": {
                    "user_emotion": emotion,
                    "sentiment_score": sentiment_score
                }
            }
        )
    except Exception as e:
        print(f"Error updating message emotion: {e}")
