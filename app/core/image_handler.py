import torch
import clip
from PIL import Image
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile


class ImageHandler:
    """Handles image saving, description generation, and embedding using CLIP."""

    def __init__(self, image_dir: Path, model_name="ViT-B/32", device=None):
        self.image_dir = image_dir
        self.image_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.preprocess = clip.load(model_name, device=self.device)
        self.model.eval()  # Set model to evaluation mode

    def save_uploaded_image(self, file: UploadFile) -> Path:
        """Save an uploaded image to the local storage directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{file.filename}"
        file_path = self.image_dir / unique_filename

        image_bytes = file.file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(image_bytes)

        return file_path

    def generate_description(self, image: Image) -> str:
        """Generate a description for an image (Dummy implementation)."""
        return "A sample image description"  # Replace with an AI-based model

    def get_image_embedding(self, image_path: Path) -> list[float]:
        """Generate CLIP embeddings for an image."""
        try:
            # Open and preprocess image
            image = Image.open(image_path).convert("RGB")
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

            # Generate embeddings
            with torch.no_grad():
                embedding = self.model.encode_image(image_tensor).squeeze(0)

            # Convert tensor to list
            return embedding.cpu().tolist()

        except OSError:
            raise RuntimeError(f"Error: Unable to open image file {image_path}")
        except RuntimeError as e:
            raise RuntimeError(f"Model inference failed: {e}")

    def store_image_metadata(self, collection, file_path: Path, embedding: list[float], description: str):
        """Store image metadata and embeddings in ChromaDB."""
        collection.add(
            ids=[file_path.name],
            embeddings=[embedding],
            metadatas=[{"description": description, "file_path": str(file_path)}],
            documents=[description]
        )
