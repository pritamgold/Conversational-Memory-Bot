from conversational_photo_gallery.services.llm_service import LLMService


def retrieve_decision(query: str) -> bool:
    """Decide if the query requires retrieving images from the database using an LLM.

    Args:
        query (str): The user's text query.

    Returns:
        bool: True if retrieval is needed, False if conversational response is sufficient.

    Raises:
        ValueError: If the LLM response is not 'yes' or 'no'.
    """
    llm_service = LLMService()  # Instantiate the service
    prompt = (
        f"Determine if the following query requires retrieving images from a database. "
        f"Answer only with 'yes' if the query implies retrieving images, otherwise 'no'. "
        f"Query: '{query}'"
    )
    decision = llm_service.generate_response(prompt).lower()

    if decision not in ['yes', 'no']:
        raise ValueError(f"Unexpected LLM response: {decision}")

    return decision == 'yes'