import os
from dotenv import load_dotenv

dotenv_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    '.env'
)
load_dotenv(dotenv_path)


MONGO_DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_NAME = "dreamassist_db" # Or load from env if preferred

# CRITICAL: JWT_SECRET_KEY must be set via environment variable in production
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    import warnings
    warnings.warn("⚠️ WARNING: JWT_SECRET_KEY not set in environment variables. Using temporary key for development only.", stacklevel=2)
    JWT_SECRET_KEY = "dev_temporary_key_change_in_production"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BOOK_SUBPATH_FROM_ROOT = os.getenv("LOCAL_BOOK_UPLOAD_DIR_SUBPATH", "user-book-files/books")
TEXT_SUBPATH_FROM_ROOT = os.getenv("LOCAL_EXTRACTED_TEXT_DIR_SUBPATH", "user-book-files/extracted-texts")
VECTOR_STORE_SUBPATH_FROM_ROOT = os.getenv("LOCAL_VECTOR_STORE_DIR_SUBPATH", "user-book-files/vector-stores")

LOCAL_BOOK_UPLOAD_DIR = os.path.join(PROJECT_ROOT_DIR, BOOK_SUBPATH_FROM_ROOT)
LOCAL_EXTRACTED_TEXT_DIR = os.path.join(PROJECT_ROOT_DIR, TEXT_SUBPATH_FROM_ROOT)
LOCAL_VECTOR_STORE_DIR = os.path.join(PROJECT_ROOT_DIR, VECTOR_STORE_SUBPATH_FROM_ROOT) # <<< AND THIS

# Basic check
if not MONGO_DATABASE_URL:
    print("⚠️ WARNING: DATABASE_URL not found in .env file")
    
# print(f"DEBUG: Dotenv path used: {dotenv_path}")
# print(f"DEBUG: Project Root Dir: {PROJECT_ROOT_DIR}")
# print(f"DEBUG: Book Subpath from .env/default: {BOOK_SUBPATH_FROM_ROOT}")
# print(f"DEBUG: Text Subpath from .env/default: {TEXT_SUBPATH_FROM_ROOT}")
# print(f"DEBUG: Final Local Book Upload Dir: {LOCAL_BOOK_UPLOAD_DIR}")
# print(f"DEBUG: Final Local Extracted Text Dir: {LOCAL_EXTRACTED_TEXT_DIR}")