
PROMPT_TEMPLATES = {
    "INITIAL_GREETING": (
        "Hello! I’m your Photo Gallery Assistant, here to help you explore and manage your photo collection. "
        "I can assist with finding images by descriptions or tags, describing uploaded photos, and showing similar images from the gallery. "
        "I can’t answer questions unrelated to the photo gallery, like weather or general knowledge queries—just ask me anything about your photos!"
    ),
    "CHATBOT_RESPONSE_PROMPT": (
        "Based on last user query generate a concise response"
    ),
    "IMAGE_SELECTION_PROMPT": (
    "Here is the query: '{query}':\n"
    "Here are some images retrieved based on the query: {retrieved_images}\n"
    "Considering the user's query, select the most relevant images to display. "
    "Relevance should be based on how well each image's description and tags match the query and conversation context. "
    "Respond with the numbers of the selected images, separated by commas (e.g., '1,3')."
    ),
    "NO_RESULT_RESPONSE": (
        "I couldn't find any photos matching '{query}'. Try different keywords or tags, or describe what you're looking for differently."
    ),
    "NO_SELECTION_RESPONSE": (
        "I found some images related to '{query}', but none seemed relevant enough to show. Would you like me to try something else?"
    ),
    "IMAGE_DESCRIPTION_PROMPT": (
        "Provide a concise, detailed description of this image in 2-3 sentences, "
        "focusing on key objects, actions, colors, the overall scene, texture (e.g., smooth, rough), "
        "and lighting conditions (e.g., bright, dim). For example: 'A bright red apple sits on a smooth "
        "wooden table under dim lighting, casting subtle shadows.'"
    ),
    "ASK_SIMILAR_IMAGES_PROMPT": (
        "Here’s a description of the image you uploaded: {description}\n"
        "Would you like to see similar images from the gallery?"
    ),
    "RETRIEVED_DECISION_PROMPT": (
        "Determine if the following query requires retrieving and displaying images from the database. "
        "Answer 'yes' if the query is asking to find, show, or display images based on some criteria, "
        "and 'no' if it's a general question or doesn't involve displaying images. Query: '{query}'\n"
        "Examples:\n- 'Show me beach images' -> yes\n- 'How many images are there?' -> no\n- "
        "'What is your name?' -> no\n- 'Can you help me find a specific image?' -> yes\n- "
        "Tell me a joke' -> no\n- 'Display photos of mountain sunsets.' -> yes\n- 'Show me a picture of a golden retriever.' -> yes\n"
        "- 'Find images of ancient Rome.' -> yes\n- 'Get me visuals of the Eiffel Tower at night.' -> yes\n"
        "- 'Can you show me landscape images?' -> yes\n- 'I want to see pictures of cherry blossoms in Japan.' -> yes\n"
        "- 'Let's visualize images of the Amazon rainforest.' -> yes\n- 'Image of a fluffy white cat.' -> yes\n"
        "- 'Picture of a crowded marketplace.' -> yes\n- 'Show me images with vibrant colors.' -> yes\n"
        "- 'How many pictures do you have of cars?' -> no\n- 'What kind of images can you show?' -> no\n"
        "- 'Tell me about the history of photography.' -> no\n- 'Can you download all beach images?' -> no\n"
        "- 'What are the most popular image formats?' -> no\n- 'Is it possible to search for images by color?' -> no\n"
        "- 'Do you store images in your database?' -> no\n- 'What is the resolution of your images?' -> no\n"
        "- 'Explain image processing to me.' -> no\n- 'Create a summary about beach images.' -> no\n"
        "If the query is ambiguous, assume 'no' unless it explicitly mentions "
        "images or visual content."
    ),
    "RESPONSE_TEXT_WITH_IMAGES": (
        "Here are some relevant images based on your query:"
    ),
    "RESPONSE_TEXT_WITH_IMAGES_MULTIMODAL": (
        "Here are some relevant images based on your query and uploaded image:"
    ),

}
