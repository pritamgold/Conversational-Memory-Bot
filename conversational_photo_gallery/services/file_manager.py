import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from conversational_photo_gallery.config import IMAGE_DIR


class FileManager:
    """Manages file operations for uploaded images."""

    def __init__(self, upload_dir: str = str(IMAGE_DIR)):
        """Initialize FileManager with an upload directory.

        Args:
            upload_dir (str): Directory path where images will be saved.
                              Defaults to IMAGE_DIR from config.
        """
        self.upload_dir = Path(upload_dir)  # Directory created in config.py

    def save_image(self, upload_file: UploadFile) -> str:
        """Save a single uploaded image locally with a unique name.

        Args:
            upload_file (UploadFile): The image file to save.

        Returns:
            str: The file path where the image was saved.
        """
        unique_id = str(uuid.uuid4())
        extension = upload_file.filename.split('.')[-1]
        image_path = self.upload_dir / f"{unique_id}.{extension}"
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return str(image_path)
