import io
from pathlib import Path
from PIL import Image
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from ..dependencies import get_collection
from ..core.image_handler import ImageHandler


# Initialize ImageHandler (handles both processing & embedding)
IMAGE_DIR = Path(__file__).resolve().parent.parent / "images"
image_handler = ImageHandler(IMAGE_DIR)


router = APIRouter()


# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def upload(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@router.post("/upload/")
async def upload_images(
        files: list[UploadFile] = File(...),
        collection=Depends(get_collection)
):
    """Uploads images, extracts embeddings using CLIP, and stores metadata in ChromaDB."""
    try:
        results = []

        for file in files:
            # Save the uploaded image
            file_path = image_handler.save_uploaded_image(file)

            # Open image and generate a description
            image = Image.open(io.BytesIO(await file.read()))
            description = image_handler.generate_description(image)

            # Generate image embeddings using CLIP
            embedding = image_handler.get_image_embedding(file_path)

            # Store metadata in ChromaDB
            image_handler.store_image_metadata(collection, file_path, embedding, description)

            # Append to response
            results.append({
                "filename": file.filename,
                "path": str(file_path),
                "description": description,
                "uri": str(file_path)
            })

        return JSONResponse(content={"results": results}, status_code=201)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")
