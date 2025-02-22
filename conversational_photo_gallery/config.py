# config.py
from pathlib import Path

# Image storage directory, two levels up from this file (e.g., project/images/)
IMAGE_DIR = Path(__file__).resolve().parent / "images"

# Database storage directory, one level up with subdirectories (e.g., project/conversational_memory_bot/database/chromadb/)
DATABASE_PATH = Path(__file__).resolve().parent / "database" / "chromadb"

# ChromaDB collection name for image embeddings
COLLECTION_NAME = "image_embeddings"

# Ensure directories exist at module import time
try:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"Error creating image directory {IMAGE_DIR}: {e}")

try:
    DATABASE_PATH.mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"Error creating database directory {DATABASE_PATH}: {e}")
