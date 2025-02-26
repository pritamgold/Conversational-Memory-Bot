import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Add the parent directory of the conversational_photo_gallery directory to the Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from routes import homepage, gallery, image_viewer, chat, upload


app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")


app.include_router(homepage.router, prefix="")
app.include_router(gallery.router, prefix="/gallery")
app.include_router(upload.router, prefix="/upload")
app.include_router(image_viewer.router, prefix="/gallery")
app.include_router(chat.router, prefix="/chat")

if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)
