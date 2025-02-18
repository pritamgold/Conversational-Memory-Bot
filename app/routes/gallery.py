from os.path import basename

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_collection

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Initialize router
router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def gallery(request: Request, collection=Depends(get_collection)) -> HTMLResponse:
    """
    Retrieve all image file paths and metadata from ChromaDB.

    Args:
        request (Request): FastAPI request object.
        collection: Dependency injection for ChromaDB collection.

    Returns:
        HTMLResponse: Rendered gallery template with image data.
    """
    results = collection.get()
    images_data = [
        {
            "url": f"/images/{basename(metadata['file_path'])}",
            "id": image_id  # Unique filename
        }
        for metadata, image_id in zip(results.get("metadatas", []), results.get("ids", []))
        if "file_path" in metadata
    ]

    return templates.TemplateResponse(
        "gallery.html",
        {"request": request, "images": images_data}
    )
