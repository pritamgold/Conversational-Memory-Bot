from typing import Dict, List, Tuple

from fastapi import UploadFile

from conversational_photo_gallery.dependencies import get_embeddings_generator
from conversational_photo_gallery.services.database_manager import DatabaseManager
from conversational_photo_gallery.services.file_manager import FileManager
from conversational_photo_gallery.services.image_processor import ImageProcessor


class ImageUploader:
    """Coordinates the upload and processing of images."""

    def __init__(self) -> None:
        """Initialize ImageUploader with required managers and processors.

        Raises:
            RuntimeError: If initialization of dependencies fails.
        """
        try:
            self.db_manager = DatabaseManager()
            self.image_processor = ImageProcessor()
            self.embedding_generator = get_embeddings_generator()
            self.file_manager = FileManager()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ImageUploader: {e}")

    def _process_image(self, image_path: str) -> Tuple[List[float], Dict[str, str]]:
        """Process a single image and return embedding and metadata.

        Args:
            image_path: Path to the image file to process.

        Returns:
            Tuple[List[float], Dict[str, str]]: Embedding vector and metadata dictionary.

        Raises:
            ValueError: If image processing fails.
        """
        try:
            embedding = self.embedding_generator.generate_embedding(image_path)
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
            upload_file: The image file to upload.

        Raises:
            ValueError: If file saving or image processing fails.
        """
        try:
            image_path = self.file_manager.save_image(upload_file)
            embedding, metadata = self._process_image(image_path)
            self.db_manager.add_image(image_path, embedding, metadata)
        except Exception as e:
            raise ValueError(f"Failed to upload image {upload_file.filename}: {str(e)}")
