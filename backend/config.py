"""
Lecturify AI - Configuration
All paths and settings for local development.
"""
import os

# Base paths (relative to backend directory)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Dataset path - auto-detected at startup
# Priority: lecturify_ai/datasets, then parent/datasets/datasets (e.g. Project/datasets/datasets)
DATASET_PATH = os.path.join(PROJECT_ROOT, "datasets")
_alt_path = os.path.join(os.path.dirname(PROJECT_ROOT), "datasets", "datasets")
if not os.path.exists(DATASET_PATH) and os.path.exists(_alt_path):
    DATASET_PATH = _alt_path

# Storage paths - all local
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "storage", "uploaded_files")
MODELS_FOLDER = os.path.join(BASE_DIR, "models")
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "storage", "processed_outputs")

# Ensure directories exist
for folder in [UPLOAD_FOLDER, MODELS_FOLDER, OUTPUT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Allowed file upload extensions
ALLOWED_EXTENSIONS = {
    "audio": ["mp3", "wav", "m4a", "ogg", "flac"],
    "video": ["mp4", "avi", "mkv", "mov", "webm", "mpeg", "mpg"],
    "document": ["pdf", "docx", "doc", "txt", "pptx", "ppt"],
    "image": ["png", "jpg", "jpeg", "bmp", "tiff"],
}

# Flask
SECRET_KEY = os.environ.get("LECTURIFY_SECRET_KEY", "lecturify-dev-secret-key-change-in-prod")
DEBUG = True

# MongoDB - local connection
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB = "lecturify_ai"

# JWT
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "lecturify-jwt-secret")
JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours

# AI Model settings
WHISPER_MODEL = "base"  # tiny, base, small, medium, large
WHISPER_LANGUAGE = None  # None = auto-detect (multilingual)

# Bloom taxonomy levels (used in this project)
BLOOM_LEVELS = ["Remember", "Understand", "Apply", "Analyze"]
