import os
from typing import List, Dict
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

# Single global in-memory store for conversation history (clears on server restart)
conversation_history: List[Dict[str, str]] = [
    {"role": "assistant", "content": "Hello! I'm your AI assistant. How can I help you today?"}
]

def build_prompt(history: List[Dict[str, str]]) -> str:
    """Construct a prompt with the full conversation history."""
    prompt = ""
    for msg in history:
        prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
    return prompt

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
    """Handle chat queries with text, image, or both, maintaining session history."""
    if not query and not image:
        raise HTTPException(
            status_code=400, detail="Please provide a text query and/or an image."
        )

    # Initialize services
    image_processor = ImageProcessor()
    llm_service = LLMService()
    n_results = 5

    # --- TEXT-ONLY SEARCH ---
    if query and not image:
        # Add user query to history
        conversation_history.append({"role": "user", "content": query})

        # Step 1: Decide if retrieval is needed
        try:
            should_retrieve = retrieve_decision(query)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Decision error: {e}")

        # Step 2: Conversational response only
        if not should_retrieve:
            try:
                prompt = build_prompt(conversation_history) + "Assistant: "
                response = llm_service.generate_response(prompt)
                conversation_history.append({"role": "assistant", "content": response})
                return JSONResponse(content={"response": response})
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"LLM error: {e}")

        # Step 3: Retrieve and select images
        else:
            try:
                text_embedding = image_processor.generate_text_embedding(query)
                results = collection.query(
                    query_embeddings=[text_embedding],
                    n_results=n_results,
                )
                image_ids = results['ids'][0]
                metadatas = results['metadatas'][0]

                image_info = [
                    {
                        "id": img_id,
                        "description": meta.get("description", ""),
                        "tags": meta.get("tags", "")
                    }
                    for img_id, meta in zip(image_ids, metadatas)
                ]

                prompt = (
                    build_prompt(conversation_history) +
                    "Assistant: Here are some images that might be relevant:\n"
                )
                for idx, info in enumerate(image_info, 1):
                    prompt += f"{idx}. Description: {info['description']}, Tags: {info['tags']}\n"
                prompt += (
                    "\nBased on the query and conversation history, select the most relevant images "
                    "to show. Respond with the numbers of the images to display (e.g., '1,3')."
                )

                response = llm_service.generate_response(prompt)
                selected_indices = [
                    int(idx) for idx in response.split(',') if idx.strip().isdigit()
                ]
                selected_image_ids = [
                    image_info[idx-1]['id'] for idx in selected_indices
                    if 1 <= idx <= len(image_info)
                ]

                image_urls = [f"/images/{os.path.basename(img_id)}" for img_id in selected_image_ids]
                response_text = "Here are some relevant images:"
                conversation_history.append({"role": "assistant", "content": f"{response_text} [Images shown]"})
                return JSONResponse(content={"response": response_text, "images": image_urls})
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Image selection error: {e}")

    # --- IMAGE-ONLY SEARCH ---
    if image and not query:
        try:
            from conversational_photo_gallery.services.file_manager import FileManager
            file_manager = FileManager()
            image_path = file_manager.save_image(image)

            prompt = (
                "Provide a concise, detailed description of this image in 2-3 sentences, "
                "focusing on key objects, actions, colors, and the overall scene."
            )
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            description = llm_service.generate_response([
                prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])

            conversation_history.append({"role": "user", "content": f"[Image uploaded: {description}]"})
            response_message = f"{description}\n\nWould you like to see similar images from the gallery?"
            conversation_history.append({"role": "assistant", "content": response_message})
            os.remove(image_path)
            return JSONResponse(content={"response": response_message})
        except Exception as e:
            if 'image_path' in locals() and os.path.exists(image_path):
                os.remove(image_path)
            raise HTTPException(status_code=500, detail=f"Image-only search error: {e}")

    # --- MULTIMODAL SEARCH (BOTH TEXT AND IMAGE) ---
    if query and image:
        try:
            from conversational_photo_gallery.services.file_manager import FileManager
            file_manager = FileManager()
            image_path = file_manager.save_image(image)

            # Generate image description
            image_prompt = (
                "Provide a concise, detailed description of this image in 2-3 sentences, "
                "focusing on key objects, actions, colors, and the overall scene."
            )
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            description = llm_service.generate_response([
                image_prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])

            # Add user query and image description to history
            conversation_history.append({"role": "user", "content": f"{query} [Image uploaded: {description}]"})

            # Step 1: Decide if retrieval is needed
            should_retrieve = retrieve_decision(query)

            # Step 2: No retrieval - send query and image to LLM
            if not should_retrieve:
                prompt = build_prompt(conversation_history) + "Assistant: "
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                response = llm_service.generate_response([
                    prompt,
                    {"mime_type": "image/jpeg", "data": image_data}
                ])
                conversation_history.append({"role": "assistant", "content": response})
                os.remove(image_path)
                return JSONResponse(content={"response": response})

            # Step 3: Retrieval - retrieve results separately and combine
            else:
                text_embedding = image_processor.generate_text_embedding(query)
                image_embedding = image_processor.generate_embedding(image_path)

                text_results = collection.query(
                    query_embeddings=[text_embedding],
                    n_results=n_results,
                )
                text_image_ids = text_results['ids'][0]
                text_metadatas = text_results['metadatas'][0]

                image_results = collection.query(
                    query_embeddings=[image_embedding],
                    n_results=n_results,
                )
                image_image_ids = image_results['ids'][0]
                image_metadatas = image_results['metadatas'][0]

                combined_image_ids = list(set(text_image_ids + image_image_ids))
                combined_metadatas = []
                for img_id in combined_image_ids:
                    if img_id in text_image_ids:
                        idx = text_image_ids.index(img_id)
                        combined_metadatas.append(text_metadatas[idx])
                    elif img_id in image_image_ids:
                        idx = image_image_ids.index(img_id)
                        combined_metadatas.append(image_metadatas[idx])

                image_info = [
                    {
                        "id": img_id,
                        "description": meta.get("description", ""),
                        "tags": meta.get("tags", "")
                    }
                    for img_id, meta in zip(combined_image_ids, combined_metadatas)
                ]

                prompt = (
                    build_prompt(conversation_history) +
                    "Assistant: Here are some images retrieved based on the query and uploaded image:\n"
                )
                for idx, info in enumerate(image_info, 1):
                    prompt += f"{idx}. Description: {info['description']}, Tags: {info['tags']}\n"
                prompt += (
                    "\nBased on the query, uploaded image, and conversation history, select the most "
                    "relevant images to show. Respond with the numbers of the images to display (e.g., '1,3')."
                )

                response = llm_service.generate_response(prompt)
                selected_indices = [
                    int(idx) for idx in response.split(',') if idx.strip().isdigit()
                ]
                selected_image_ids = [
                    image_info[idx-1]['id'] for idx in selected_indices
                    if 1 <= idx <= len(image_info)
                ]

                image_urls = [f"/images/{os.path.basename(img_id)}" for img_id in selected_image_ids]
                response_text = "Here are some relevant images based on your query and uploaded image:"
                conversation_history.append({"role": "assistant", "content": f"{response_text} [Images shown]"})
                os.remove(image_path)
                return JSONResponse(content={"response": response_text, "images": image_urls})

        except Exception as e:
            if 'image_path' in locals() and os.path.exists(image_path):
                os.remove(image_path)
            raise HTTPException(status_code=500, detail=f"Multimodal search error: {e}")