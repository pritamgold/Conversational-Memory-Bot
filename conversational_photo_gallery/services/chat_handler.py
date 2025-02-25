import os
from typing import List, Dict
from fastapi import HTTPException, UploadFile

from conversational_photo_gallery.models import ChatResponse
from conversational_photo_gallery.services.image_processor import ImageProcessor
from conversational_photo_gallery.services.llm_service import LLMService
from conversational_photo_gallery.services.decision_maker import retrieve_decision
from conversational_photo_gallery.services.file_manager import FileManager


class ChatHandler:
    """Handles chat queries with text, image, or both, maintaining conversation history."""

    conversation_history: List[Dict[str, str]] = [
        {"role": "assistant", "content": "Hello! I'm your AI assistant. How can I help you today?"}
    ]

    def __init__(self, collection):
        """Initialize ChatHandler with dependencies."""
        self.collection = collection
        self.image_processor = ImageProcessor()
        self.llm_service = LLMService()
        self.file_manager = FileManager()
        self.n_results = 5

    def build_prompt(self) -> str:
        """Construct a prompt with the full conversation history."""
        return "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}" for msg in self.conversation_history
        )

    def handle_text_query(self, query: str) -> ChatResponse:
        """Handle text-only queries."""
        self.conversation_history.append({"role": "user", "content": query})

        try:
            should_retrieve = retrieve_decision(query)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Decision error: {exc}")

        if not should_retrieve:
            return self._generate_llm_response()
        return self._retrieve_images(query)

    def _generate_llm_response(self) -> ChatResponse:
        """Generate a response from the LLM based on conversation history."""
        try:
            prompt = self.build_prompt() + "\nAssistant: "
            response = self.llm_service.generate_response(prompt)
            self.conversation_history.append({"role": "assistant", "content": response})
            return ChatResponse(response=response)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"LLM error: {exc}")

    def _retrieve_images(self, query: str) -> ChatResponse:
        """Retrieve relevant images based on the query."""
        try:
            text_embedding = self.image_processor.generate_text_embedding(query)
            results = self.collection.query(query_embeddings=[text_embedding], n_results=self.n_results)
            image_info = [
                {
                    "id": img_id,
                    "description": meta.get("description", ""),
                    "tags": meta.get("tags", "")
                }
                for img_id, meta in zip(results['ids'][0], results['metadatas'][0])
            ]

            response_text, image_urls = self._select_images(image_info)
            return ChatResponse(response=response_text, images=image_urls)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Image selection error: {exc}")

    def _select_images(self, image_info: List[Dict[str, str]]) -> (str, List[str]):
        """Let the LLM decide which images are most relevant."""
        prompt = self.build_prompt() + "\nAssistant: Here are some images that might be relevant:\n"
        prompt += "\n".join(
            f"{idx + 1}. Description: {info['description']}, Tags: {info['tags']}"
            for idx, info in enumerate(image_info)
        )
        prompt += "\nSelect the most relevant images by responding with numbers (e.g., '1,3')."

        response = self.llm_service.generate_response(prompt)
        selected_indices = [int(idx) for idx in response.split(',') if idx.strip().isdigit()]
        selected_image_ids = [image_info[idx - 1]['id'] for idx in selected_indices if 1 <= idx <= len(image_info)]
        image_urls = [f"/images/{os.path.basename(img_id)}" for img_id in selected_image_ids]

        return "Here are some relevant images:", image_urls

    def handle_image_query(self, image: UploadFile) -> ChatResponse:
        """Handle image-only queries."""
        try:
            image_path = self.file_manager.save_image(image)
            response_message = self._describe_image(image_path)
            os.remove(image_path)
            return ChatResponse(response=response_message)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Image-only search error: {exc}")

    def _describe_image(self, image_path: str) -> str:
        """Generate a description for the uploaded image."""
        prompt = "Provide a concise description of this image in 2-3 sentences."
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        description = self.llm_service.generate_response([
            prompt, {"mime_type": "image/jpeg", "data": image_data}
        ])

        self.conversation_history.append({"role": "user", "content": f"[Image uploaded: {description}]"})
        return f"{description}\n\nWould you like to see similar images from the gallery?"

    def handle_multimodal_query(self, query: str, image: UploadFile) -> ChatResponse:
        """Handle queries with both text and image."""
        try:
            image_path = self.file_manager.save_image(image)
            description = self._describe_image(image_path)
            self.conversation_history.append({"role": "user", "content": f"{query} [Image uploaded: {description}]"})

            should_retrieve = retrieve_decision(query)
            if not should_retrieve:
                response = self._generate_llm_response()
            else:
                response = self._retrieve_images(query)

            os.remove(image_path)
            return response
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Multimodal search error: {exc}")
