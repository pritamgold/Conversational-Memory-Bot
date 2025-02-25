from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from conversational_photo_gallery.config import TEMPLATES

router = APIRouter()


# Homepage route
@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """
    Renders the homepage.

    Args:
        request: The incoming request.

    Returns:
        An HTML response rendering the index.html template.
    """
    return TEMPLATES.TemplateResponse("index.html", {"request": request})
