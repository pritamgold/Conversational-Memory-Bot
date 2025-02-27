from conversational_photo_gallery.services.llm_service import LLMService
from conversational_photo_gallery.constants import PROMPT_TEMPLATES

def retrieve_decision(query: str) -> bool:
    """Decide if the query requires retrieving images from the database using an LLM.

    Args:
        query (str): The user's text query.

    Returns:
        bool: True if retrieval is needed, False if conversational response is sufficient.

    Raises:
        ValueError: If the LLM response is not 'yes' or 'no' or if an error occurs.
    """
    llm_service = LLMService()  # Instantiate the service
    prompt = PROMPT_TEMPLATES["RETRIEVED_DECISION_PROMPT"].format(query=query)
    try:
        decision = llm_service.generate_response(prompt).lower().strip()
        if decision not in ['yes', 'no']:
            raise ValueError(f"Unexpected LLM response: '{decision}'")
        return decision == 'yes'
    except Exception as e:
        raise ValueError(f"Error in retrieval decision: {str(e)}")
