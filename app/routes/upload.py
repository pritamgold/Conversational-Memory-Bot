from pathlib import Path

from PIL import Image
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_collection
from app.core.image_handler import ImageHandler


# Define image storage directory to upload
IMAGE_DIR = Path(__file__).resolve().parent.parent / "images"
try:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Error creating image directory: {e}")


# Initialize
router = APIRouter()
image_handler = ImageHandler(IMAGE_DIR)
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def upload(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@router.post("")
async def upload_images(
    files: list[UploadFile] = File(...),
    collection=Depends(get_collection)
):
    """
    Handles image uploads, generates embeddings, and stores metadata.

    Steps:
    1. Saves uploaded images to local storage.
    2. Generates descriptions for each image.
    3. Computes image embeddings.
    4. Stores image metadata and embeddings in ChromaDB.

    Args:
        files (list[UploadFile]): List of uploaded image files.
        collection: ChromaDB collection dependency.

    Returns:
        JSONResponse: A response containing metadata of uploaded images.
    """
    try:
        results = []

        for file in files:
            # Save the uploaded image
            unique_filename, file_path = await image_handler.save_uploaded_image(file)

            # Open image and generate a description + tags
            image = Image.open(file_path).convert("RGB")
            description_data = image_handler.generate_description_and_tags(image)

            # Extract description and tags
            description = description_data["description"]
            tags = description_data["tags"]

            # Generate image embeddings
            embedding = image_handler.get_image_embedding(file_path)

            # Store metadata in ChromaDB
            image_handler.store_image_metadata(collection, unique_filename, file_path, embedding, description, tags)

            # Append result for response
            results.append({
                "id": unique_filename,
                "description": description,
                "tags": tags,
                "uri": str(file_path)
            })

        return JSONResponse(content={"results": results}, status_code=201)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")
