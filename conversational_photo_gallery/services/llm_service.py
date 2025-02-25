import os
from typing import Dict, List, Union

import google.generativeai as genai
from dotenv import load_dotenv


class LLMService:
    """Manages configuration and response generation for the Gemini LLM."""

    def __init__(self) -> None:
        """Initialize the LLMService with Gemini model configuration.

        Raises:
            ValueError: If GEMINI_API_KEY is missing in the environment.
        """
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing in .env file.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")

    def generate_response(
        self, prompt: Union[str, List[Union[str, Dict[str, str]]]]
    ) -> str:
        """Generate a response from the LLM based on the given prompt.

        Args:
            prompt: A string prompt or a list containing a string prompt and image data dict
                    (e.g., {"mime_type": "image/jpeg", "data": bytes}).

        Returns:
            str: The generated response text.

        Raises:
            ValueError: If the LLM fails to generate a response.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise ValueError(f"Failed to generate response: {e}")

    def generate_image_response(self, image_path: str, prompt: str) -> str:
        """Generate a response for an image with a given prompt using Gemini.

        Args:
            image_path: Path to the image file.
            prompt: The prompt to send alongside the image.

        Returns:
            str: The generated response text.

        Raises:
            ValueError: If querying Gemini with the image fails.
        """
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            response = self.model.generate_content(
                [prompt, {"mime_type": "image/jpeg", "data": image_data}]
            )
            return response.text.strip()
        except Exception as e:
            raise ValueError(f"Failed to query Gemini for {image_path}: {e}")
