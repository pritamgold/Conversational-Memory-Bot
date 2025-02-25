from typing import List

from PIL import Image
from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:
    """Handles generation of CLIP embeddings for text and images."""

    def __init__(self) -> None:
        """Initialize the EmbeddingGenerator with the CLIP model.

        Raises:
            RuntimeError: If CLIP model initialization fails.
        """
        try:
            self.clip_model = SentenceTransformer("clip-ViT-B-32")
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

        Raises:
            ValueError: If image loading or embedding generation fails.
        """
        try:
            image = Image.open(image_path)
            return self.clip_model.encode(image).tolist()
        except Exception as e:
            raise ValueError(f"Failed to generate embedding for {image_path}: {e}")
