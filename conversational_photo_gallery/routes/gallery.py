from os.path import basename

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse

from conversational_photo_gallery.config import TEMPLATES
from conversational_photo_gallery.dependencies import get_collection


router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def gallery(request: Request, collection=Depends(get_collection)) -> HTMLResponse:
    """Retrieve all image file paths and metadata from ChromaDB.

    Args:
        request (Request): FastAPI request object.
        collection: ChromaDB collection dependency.

    Returns:
        HTMLResponse: Rendered gallery template with image data.

    Raises:
        HTTPException: If retrieving image data fails.
    """
    try:
        # Fetch all data from ChromaDB
        results = collection.get(include=["metadatas"])

        # Extract image paths (IDs) and prepare data for template
        images_data = [
            {
                "url": f"/images/{basename(image_id)}",  # Relative URL from absolute path
                "id": basename(image_id)  # Use filename as ID for routing
            }
            for image_id in results.get("ids", [])
        ]

        return TEMPLATES.TemplateResponse(
            "gallery.html",
            {"request": request, "images": images_data}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve gallery images: {str(e)}"
        )
