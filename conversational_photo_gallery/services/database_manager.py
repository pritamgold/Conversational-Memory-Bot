from typing import Dict, List, Optional

import chromadb

from conversational_photo_gallery.config import COLLECTION_NAME, DATABASE_PATH


class DatabaseManager:
    """Handles interactions with ChromaDB for image storage."""

    def __init__(
        self,
        db_path: str = str(DATABASE_PATH),
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        """Initialize the DatabaseManager with a ChromaDB client and collection.

        Args:
            db_path: Path to the ChromaDB storage directory.
            collection_name: Name of the collection to use or create.

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

    def add_image(
        self, image_path: str, embedding: List[float], metadata: Dict[str, str]
    ) -> None:
        """Add an image embedding and metadata to the collection.

        Args:
            image_path: Path to the image file, used as the ID.
            embedding: Embedding vector for the image.
            metadata: Metadata dictionary for the image.

        Raises:
            ValueError: If adding the image to ChromaDB fails.
        """
        try:
            self.collection.add(
                ids=[image_path],
                embeddings=[embedding],
                metadatas=[metadata],
            )
        except Exception as e:
            raise ValueError(f"Failed to add image {image_path}: {e}")

    def get_metadata(self, image_path: str) -> Dict[str, str]:
        """Retrieve metadata for an image.

        Args:
            image_path: Path to the image file, used as the ID.

        Returns:
            Dict[str, str]: Metadata dictionary for the image, empty if not found.

        Raises:
            RuntimeError: If metadata retrieval fails.
        """
        try:
            result = self.collection.get(ids=[image_path])
            return result["metadatas"][0] if result["metadatas"] else {}
        except Exception as e:
            raise RuntimeError(f"Metadata retrieval failed for {image_path}: {e}")

    def update_metadata(
        self,
        image_path: str,
        metadata: Optional[Dict[str, str]] = None,
        user_tags: Optional[List[str]] = None,
    ) -> None:
        """Update metadata for an image, optionally merging user tags.

        Args:
            image_path: Path to the image file, used as the ID.
            metadata: Full metadata dictionary to update (optional).
            user_tags: List of user-defined tags to merge into existing metadata (optional).

        Raises:
            ValueError: If metadata update fails or image_path is invalid.
        """
        try:
            if user_tags is not None:
                current_metadata = self.get_metadata(image_path)
                if not current_metadata:
                    raise ValueError(f"No metadata found for image {image_path}")
                current_metadata["user_tags"] = ",".join(user_tags)
                self.collection.update(
                    ids=[image_path],
                    metadatas=[current_metadata],
                )
            elif metadata is not None:
                self.collection.update(
                    ids=[image_path],
                    metadatas=[metadata],
                )
            else:
                raise ValueError("Either metadata or user_tags must be provided")
        except ValueError as e:
            raise  # Re-raise ValueError from get_metadata or our check
        except Exception as e:
            raise ValueError(f"Failed to update metadata for {image_path}: {e}")
