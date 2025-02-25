from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from conversational_photo_gallery.dependencies import get_collection
from conversational_photo_gallery.services.chat_handler import ChatHandler

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def chat(request: Request):
    """Render the chat interface."""
    return templates.TemplateResponse("chat.html", {"request": request})

@router.post("/")
async def chat(
    request: Request,
    query: str = Form(None),
    image: UploadFile = File(None),
    collection=Depends(get_collection),
):
    """Handle chat queries with text, image, or both."""
    if not query and not image:
        raise HTTPException(
            status_code=400, detail="Please provide a text query and/or an image."
        )

    chat_handler = ChatHandler(collection)

    if query and not image:
        return chat_handler.handle_text_query(query)
    elif image and not query:
        return chat_handler.handle_image_query(image)
    elif query and image:
        return chat_handler.handle_multimodal_query(query, image)