from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

# --- Generic Charting Models ---

class ChartDataPoint(BaseModel):
    """
    A generic data point for bar and line charts.
    'label' is the X-axis, 'value' is the Y-axis.
    """
    label: str
    value: float

class PieChartDataPoint(BaseModel):
    """
    A data point for pie/donut charts.
    'name' is the category, 'value' is the count.
    """
    name: str
    value: int

# --- Global Progress (for /progress page) ---

class GlobalStats(BaseModel):
    """
    High-level stat cards for the global progress page.
    """
    total_quizzes: int
    average_score: float
    weakest_subject: Optional[str] = None # The book_name with the lowest avg score
    
    # Activity stats
    total_ai_chats: int = 0
    total_summaries: int = 0
    total_flashcards: int = 0
    total_study_notes: int = 0
    total_qna: int = 0
    total_quiz_generated: int = 0

class GlobalProgressResponse(BaseModel):
    """
    The all-in-one response model for the global progress page.
    """
    stats: GlobalStats
    score_over_time: List[ChartDataPoint]       # For the Line Chart
    performance_by_subject: List[ChartDataPoint] # For the Bar Chart
    grade_distribution: List[PieChartDataPoint] # For the Pie Chart

# --- Per-Book Progress (for /books/[bookID] page) ---

TopicStatusType = Literal["completed", "failed", "not_attempted"]

class TopicStatus(BaseModel):
    """
    A single item in the "Topic Completion Checklist".
    """
    topic_title: str
    status: TopicStatusType
    score: Optional[float] = None # e.g., 0.85 or 0.45

class BookProgressResponse(BaseModel):
    """
    The all-in-one response model for the per-book progress tab.
    """
    completion_status: List[TopicStatus]        # For the Checklist
    performance_by_topic: List[ChartDataPoint]  # For the Bar Chart