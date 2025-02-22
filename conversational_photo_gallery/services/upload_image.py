from typing import Dict, List, Optional, Tuple

from fastapi import UploadFile

from conversational_photo_gallery.services.database_manager import DatabaseManager
from conversational_photo_gallery.services.file_manager import FileManager
from conversational_photo_gallery.services.image_processor import ImageProcessor


class ImageUploader:
    """Coordinates the image upload process."""

    def __init__(self) -> None:
        """Initialize ImageUploader with required managers and processors.

        Raises:
            RuntimeError: If initialization of dependencies fails.
        """
        try:
            self.db_manager = DatabaseManager()
            self.image_processor = ImageProcessor()
            self.file_manager = FileManager()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ImageUploader: {e}")

    def _process_image(self, image_path: str) -> Tuple[List[float], Dict[str, str]]:
        """Process a single image and return embedding and metadata.

        Args:
            image_path (str): Path to the image file to process.

        Returns:
            Tuple[List[float], Dict[str, str]]: Embedding vector and metadata dictionary.

        Raises:
            ValueError: If image processing fails (e.g., embedding, description, or metadata generation).
        """
        try:
            embedding = self.image_processor.generate_embedding(image_path)
            description = self.image_processor.generate_description(image_path)
            tags = self.image_processor.generate_tags(image_path)
            date = self.image_processor.extract_exif_data(image_path)
            dominant_color = self.image_processor.detect_dominant_color(image_path)
            objects = self.image_processor.detect_objects(image_path)

            metadata = {
                "description": description,
                "tags": ",".join(tags),
                "date": date if date else "",
                "user_tags": "",
                "dominant_color": dominant_color,
                "objects": ",".join(objects),
            }
            return embedding, metadata
        except Exception as e:
            raise ValueError(f"Error processing image {image_path}: {str(e)}")

    def upload(self, upload_file: UploadFile) -> None:
        """Process and upload a single image to ChromaDB.

        Args:
            upload_file (UploadFile): The image file to upload.

        Raises:
            ValueError: If file saving or image processing fails.
        """
        try:
            image_path = self.file_manager.save_image(upload_file)
            embedding, metadata = self._process_image(image_path)
            self.db_manager.add_image(image_path, embedding, metadata)
        except Exception as e:
            raise ValueError(f"Failed to upload image {upload_file.filename}: {str(e)}")

    def update_metadata(self, image_path: str, user_tags: Optional[List[str]] = None) -> None:
        """Update user-provided metadata for an image.

        Args:
            image_path (str): Unique identifier for the image to update.
            user_tags (Optional[List[str]]): List of user-defined tags to update.

        Raises:
            ValueError: If metadata update fails or image_path is invalid.
        """
        try:
            current_metadata = self.db_manager.get_metadata(image_path)
            if not current_metadata:
                raise ValueError(f"No metadata found for image {image_path}")

            if user_tags is not None:
                current_metadata["user_tags"] = ",".join(user_tags)

            self.db_manager.update_metadata(image_path, current_metadata)
        except ValueError as e:
            raise  # Re-raise ValueError from get_metadata or our check
        except Exception as e:
            raise ValueError(f"Failed to update metadata for {image_path}: {str(e)}")