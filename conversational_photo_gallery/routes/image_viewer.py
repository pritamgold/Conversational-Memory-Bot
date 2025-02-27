from os.path import basename, join

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from conversational_photo_gallery.config import IMAGE_DIR, TEMPLATES
from conversational_photo_gallery.dependencies import get_collection
from conversational_photo_gallery.models import ImageMetadata

router = APIRouter()

@router.get("/{image_id}", response_class=HTMLResponse)
async def image_viewer(
    request: Request,
    image_id: str,
    collection=Depends(get_collection)
) -> HTMLResponse:
    """Retrieve and display image details from ChromaDB.

    Args:
        request (Request): FastAPI request object.
        image_id (str): Filename of the image (e.g., '11fece7a-fc0e-450e-b536-b8718bf44600.jpg').
        collection: ChromaDB collection dependency.

    Returns:
        HTMLResponse: Rendered image viewer template with image metadata.

    Raises:
        HTTPException: If the image is not found or an error occurs.
    """
    try:
        # Construct full image path from filename
        full_image_path = join(IMAGE_DIR, image_id)

        # Fetch metadata using the full path as the ID
        results = collection.get(ids=[full_image_path], include=["metadatas"])

        if not results.get("metadatas"):
            raise HTTPException(status_code=404, detail="Image not found")

        metadata = results["metadatas"][0]

        # Combine tags and user_tags into a single list
        tags = metadata.get("tags", "").split(",")
        user_tags = metadata.get("user_tags", "").split(",")
        combined_tags = [tag.strip() for tag in tags + user_tags if tag.strip()]

        # Create Pydantic model instance
        image_data = ImageMetadata(
            url=f"/images/{image_id}",
            description=metadata.get("description", "No description available"),
            tags=combined_tags,
            date=metadata.get("date", "No date available"),
            dominant_color=metadata.get("dominant_color", "Unknown"),
            objects=metadata.get("objects", "").split(",") if metadata.get("objects") else [],
            id=image_id
        )

        return TEMPLATES.TemplateResponse(
            "image_viewer.html",
            {"request": request, "image": image_data.dict()}  # Convert to dict for template
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve image details: {str(e)}"
        )
