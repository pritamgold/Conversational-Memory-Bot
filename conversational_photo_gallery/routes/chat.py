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

    if image and not query:
        try:
            # Save the uploaded image temporarily using FileManager
            from conversational_photo_gallery.services.file_manager import FileManager
            file_manager = FileManager()
            image_path = file_manager.save_image(image)

            # Generate a description using LLMService
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

            # Clean up the temporary file
            os.remove(image_path)

            # Return description and ask user about similar images
            response_message = (
                f"{description}\n\nWould you like to see similar images from the gallery?"
            )
            return JSONResponse(content={"response": response_message})

        except Exception as e:
            # Clean up in case of failure
            if 'image_path' in locals() and os.path.exists(image_path):
                os.remove(image_path)
            raise HTTPException(status_code=500, detail=f"Image-only search error: {e}")

    # --- MULTIMODAL SEARCH (BOTH TEXT AND IMAGE) ---
    if query and image:
        try:
            # Step 1: Decide if retrieval is needed using the text query
            should_retrieve = retrieve_decision(query)

            # Step 2: No retrieval - send query and image to LLM for response
            if not should_retrieve:
                from conversational_photo_gallery.services.file_manager import FileManager
                file_manager = FileManager()
                image_path = file_manager.save_image(image)

                prompt = f"User query: '{query}'\nRespond based on this query and the provided image."
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                response = llm_service.generate_response([
                    prompt,
                    {"mime_type": "image/jpeg", "data": image_data}
                ])

                os.remove(image_path)  # Clean up temporary file
                return JSONResponse(content={"response": response})

            # Step 3: Retrieval - retrieve results separately and combine
            else:
                from conversational_photo_gallery.services.file_manager import FileManager
                file_manager = FileManager()
                image_path = file_manager.save_image(image)

                # Generate embeddings
                text_embedding = image_processor.generate_text_embedding(query)
                image_embedding = image_processor.generate_embedding(image_path)

                # Retrieve results for text query
                text_results = collection.query(
                    query_embeddings=[text_embedding],
                    n_results=n_results,
                )
                text_image_ids = text_results['ids'][0]
                text_metadatas = text_results['metadatas'][0]

                # Retrieve results for image
                image_results = collection.query(
                    query_embeddings=[image_embedding],
                    n_results=n_results,
                )
                image_image_ids = image_results['ids'][0]
                image_metadatas = image_results['metadatas'][0]

                # Combine results (union of image IDs with metadata)
                combined_image_ids = list(set(text_image_ids + image_image_ids))
                combined_metadatas = []
                for img_id in combined_image_ids:
                    if img_id in text_image_ids:
                        idx = text_image_ids.index(img_id)
                        combined_metadatas.append(text_metadatas[idx])
                    elif img_id in image_image_ids:
                        idx = image_image_ids.index(img_id)
                        combined_metadatas.append(image_metadatas[idx])

                # Format image information for LLM
                image_info = [
                    {
                        "id": img_id,
                        "description": meta.get("description", ""),
                        "tags": meta.get("tags", "")
                    }
                    for img_id, meta in zip(combined_image_ids, combined_metadatas)
                ]

                # Prompt LLM to select relevant images
                prompt = (
                    f"User query: '{query}'\n\nHere are some images retrieved based "
                    f"on the query and the uploaded image:\n"
                )
                for idx, info in enumerate(image_info, 1):
                    prompt += f"{idx}. Description: {info['description']}, Tags: {info['tags']}\n"
                prompt += (
                    "\nBased on the query and the uploaded image, select the most relevant images "
                    "to show. Respond with the numbers of the images to display (e.g., '1,3')."
                )

                response = llm_service.generate_response(prompt)
                selected_indices = [
                    int(idx) for idx in response.split(',') if idx.strip().isdigit()
                ]
                selected_image_ids = [
                    image_info[idx - 1]['id'] for idx in selected_indices
                    if 1 <= idx <= len(image_info)
                ]

                # Clean up temporary file
                os.remove(image_path)

                # Prepare response with image URLs
                image_urls = [f"/images/{os.path.basename(img_id)}" for img_id in selected_image_ids]
                return JSONResponse(content={
                    "response": "Here are some relevant images based on your query and uploaded image:",
                    "images": image_urls
                })

        except Exception as e:
            # Clean up in case of failure
            if 'image_path' in locals() and os.path.exists(image_path):
                os.remove(image_path)
            raise HTTPException(status_code=500, detail=f"Multimodal search error: {e}")