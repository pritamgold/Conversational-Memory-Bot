from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()


# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def chat(request: Request):
    return templates.TemplateResponse("query.html", {"request": request})


@router.post("")
async def chat_response(request: Request, files: list[UploadFile] = File(...)):
    # ... chatbot logic ...
    return {"response": "bot_response"}