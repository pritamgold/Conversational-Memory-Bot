# import torch
# import clip
# import google.generativeai as genai
# from PIL import Image
# from pathlib import Path
# from datetime import datetime
# from fastapi import UploadFile


# class ImageHandler:
#     """Handles image saving, description generation, and embedding using CLIP and Gemini AI."""

#     def __init__(self, image_dir: Path, model_name="ViT-B/32", device=None):
#         self.image_dir = image_dir
#         self.image_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

#         self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
#         self.model, self.preprocess = clip.load(model_name, device=self.device)
#         self.model.eval()  # Set model to evaluation mode

#         # Configure Gemini API
#         genai.configure(api_key="AIzaSyCGI1hgjReYktaqf8hvXMbFO7vWOv9HMeM")  # Replace with your actual key
#         self.model_gemini = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")


#     async def save_uploaded_image(self, file: UploadFile) -> Path:
#         """Save an uploaded image to the local storage directory."""
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         unique_filename = f"{timestamp}_{file.filename}"
#         file_path = self.image_dir / unique_filename

#         image_bytes = await file.read()
#         with open(file_path, "wb") as buffer:
#             buffer.write(image_bytes)

#         return unique_filename, file_path


#     def generate_description_and_tags(self, image: Image) -> dict:
#         """
#         Generate an image description and relevant tags using Gemini API.
        
#         Returns:
#         - dict: {"description": str, "tags": list[str]}
#         """
#         try:
#             # Generate image description
#             prompt_desc = "Describe what is happening in this image. What is the story it tells? do not include the image shows, the story of the image. Just describe."
#             response_desc = self.model_gemini.generate_content([prompt_desc, image])
#             description = response_desc.text if response_desc else "No description available."

#             # Generate image tags
#             prompt_tags = "Generate comma-separated tags for this image, focusing on objects, people, activities and the overall scene.  Return only important tags, no other text."
#             response_tags = self.model_gemini.generate_content([prompt_tags, image])
#             tags = response_tags.text.split(", ") if response_tags else []

#             return {"description": description.strip(), "tags": [tag.strip() for tag in tags]}

#         except Exception as e:
#             return {"description": f"Error generating description: {str(e)}", "tags": []}


#     def get_image_embedding(self, image_path: Path) -> list[float]:
#         """Generate CLIP embeddings for an image."""
#         try:
#             # Open and preprocess image
#             image = Image.open(image_path).convert("RGB")
#             image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

#             # Generate embeddings
#             with torch.no_grad():
#                 embedding = self.model.encode_image(image_tensor).squeeze(0)

#             # Convert tensor to list
#             return embedding.cpu().tolist()

#         except OSError:
#             raise RuntimeError(f"Error: Unable to open image file {image_path}")
#         except RuntimeError as e:
#             raise RuntimeError(f"Model inference failed: {e}")


#     def store_image_metadata(self, collection, unique_filename: str, file_path: Path, embedding: list[float], description: str, tags: list[str]):
#         """Store image metadata and embeddings in ChromaDB."""
        
#         # Convert the tags list into a single comma-separated string
#         tags_str = ", ".join(tags) if tags else ""

#         collection.add(
#             ids=[unique_filename],
#             embeddings=[embedding],
#             metadatas=[{"description": description, "tags": tags_str, "file_path": str(file_path)}],
#             documents=[description]
#         )
import os
import torch
import clip
import google.generativeai as genai
from PIL import Image
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from fastapi import UploadFile

# Load environment variables
load_dotenv()

class ImageHandler:
    """Handles image saving, description generation, and embedding using CLIP and Gemini AI."""

    def __init__(self, image_dir: Path, model_name="ViT-B/32", device=None):
        self.image_dir = image_dir
        self.image_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.preprocess = clip.load(model_name, device=self.device)
        self.model.eval()  # Set model to evaluation mode

        # Configure Gemini API
        genai_api_key = os.getenv("GEMINI_API_KEY")
        if not genai_api_key:
            raise ValueError("GEMINI_API_KEY is missing in .env file.")
        
        genai.configure(api_key=genai_api_key)
        self.model_gemini = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

    async def save_uploaded_image(self, file: UploadFile) -> tuple[str, Path]:
        """Save an uploaded image and return its unique filename and path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{file.filename}"
        file_path = self.image_dir / unique_filename

        image_bytes = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(image_bytes)

        return unique_filename, file_path

    def generate_description_and_tags(self, image: Image) -> dict:
        """
        Generate an image description and relevant tags using Gemini API.
        
        Returns:
            dict: {"description": str, "tags": list[str]}
        """
        try:
            # Generate image description
            prompt_desc = (
                "Describe what is happening in this image. "
                "What is the story it tells? do not include the image shows, the story of the image. Just describe."
            )
            response_desc = self.model_gemini.generate_content([prompt_desc, image])
            description = response_desc.text.strip() if response_desc else "No description available."

            # Generate image tags
            prompt_tags = (
                "Generate comma-separated tags for this image, focusing on objects, "
                "people, activities, and the overall scene. Return only important tags, no other text."
            )
            response_tags = self.model_gemini.generate_content([prompt_tags, image])
            tags = [tag.strip() for tag in response_tags.text.split(",")] if response_tags else []

            return {"description": description, "tags": tags}

        except Exception as e:
            return {"description": f"Error generating description: {str(e)}", "tags": []}

    def get_image_embedding(self, image_path: Path) -> list[float]:
        """Generate CLIP embeddings for an image."""
        try:
            image = Image.open(image_path).convert("RGB")
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                embedding = self.model.encode_image(image_tensor).squeeze(0)

            return embedding.cpu().tolist()

        except OSError:
            raise RuntimeError(f"Error: Unable to open image file {image_path}")
        except RuntimeError as e:
            raise RuntimeError(f"Model inference failed: {e}")

    def store_image_metadata(
        self, collection, unique_filename: str, file_path: Path, 
        embedding: list[float], description: str, tags: list[str]
    ):
        """Store image metadata and embeddings in ChromaDB."""

        # Convert the tags list into a single comma-separated string
        tags_str = ", ".join(tags) if tags else ""

        collection.add(
            ids=[unique_filename],
            embeddings=[embedding],
            metadatas=[{
                "description": description,
                "tags": tags_str,
                "file_path": str(file_path)
            }],
            documents=[description]
        )
