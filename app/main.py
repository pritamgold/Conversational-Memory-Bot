import os

import uvicorn
from fastapi import FastAPI

from routes import homepage, gallery, image_viewer, chat, upload

app = FastAPI()

# Directory to save uploaded images
IMAGE_DIR = "images/"
os.makedirs(IMAGE_DIR, exist_ok=True)


app.include_router(homepage.router, prefix="")
app.include_router(gallery.router, prefix="/gallery")
app.include_router(upload.router, prefix="/upload-image")
app.include_router(image_viewer.router, prefix="/image-viewer")
app.include_router(chat.router, prefix="/chat")



if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)