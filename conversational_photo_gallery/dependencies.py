import chromadb
from pathlib import Path

# Define database path
DATABASE_PATH = Path(__file__).resolve().parent / "database/chromadb"


def get_collection():
    """Initialize ChromaDB collection without using its integrated embedding function."""
    client = chromadb.PersistentClient(path=str(DATABASE_PATH))

    return client.get_or_create_collection(name="image_embeddings")
