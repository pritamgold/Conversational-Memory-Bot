from typing import List, Optional

from PIL import Image, ExifTags
from ultralytics import YOLO

from conversational_photo_gallery.config import YOLOV8S_PATH
from conversational_photo_gallery.services.llm_service import LLMService


class ImageProcessor:
    """Processes images to generate metadata and descriptions."""

    def __init__(self) -> None:
        """Initialize ImageProcessor with YOLO and LLM dependencies.

        Raises:
            RuntimeError: If model initialization fails.
        """
        try:
            self.yolo_model = YOLO(YOLOV8S_PATH)
            self.llm_service = LLMService()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ImageProcessor: {e}")

    def generate_description(self, image_path: str) -> str:
        """Generate a description using the Gemini model via LLMService.

        Args:
            image_path: Path to the image file.

        Returns:
            str: One-sentence description of the image.

        Raises:
            ValueError: If description generation fails.
        """
        prompt = (
            "Provide a concise, detailed description of this image in 2-3 sentences, "
            "focusing on key objects, actions, colors, and the overall scene. Highlight "
            "any notable elements like people, animals, or landscapes that might "
            "help identify or categorize the image for a photo gallery."
        )
        return self.llm_service.generate_image_response(image_path, prompt)

    def generate_tags(self, image_path: str) -> List[str]:
        """Generate tags directly from the image using the Gemini model.

        Args:
            image_path: Path to the image file.

        Returns:
            List[str]: List of tags extracted from the image.

        Raises:
            ValueError: If tag generation fails.
        """
        prompt = (
            "Generate a comma-separated list of relevant tags for this image, "
            "focusing on activities, objects and scenes."
        )
        response = self.llm_service.generate_image_response(image_path, prompt)
        return [tag.strip() for tag in response.split(",")]

    def detect_objects(self, image_path: str) -> List[str]:
        """Detect objects in the image using YOLOv8.

        Args:
            image_path: Path to the image file.

        Returns:
            List[str]: List of unique object labels detected.

        Raises:
            ValueError: If object detection fails.
        """
        try:
            results = self.yolo_model(image_path)
            detections = results[0].boxes.data
            labels = [self.yolo_model.names[int(cls)] for cls in detections[:, -1]]
            return list(set(labels))
        except Exception as e:
            raise ValueError(f"Failed to detect objects in {image_path}: {e}")

    def detect_dominant_color(self, image_path: str) -> str:
        """Detect the dominant color in the image using the Gemini model.

        Args:
            image_path: Path to the image file.

        Returns:
            str: Name of the dominant color (e.g., 'red').

        Raises:
            ValueError: If color detection fails.
        """
        prompt = (
            "Identify the dominant color in this image and return only the color name "
            "(e.g., 'red', 'blue') without additional text."
        )
        return self.llm_service.generate_image_response(image_path, prompt)

    def extract_exif_data(self, image_path: str) -> Optional[str]:
        """Extract date from image EXIF data.

        Args:
            image_path: Path to the image file.

        Returns:
            Optional[str]: Date string from EXIF data, or None if not found.

        Raises:
            ValueError: If image loading fails.
            FileNotFoundError: if the image file is not found.
            PIL.UnidentifiedImageError: if the image format is not recognized.
        """
        try:
            image = Image.open(image_path)
            exif = image.getexif()
            date = None

            if exif:
                date_tag = ExifTags.TAGS.get("DateTimeOriginal")
                if date_tag and date_tag in exif:
                    date = exif[date_tag]

            return date
        except FileNotFoundError:
            raise FileNotFoundError(f"Image file not found: {image_path}")
        except Image.UnidentifiedImageError:
            raise Image.UnidentifiedImageError(f"Unidentified image file: {image_path}")
        except Exception as e:
            raise ValueError(f"Failed to extract EXIF data from {image_path}: {e}")
