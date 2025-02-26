import chromadb

from conversational_photo_gallery.config import DATABASE_PATH, COLLECTION_NAME
from conversational_photo_gallery.services.embedding_generator import EmbeddingGenerator


def get_collection():
    """Initialize and return the ChromaDB collection for image embeddings.

    Returns:
        chromadb.Collection: The configured collection instance.
    """
    client = chromadb.PersistentClient(path=str(DATABASE_PATH))
    return client.get_or_create_collection(name=COLLECTION_NAME)

def get_embeddings_generator():
    return EmbeddingGenerator()