from typing import Dict, List

import chromadb

from conversational_photo_gallery.config import DATABASE_PATH, COLLECTION_NAME


class DatabaseManager:
    """Handles interactions with ChromaDB."""

    def __init__(self, db_path: str = str(DATABASE_PATH), collection_name: str = COLLECTION_NAME):
        """Initialize the DatabaseManager with a ChromaDB client and collection.

        Args:
            db_path (str): Path to the ChromaDB storage directory.
            collection_name (str): Name of the collection to use or create.

        Raises:
            RuntimeError: If ChromaDB client or collection initialization fails.
        """
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            raise RuntimeError(f"Database initialization failed: {e}")


    def add_image(self, image_path: str, embedding: List[float], metadata: Dict[str, str]) -> None:
        """Add an image embedding and metadata to the collection."""
        try:
            self.collection.add(
                ids=[image_path],
                embeddings=[embedding],
                metadatas=[metadata],
            )
        except Exception as e:
            raise ValueError(f"Failed to add image {image_path}: {e}")


    def get_metadata(self, image_path: str) -> Dict[str, str]:
        """Retrieve metadata for an image."""
        try:
            result = self.collection.get(ids=[image_path])
            return result["metadatas"][0] if result["metadatas"] else {}
        except Exception as e:
            raise RuntimeError(f"Metadata retrieval failed for {image_path}: {e}")


    def update_metadata(self, image_path: str, metadata: Dict[str, str]) -> None:
        """Update metadata for an image."""
        try:
            self.collection.update(
                ids=[image_path],
                metadatas=[metadata],
            )
        except Exception as e:
            raise ValueError(f"Metadata update failed for {image_path}: {e}")
