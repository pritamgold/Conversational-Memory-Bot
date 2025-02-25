from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse

from conversational_photo_gallery.config import TEMPLATES
from conversational_photo_gallery.models import UploadResponse
from conversational_photo_gallery.services.image_uploader import ImageUploader

router = APIRouter(prefix="/upload", tags=["upload"])


@router.get("/", response_class=HTMLResponse)
async def upload_page(request: Request) -> HTMLResponse:
    """Render the image upload page.

    Args:
        request: The incoming HTTP request object from FastAPI.

    Returns:
        HTMLResponse: The rendered upload.html template.

    Raises:
        HTTPException: If template rendering fails (e.g., missing template file).
    """
    try:
        return TEMPLATES.TemplateResponse("upload.html", {"request": request})
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to render upload page: {e}"
        )


@router.post("/", response_model=UploadResponse)
async def upload_images(files: list[UploadFile] = File(...)) -> UploadResponse:
    """Upload one or multiple images and process them for storage in ChromaDB.

    Args:
        files: A list of image files to upload, provided as UploadFile objects.

    Returns:
        UploadResponse: A Pydantic model containing a success message.

    Raises:
        HTTPException: If any image upload fails or processing encounters an error.
    """
    try:
        uploader = ImageUploader()  # Create ImageUploader instance here
        errors = []

        for upload_file in files:
            try:
                uploader.upload(upload_file)
            except ValueError as e:
                errors.append(f"Failed to upload {upload_file.filename}: {str(e)}")

        num_files = len(files)
        if errors:
            error_message = "Error while uploading: " + "; ".join(errors)
            raise HTTPException(status_code=400, detail=error_message)

        message = (
            "Image uploaded successfully"
            if num_files == 1
            else "Images uploaded successfully"
        )
        return UploadResponse(message=message)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unexpected error during upload: {str(e)}"
        )
