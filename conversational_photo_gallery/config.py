from pathlib import Path

from fastapi.templating import Jinja2Templates


# Image storage directory, one level up from this file (e.g., conversational_photo_gallery/images/)
IMAGE_DIR = Path(__file__).resolve().parent / "images"

# Database storage directory (e.g., conversational_photo_gallery/database/chromadb/)
DATABASE_PATH = Path(__file__).resolve().parent / "database" / "chromadb"

# ChromaDB collection name for image embeddings
COLLECTION_NAME = "image_embeddings"

# Jinja2 templates configuration
try:
    TEMPLATES = Jinja2Templates(directory="templates")
except Exception as e:
    raise RuntimeError(f"Failed to initialize Jinja2 templates: {e}")

# Ensure directories exist at module import time
try:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"Error creating image directory {IMAGE_DIR}: {e}")

try:
    DATABASE_PATH.mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"Error creating database directory {DATABASE_PATH}: {e}")
