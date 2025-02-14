from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()


# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def upload(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@router.post("")
async def upload_image(request: Request, files: list[UploadFile] = File(...)):
    return {"message": "Image upload complete"}