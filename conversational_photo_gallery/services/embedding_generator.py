import os
from typing import List

import torch
from PIL import Image
from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:
    """Handles generation of CLIP embeddings for text and images."""
    _instance = None  # Singleton instance

    def __new__(cls):
        """Ensure a single instance of EmbeddingGenerator."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()  # Initialize only once
        return cls._instance

    def _initialize(self) -> None:
        """Initialize the EmbeddingGenerator with the CLIP model."""
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.clip_model = SentenceTransformer("clip-ViT-B-32", device=device)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize EmbeddingGenerator: {e}")

    def generate_text_embedding(self, text: str) -> List[float]:
        """Generate a CLIP embedding for the given text.

        Args:
            text: The text to encode.

        Returns:
            List[float]: Embedding vector for the text.

        Raises:
            ValueError: If text encoding fails.
        """
        # Ensure the text parameter isn’t empty
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")

        try:
            return self.clip_model.encode(text).tolist()
        except Exception as e:
            raise ValueError(f"Failed to generate text embedding: {e}")

    def generate_embedding(self, image_path: str) -> List[float]:
        """Generate a CLIP embedding for the image.

        Args:
            image_path: Path to the image file.

        Returns:
            List[float]: Embedding vector for the image.
        """
        # Verify that image_path exists
        if not isinstance(image_path, str) or not os.path.isfile(image_path):
            raise ValueError(f"Invalid image path: {image_path}")

        try:
            image = Image.open(image_path).convert("RGB")
            return self.clip_model.encode(image).tolist()
        except Exception as e:
            raise ValueError(f"Failed to generate embedding for {image_path}: {e}")
