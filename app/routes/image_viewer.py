from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()


# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")


@router.get("/{image_id}", response_class=HTMLResponse)
async def image_viewer(request: Request, image_id: str):
    return templates.TemplateResponse("image_viewer.html", {"request": request, "image_id": image_id})
