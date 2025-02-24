import os
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from conversational_photo_gallery.dependencies import get_collection
from conversational_photo_gallery.services.image_processor import ImageProcessor
from conversational_photo_gallery.services.decision_maker import retrieve_decision
from conversational_photo_gallery.services.llm_service import LLMService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def chat(request: Request):
    """Render the chat interface."""
    return templates.TemplateResponse("chat.html", {"request": request})

@router.post("/")
async def chat(
    query: str = Form(None),
    image: UploadFile = File(None),
    collection=Depends(get_collection),
):
    """Handle chat queries with text, image, or both."""
    if not query and not image:
        raise HTTPException(
            status_code=400, detail="Please provide a text query and/or an image."
        )

    # Initialize ImageProcessor and LLMService directly
    image_processor = ImageProcessor()
    llm_service = LLMService()
    n_results = 5

    # --- TEXT-ONLY SEARCH ---
    if query and not image:
        # Step 1: Decide if retrieval is needed
        try:
            should_retrieve = retrieve_decision(query)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Decision error: {e}")

        # Step 2: Conversational response only
        if not should_retrieve:
            try:
                response = llm_service.generate_response(query)
                return JSONResponse(content={"response": response})
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"LLM error: {e}")

        # Step 3: Retrieve and select images
        else:
            # Generate text embedding
            try:
                text_embedding = image_processor.generate_text_embedding(query)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Embedding error: {e}")

            # Retrieve similar images from ChromaDB
            results = collection.query(
                query_embeddings=[text_embedding],
                n_results=n_results,
            )
            image_ids = results['ids'][0]
            metadatas = results['metadatas'][0]

            # Format image information for LLM
            image_info = [
                {
                    "id": img_id,
                    "description": meta.get("description", ""),
                    "tags": meta.get("tags", "")
                }
                for img_id, meta in zip(image_ids, metadatas)
            ]

            # Prompt LLM to select relevant images
            prompt = (
                f"User query: '{query}'\n\nHere are some images that might be relevant:\n"
            )
            for idx, info in enumerate(image_info, 1):
                prompt += f"{idx}. Description: {info['description']}, Tags: {info['tags']}\n"
            prompt += (
                "\nBased on the query, select the most relevant images to show. "
                "Respond with the numbers of the images to display (e.g., '1,3')."
            )

            try:
                response = llm_service.generate_response(prompt)
                selected_indices = [
                    int(idx) for idx in response.split(',') if idx.strip().isdigit()
                ]
                selected_image_ids = [
                    image_info[idx-1]['id'] for idx in selected_indices
                    if 1 <= idx <= len(image_info)
                ]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Image selection error: {e}")

            # Prepare response with image URLs
            image_urls = [f"/images/{os.path.basename(img_id)}" for img_id in selected_image_ids]
            return JSONResponse(content={
                "response": "Here are some relevant images:",
                "images": image_urls
            })

    # --- IMAGE-ONLY SEARCH ---
    if image and not query:
        raise HTTPException(status_code=501, detail="Image-only search not implemented yet.")

    # --- MULTIMODAL SEARCH (BOTH TEXT AND IMAGE) ---
    if query and image:
        raise HTTPException(status_code=501, detail="Multimodal search not implemented yet.")