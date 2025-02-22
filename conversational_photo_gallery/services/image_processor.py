import os
from typing import List, Optional

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image, ExifTags
from sentence_transformers import SentenceTransformer
from ultralytics import YOLO

from conversational_photo_gallery.config import YOLOV8S_PATH


# Load environment variables from .env at module import time
load_dotenv()


class ImageProcessor:
    """Processes images to generate embeddings, metadata, and descriptions."""

    def __init__(self):
        """Initialize ImageProcessor with CLIP, YOLO, and Gemini models.

        Raises:
            RuntimeError: If model initialization or API configuration fails.
        """
        try:
            self.clip_model = SentenceTransformer('clip-ViT-B-32')
            self.yolo_model = YOLO(YOLOV8S_PATH)
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not self.gemini_api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ImageProcessor: {e}")

    def generate_embedding(self, image_path: str) -> List[float]:
        """Generate a CLIP embedding for the image.

        Args:
            image_path (str): Path to the image file.

        Returns:
            List[float]: Embedding vector for the image.

        Raises:
            ValueError: If image loading or embedding generation fails.
        """
        try:
            image = Image.open(image_path)
            return self.clip_model.encode(image).tolist()
        except Exception as e:
            raise ValueError(f"Failed to generate embedding for {image_path}: {e}")

    def generate_description(self, image_path: str) -> str:
        """Generate a description using the Gemini model.

        Args:
            image_path (str): Path to the image file.

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
        return self._query_gemini(image_path, prompt)

    def generate_tags(self, image_path: str) -> List[str]:
        """Generate tags directly from the image using the Gemini model.

        Args:
            image_path (str): Path to the image file.

        Returns:
            List[str]: List of tags extracted from the image.

        Raises:
            ValueError: If tag generation fails.
        """
        prompt = (
            "Generate a comma-separated list of relevant tags for this image, "
            "focusing on activities, objects and scenes."
        )
        response = self._query_gemini(image_path, prompt)
        return [tag.strip() for tag in response.split(',')]

    def detect_objects(self, image_path: str) -> List[str]:
        """Detect objects in the image using YOLOv8.

        Args:
            image_path (str): Path to the image file.

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
            image_path (str): Path to the image file.

        Returns:
            str: Name of the dominant color (e.g., 'red').

        Raises:
            ValueError: If color detection fails.
        """
        prompt = (
            "Identify the dominant color in this image and return only the color name "
            "(e.g., 'red', 'blue') without additional text."
        )
        return self._query_gemini(image_path, prompt)

    def extract_exif_data(self, image_path: str) -> Optional[str]:
        """Extract date from image EXIF data.

        Args:
            image_path (str): Path to the image file.

        Returns:
            Optional[str]: Date string from EXIF data, or None if not found.

        Raises:
            ValueError: If image loading fails.
        """
        try:
            image = Image.open(image_path)
            exif = image.getexif()
            date = None

            if exif:
                date_tag = 36867  # EXIF tag for DateTimeOriginal
                if date_tag in exif:
                    date = exif[date_tag]

            return date
        except Exception as e:
            raise ValueError(f"Failed to extract EXIF data from {image_path}: {e}")

    def _query_gemini(self, image_path: str, prompt: str) -> str:
        """Query the Gemini model with an image and prompt.

        Args:
            image_path (str): Path to the image file.
            prompt (str): Prompt to send to the Gemini model.

        Returns:
            str: Response text from the Gemini model.

        Raises:
            ValueError: If querying the Gemini model fails.
        """
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            response = self.gemini_model.generate_content(
                [prompt, {"mime_type": "image/jpeg", "data": image_data}]
            )
            return response.text.strip()
        except Exception as e:
            raise ValueError(f"Failed to query Gemini for {image_path}: {e}")