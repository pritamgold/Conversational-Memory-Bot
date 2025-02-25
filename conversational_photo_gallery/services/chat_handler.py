import os
from typing import Dict, List

from fastapi import HTTPException, UploadFile

from conversational_photo_gallery.models import ChatResponse
from conversational_photo_gallery.services.decision_maker import retrieve_decision
from conversational_photo_gallery.services.embedding_generator import EmbeddingGenerator
from conversational_photo_gallery.services.file_manager import FileManager
from conversational_photo_gallery.services.image_processor import ImageProcessor
from conversational_photo_gallery.services.llm_service import LLMService

class ChatHandler:
    """Handles chat queries with text, image, or both, maintaining conversation history."""

    conversation_history: List[Dict[str, str]] = [
        {
            "role": "assistant",
            "content": "Hello! I'm your AI assistant. How can I help you today?",
        }
    ]

    def __init__(self, collection) -> None:
        """Initialize ChatHandler with dependencies.

        Args:
            collection: ChromaDB collection instance for querying images.
        """
        self.collection = collection
        self.image_processor = ImageProcessor()
        self.embedding_generator = EmbeddingGenerator()
        self.llm_service = LLMService()
        self.file_manager = FileManager()
        self.n_results = 5

    def build_prompt(self) -> str:
        """Construct a prompt with the full conversation history.

        Returns:
            str: The concatenated conversation history as a prompt.
        """
        prompt = ""
        for msg in self.conversation_history:
            prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
        return prompt

    def handle_text_query(self, query: str) -> ChatResponse:
        """Handle text-only queries.

        Args:
            query: The user's text query.

        Returns:
            ChatResponse: The assistant's response, possibly with image URLs.

        Raises:
            HTTPException: If processing the query fails.
        """
        self.conversation_history.append({"role": "user", "content": query})
        try:
            should_retrieve = retrieve_decision(query)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Decision error: {e}")

        if not should_retrieve:
            try:
                prompt = self.build_prompt() + "Assistant: "
                response = self.llm_service.generate_response(prompt)
                self.conversation_history.append(
                    {"role": "assistant", "content": response}
                )
                return ChatResponse(response=response)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"LLM error: {e}")
        else:
            try:
                text_embedding = self.embedding_generator.generate_text_embedding(
                    query
                )
                results = self.collection.query(
                    query_embeddings=[text_embedding],
                    n_results=self.n_results,
                )
                image_ids = results["ids"][0]
                metadatas = results["metadatas"][0]

                image_info = [
                    {
                        "id": img_id,
                        "description": meta.get("description", ""),
                        "tags": meta.get("tags", ""),
                    }
                    for img_id, meta in zip(image_ids, metadatas)
                ]

                prompt = (
                    self.build_prompt()
                    + "Assistant: Here are some images that might be relevant:\n"
                )
                for idx, info in enumerate(image_info, 1):
                    prompt += f"{idx}. Description: {info['description']}, Tags: {info['tags']}\n"
                prompt += (
                    "\nBased on the query and conversation history, select the most relevant images "
                    "to show. Respond with the numbers of the images to display (e.g., '1,3')."
                )

                response = self.llm_service.generate_response(prompt)
                selected_indices = [
                    int(idx) for idx in response.split(",") if idx.strip().isdigit()
                ]
                selected_image_ids = [
                    image_info[idx - 1]["id"]
                    for idx in selected_indices
                    if 1 <= idx <= len(image_info)
                ]

                image_urls = [
                    f"/images/{os.path.basename(img_id)}" for img_id in selected_image_ids
                ]
                response_text = "Here are some relevant images:"
                self.conversation_history.append(
                    {"role": "assistant", "content": f"{response_text} [Images shown]"}
                )
                return ChatResponse(response=response_text, images=image_urls)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Image selection error: {e}")

    def handle_image_query(self, image: UploadFile) -> ChatResponse:
        """Handle image-only queries.

        Args:
            image: The uploaded image file.

        Returns:
            ChatResponse: The assistant's response describing the image.

        Raises:
            HTTPException: If processing the image fails.
        """
        try:
            image_path = self.file_manager.save_image(image)

            prompt = (
                "Provide a concise, detailed description of this image in 2-3 sentences, "
                "focusing on key objects, actions, colors, and the overall scene."
            )
            description = self.llm_service.generate_image_response(image_path, prompt)

            self.conversation_history.append(
                {"role": "user", "content": f"[Image uploaded: {description}]"}
            )
            response_message = f"{description}\n\nWould you like to see similar images from the gallery?"
            self.conversation_history.append(
                {"role": "assistant", "content": response_message}
            )
            os.remove(image_path)
            return ChatResponse(response=response_message)
        except Exception as e:
            if "image_path" in locals() and os.path.exists(image_path):
                os.remove(image_path)
            raise HTTPException(status_code=500, detail=f"Image-only search error: {e}")

    def handle_multimodal_query(self, query: str, image: UploadFile) -> ChatResponse:
        """Handle queries with both text and image.

        Args:
            query: The user's text query.
            image: The uploaded image file.

        Returns:
            ChatResponse: The assistant's response, possibly with image URLs.

        Raises:
            HTTPException: If processing the multimodal query fails.
        """
        try:
            image_path = self.file_manager.save_image(image)

            image_prompt = (
                "Provide a concise, detailed description of this image in 2-3 sentences, "
                "focusing on key objects, actions, colors, and the overall scene."
            )
            description = self.llm_service.generate_image_response(
                image_path, image_prompt
            )

            self.conversation_history.append(
                {"role": "user", "content": f"{query} [Image uploaded: {description}]"}
            )

            should_retrieve = retrieve_decision(query)

            if not should_retrieve:
                prompt = self.build_prompt() + "Assistant: "
                response = self.llm_service.generate_image_response(image_path, prompt)
                self.conversation_history.append(
                    {"role": "assistant", "content": response}
                )
                os.remove(image_path)
                return ChatResponse(response=response)
            else:
                text_embedding = self.embedding_generator.generate_text_embedding(
                    query
                )
                image_embedding = self.embedding_generator.generate_embedding(
                    image_path
                )

                text_results = self.collection.query(
                    query_embeddings=[text_embedding],
                    n_results=self.n_results,
                )
                text_image_ids = text_results["ids"][0]
                text_metadatas = text_results["metadatas"][0]

                image_results = self.collection.query(
                    query_embeddings=[image_embedding],
                    n_results=self.n_results,
                )
                image_image_ids = image_results["ids"][0]
                image_metadatas = image_results["metadatas"][0]

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
                        "tags": meta.get("tags", ""),
                    }
                    for img_id, meta in zip(combined_image_ids, combined_metadatas)
                ]

                prompt = (
                    self.build_prompt()
                    + "Assistant: Here are some images retrieved based on the query and uploaded image:\n"
                )
                for idx, info in enumerate(image_info, 1):
                    prompt += f"{idx}. Description: {info['description']}, Tags: {info['tags']}\n"
                prompt += (
                    "\nBased on the query, uploaded image, and conversation history, select the most "
                    "relevant images to show. Respond with the numbers of the images to display (e.g., '1,3')."
                )

                response = self.llm_service.generate_response(prompt)
                selected_indices = [
                    int(idx) for idx in response.split(",") if idx.strip().isdigit()
                ]
                selected_image_ids = [
                    image_info[idx - 1]["id"]
                    for idx in selected_indices
                    if 1 <= idx <= len(image_info)
                ]

                image_urls = [
                    f"/images/{os.path.basename(img_id)}" for img_id in selected_image_ids
                ]
                response_text = "Here are some relevant images based on your query and uploaded image:"
                self.conversation_history.append(
                    {"role": "assistant", "content": f"{response_text} [Images shown]"}
                )
                os.remove(image_path)
                return ChatResponse(response=response_text, images=image_urls)
        except Exception as e:
            if "image_path" in locals() and os.path.exists(image_path):
                os.remove(image_path)
            raise HTTPException(status_code=500, detail=f"Multimodal search error: {e}")
