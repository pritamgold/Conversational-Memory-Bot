import os
from typing import Dict, List

from fastapi import HTTPException, UploadFile

from conversational_photo_gallery.models import ChatResponse
from conversational_photo_gallery.services.decision_maker import retrieve_decision
from conversational_photo_gallery.services.embedding_generator import EmbeddingGenerator
from conversational_photo_gallery.services.file_manager import FileManager
from conversational_photo_gallery.services.image_processor import ImageProcessor
from conversational_photo_gallery.services.llm_service import LLMService
from conversational_photo_gallery.constants import PROMPT_TEMPLATES

class ChatHandler:
    """Handles chat queries with text, image, or both, maintaining conversation history."""

    conversation_history: List[Dict[str, str]] = [
        {
            "role": "assistant",
            "content": PROMPT_TEMPLATES["INITIAL_GREETING"],
        }
    ]
    # prompt variables
    CHATBOT_RESPONSE_PROMPT = PROMPT_TEMPLATES["CHATBOT_RESPONSE_PROMPT"]
    IMAGE_SELECTION_PROMPT = PROMPT_TEMPLATES["IMAGE_SELECTION_PROMPT"]

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
        # append query to chat history
        self.conversation_history.append({"role": "user", "content": query})

        # make retrieved decision
        try:
            should_retrieve = retrieve_decision(query)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=f"Decision error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error in decision: {str(e)}")

        # only conversation
        if not should_retrieve:
            try:
                # build prompt with memory
                prompt = self.build_prompt() + ChatHandler.CHATBOT_RESPONSE_PROMPT

                # generate response
                response = self.llm_service.generate_response(prompt)

                # save response to chat history
                self.conversation_history.append(
                    {"role": "assistant", "content": response}
                )
                return ChatResponse(response=response)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"LLM error: {e}")

        # conversation with retrieving
        else:
            try:
                text_embedding = self.embedding_generator.generate_text_embedding(query)
                results = self.collection.query(
                    query_embeddings=[text_embedding],
                    n_results=self.n_results,
                )

                # extract image_id and metadata
                image_ids = results["ids"][0]
                metadatas = results["metadatas"][0]

                # Check if there is no results at all
                if not image_ids:
                    no_results_response = PROMPT_TEMPLATES['NO_RESULTS_RESPONSE'].format(query=query)
                    self.conversation_history.append(
                        {"role": "assistant", "content": no_results_response}
                    )
                    return ChatResponse(response=no_results_response, images=[])

                # extract retrieved image info
                image_info = [
                    {
                        "id": img_id,
                        "description": meta.get("description", ""),
                        "tags": meta.get("tags", ""),
                    }
                    for img_id, meta in zip(image_ids, metadatas)
                ]

                # Initialize an empty string to accumulate the formatted image information.
                retrieved_images = PROMPT_TEMPLATES['RESPONSE_TEXT_WITH_IMAGES']
                for idx, info in enumerate(image_info, 1):
                    retrieved_images += f"{idx}. Description: {info['description']}, Tags: {info['tags']}\n"

                #  build prompt to filter retrieved images
                prompt = (
                        self.build_prompt() +
                        ChatHandler.IMAGE_SELECTION_PROMPT.format( query=query, retrieved_images=retrieved_images)
                )

                # response to filter (e.g., '1,3')
                response = self.llm_service.generate_response(prompt)

                selected_indices = [int(idx) for idx in response.split(",") if idx.strip().isdigit()]
                selected_image_ids = [
                    image_info[idx - 1]["id"]
                    for idx in selected_indices
                    if 1 <= idx <= len(image_info)
                ]
                if not selected_image_ids:
                    no_selection_response = PROMPT_TEMPLATES['NO_SELECTION_RESPONSE'].format(query=query)
                    self.conversation_history.append(
                        {"role": "assistant", "content": no_selection_response}
                    )
                    return ChatResponse(response=no_selection_response, images=[])

                image_urls = [
                    f"/images/{os.path.basename(img_id)}" for img_id in selected_image_ids
                ]
                response_text = "Here are some relevant images:\n"
                for i, (img_id, info) in enumerate(
                        [(img_id, info) for img_id in selected_image_ids for info in image_info if
                         info["id"] == img_id], 1
                ):
                    response_text += f"{i}. {info['description']} \n"

                return ChatResponse(response=response_text, images = image_urls, )
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

            # generate image description
            prompt = PROMPT_TEMPLATES['IMAGE_DESCRIPTION_PROMPT']
            description = self.llm_service.generate_image_response(image_path, prompt)

            self.conversation_history.append(
                {"role": "user", "content": f"[Image uploaded: {description}]"}
            )
            response_message = PROMPT_TEMPLATES['ASK_SIMILAR_IMAGES_PROMPT'].format(description=description)
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

            image_prompt = PROMPT_TEMPLATES['IMAGE_DESCRIPTION_PROMPT']
            description = self.llm_service.generate_image_response(image_path, image_prompt)

            self.conversation_history.append(
                {"role": "user", "content": f"query: {query}, [Image uploaded: {description}]"}
            )

            # make retrieval decision
            should_retrieve = retrieve_decision(query)

            # only conversation
            if not should_retrieve:
                prompt = self.build_prompt() + ChatHandler.CHATBOT_RESPONSE_PROMPT
                response = self.llm_service.generate_image_response(image_path, prompt)
                self.conversation_history.append(
                    {"role": "assistant", "content": response}
                )
                os.remove(image_path)
                return ChatResponse(response=response)

            # conversation with retrieving
            else:
                # get embedding for retrieval
                text_embedding = self.embedding_generator.generate_text_embedding(query)
                image_embedding = self.embedding_generator.generate_embedding(image_path)

                # retrieve from text
                text_results = self.collection.query(query_embeddings=[text_embedding], n_results=self.n_results)
                text_image_ids = text_results["ids"][0]
                text_metadatas = text_results["metadatas"][0]

                # retrieve from image
                image_results = self.collection.query(query_embeddings=[image_embedding], n_results=self.n_results)
                image_image_ids = image_results["ids"][0]
                image_metadatas = image_results["metadatas"][0]

                # combine retrieved result
                combined_image_ids = list(set(text_image_ids + image_image_ids))
                combined_metadatas = []
                for img_id in combined_image_ids:
                    if img_id in text_image_ids:
                        idx = text_image_ids.index(img_id)
                        combined_metadatas.append(text_metadatas[idx])
                    elif img_id in image_image_ids:
                        idx = image_image_ids.index(img_id)
                        combined_metadatas.append(image_metadatas[idx])

                # extract from combined image
                image_info = [
                    {
                        "id": img_id,
                        "description": meta.get("description", ""),
                        "tags": meta.get("tags", ""),
                    }
                    for img_id, meta in zip(combined_image_ids, combined_metadatas)
                ]


                # Initialize an empty string to accumulate the formatted image information.
                retrieved_images = ""
                for idx, info in enumerate(image_info, 1):
                    retrieved_images += f"{idx}. Description: {info['description']}, Tags: {info['tags']}\n"

                # build prompt to filter retrieved images
                prompt = (
                        self.build_prompt() +
                        ChatHandler.IMAGE_SELECTION_PROMPT.format(query=query, retrieved_images=retrieved_images)
                )

                # filter retrieved image
                response = self.llm_service.generate_response(prompt)

                selected_indices = [
                    int(idx) for idx in response.split(",") if idx.strip().isdigit()
                ]
                selected_image_ids = [
                    image_info[idx - 1]["id"]
                    for idx in selected_indices
                    if 1 <= idx <= len(image_info)
                ]

                #get url to show images
                image_urls = [
                    f"/images/{os.path.basename(img_id)}" for img_id in selected_image_ids
                ]


                response_text = PROMPT_TEMPLATES['RESPONSE_TEXT_WITH_IMAGES_MULTIMODAL']
                for i, (img_id, info) in enumerate(
                        [(img_id, info) for img_id in selected_image_ids for info in image_info if
                         info["id"] == img_id], 1
                ):
                    response_text += f"{i}. {info['description']}\n"

                self.conversation_history.append(
                    {"role": "assistant", "content": response_text}
                )
                os.remove(image_path)
                return ChatResponse(response=response_text, images=image_urls)
        except Exception as e:
            if "image_path" in locals() and os.path.exists(image_path):
                os.remove(image_path)
            raise HTTPException(status_code=500, detail=f"Multimodal search error: {e}")
