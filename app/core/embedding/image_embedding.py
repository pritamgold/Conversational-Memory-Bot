import torch
import clip
from PIL import Image
from pathlib import Path
from typing import List


# Load CLIP model (OpenAI's ViT-B/32)
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Set model to evaluation mode
model.eval()


def get_image_embedding(image_path: Path) -> List[float]:
    """
    Generates a CLIP (Contrastive Language-Image Pretraining) embedding for a given image.

    This function:
    - Loads an image from the provided path.
    - Converts it to RGB format to ensure compatibility.
    - Applies the CLIP model's preprocessing pipeline.
    - Encodes the image into a high-dimensional vector (embedding).
    - Returns the embedding as a list of floats.

    Args:
        image_path (Path): The file path of the image to be processed.

    Returns:
        List[float]: A list representing the image's embedding in a high-dimensional space.

    Raises:
        RuntimeError: If the image cannot be opened or if the model fails to generate an embedding.
    """
    try:
        # Open and preprocess image
        image = Image.open(image_path).convert("RGB")
        image_tensor = preprocess(image).unsqueeze(0).to(device)

        # Generate embeddings
        with torch.no_grad():
            embedding = model.encode_image(image_tensor).squeeze(0)

        # Convert tensor to list (via numpy for efficiency)
        return embedding.cpu().numpy().tolist()

    except OSError:
        raise RuntimeError(f"Error: Unable to open image file {image_path}")
    except RuntimeError as e:
        raise RuntimeError(f"Model inference failed: {e}")
