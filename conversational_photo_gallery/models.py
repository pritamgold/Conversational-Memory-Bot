from typing import List, Optional

from pydantic import BaseModel


# Model for image metadata (used in image_viewer.py and chat_handler.py)
class ImageMetadata(BaseModel):
    url: str
    description: str = "No description available"
    tags: List[str] = []
    date: str = "No date available"
    dominant_color: str = "Unknown"
    objects: List[str] = []
    id: str


# Model for upload response (used in upload.py)
class UploadResponse(BaseModel):
    message: str


# Model for chat response (used in chat_handler.py)
class ChatResponse(BaseModel):
    response: str
    images: Optional[List[str]] = None
