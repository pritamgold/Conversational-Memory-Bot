# config.py
from pathlib import Path

# Image storage directory, one level up from this file (e.g., project/conversational_memory_bot/images/)
IMAGE_DIR = Path(__file__).resolve().parent / "images"

# Database storage directory (e.g., project/conversational_memory_bot/database/chromadb/)
DATABASE_PATH = Path(__file__).resolve().parent / "database" / "chromadb"

# ChromaDB collection name for image embeddings
COLLECTION_NAME = "image_embeddings"

# Directory for storing model files (e.g., project/conversational_memory_bot/models/)
MODELS_DIR = Path(__file__).resolve().parent / "models"
YOLOV8S_PATH = MODELS_DIR / "yolov8s.pt"

# Ensure directories exist at module import time
try:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"Error creating image directory {IMAGE_DIR}: {e}")

try:
    DATABASE_PATH.mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"Error creating database directory {DATABASE_PATH}: {e}")

try:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"Error creating models directory {MODELS_DIR}: {e}")
