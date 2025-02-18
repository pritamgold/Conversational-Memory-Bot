from os.path import basename

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_collection

# Initialize router
router = APIRouter()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")


@router.get("/{image_id}", response_class=HTMLResponse)
async def image_viewer(
        request: Request,
        image_id: str,
        collection=Depends(get_collection)
) -> HTMLResponse:
    """
    Retrieve and display image details from ChromaDB.

    Args:
        request (Request): FastAPI request object.
        image_id (str): Unique identifier of the image.
        collection: Dependency injection for ChromaDB collection.

    Returns:
        HTMLResponse: Rendered image viewer template.

    Raises:
        HTTPException: If the image is not found or an error occurs.
    """
    results = collection.get(ids=[image_id])

    if not results.get("metadatas"):
        raise HTTPException(status_code=404, detail="Image not found")

    metadata = results["metadatas"][0]

    image_data = {
        "url": f"/images/{basename(metadata['file_path'])}",
        "description": metadata.get("description", "No description available"),
        "tags": metadata.get("tags", "").split(", ") if metadata.get("tags") else [],
        "id": image_id
    }

    return templates.TemplateResponse(
        "image_viewer.html",
        {"request": request, "image": image_data}
    )
