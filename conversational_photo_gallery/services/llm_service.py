from dotenv import load_dotenv
import os
import google.generativeai as genai

class LLMService:
    """A service class to manage LLM configuration and response generation."""

    def __init__(self):
        """Initialize the LLMService with Gemini model configuration.

        Raises:
            ValueError: If GEMINI_API_KEY is missing in the environment.
        """
        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing in .env file.")

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def generate_response(self, prompt: str) -> str:
        """Generate a response from the LLM based on the given prompt.

        Args:
            prompt (str): The prompt to send to the LLM.

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
