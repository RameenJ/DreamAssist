from . import auth_router
from . import book_router
from . import ai_router
from . import subject_router
from . import user_router
from . import progress_router
from . import recommendation_router
from . import forum_router
from . import study_groups_router
from . import chat_router
from . import diagnostic_router
from . import subject_profile_router
from . import planner_router
from . import goal_based_planning_router
from . import conflict_detection_router
from . import prerequisite_router

__all__ = [
    "auth_router",
    "book_router",
    "ai_router",
    # "category_router",  # Removed - categories replaced with subjects
    "subject_router",
    "user_router",
    "progress_router",
    "recommendation_router",
    "forum_router",
    "study_groups_router",
    "chat_router",
    "diagnostic_router",
    "subject_profile_router",
    "planner_router",
    "goal_based_planning_router",
    "conflict_detection_router",
    "prerequisite_router",
]
