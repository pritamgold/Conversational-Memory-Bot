from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def gallery(request: Request):
    return templates.TemplateResponse("gallery.html", {"request": request})
