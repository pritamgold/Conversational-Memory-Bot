Project Title: Conversational Memory Bot – AI-Powered Photo Gallery Assistant
---



**A smart photo gallery application with a conversational AI assistant.**

The Conversational Photo Gallery is a web application that allows users to upload, manage, and explore a collection of photos using natural language queries. Powered by FastAPI, a modern Python web framework, and integrated with AI technologies like CLIP embeddings and a language model (Gemini), this project offers a seamless way to interact with your photo gallery through a chatbot interface.

## Features
- **Photo Upload**: Upload single or multiple images via a drag-and-drop interface.
- **Conversational AI**: Chat with an assistant to search for images by text queries (e.g., "show me some cake photos") or upload an image to find similar ones.
- **Advanced Search**: Uses CLIP embeddings for text-to-image similarity, enhanced with keyword filtering for precision.
- **Metadata Extraction**: Automatically generates descriptions, tags, dominant colors, and object labels for each photo.
- **Persistent Storage**: Stores images and their embeddings in ChromaDB for fast retrieval.
- **Responsive UI**: A clean, user-friendly front-end built with HTML, CSS, and JavaScript.

## Tech Stack
- **Backend**: FastAPI (Python)
- **AI Models**:
  - CLIP (`clip-ViT-B-32`) via `sentence_transformers` for text and image embeddings
  - Gemini (via `LLMService`) for natural language processing and image metadata generation
- **Database**: ChromaDB for vector storage and similarity search
- **Frontend**: HTML, CSS, JavaScript with Jinja2 templating
- **Dependencies**: PIL, FastAPI, SentenceTransformers

## Prerequisites
Before running the project, ensure you have the following installed:
- Python 3.10
- pip (Python package manager)
- Git (optional, for cloning the repository)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone --single-branch -- branch pritam_30189_final_project https://github.com/BJIT-Academy-24/YSD_B4_AI_Pritam/tree/pritam_30189_final_project
   cd YSD_B4_AI_Pritam
   ```

2. **Set Up a Virtual Environment** (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Example `requirements.txt` (create this file if not present):
   ```
    fastapi[standard]
    pillow
    clip
    torch
    chromadb
    git+https://github.com/openai/CLIP.git
    google-generativeai
    python-dotenv
    sentence_transformers
   ```

4. **Configure Environment Variables**:
   - Create a `.env` file in the root directory:
     ```bash
     GEMINI_API_KEY=your_gemini_api_key_here
     ```
   - Replace `your_gemini_api_key_here` with your actual Gemini API key.

## Running the Application

1. **Start the FastAPI Server**:
   ```bash
   cd conversational_photo_gallery
   python main.py
   ```

2. **Access the Application**:
   - Open your browser and navigate to `http://127.0.0.1:8000/` to see the upload page.
   - Use `/chat/` endpoint for the chatbot interface.

## Usage

### Uploading Photos
- Visit the homepage (`/`), drag and drop images into the upload area, or click to select files.
- Click "Upload Images" to process and store them in the gallery.
- The system generates embeddings and metadata (description, tags, etc.) for each photo.

### Chatting with the Assistant
- Navigate to the chat interface (e.g., `/chat/`).
- Type queries like:
  - "Show me some cake photos"
  - "Find river images"
- Upload an image to find similar photos in the gallery.
- The assistant responds with relevant images or a message if none are found (e.g., "There are no similar photos in the gallery").

## Project Structure
```
YSD_B4_AI_Pritam/
├── conversational_photo_gallery/
│   ├── config.py       # Configuration settings (directories, templates)
│   ├── constants.py    # Prompt templates for the LLM
│   ├── dependencies.py # Dependency injection utilities
│   ├── models.py       # Pydantic models (e.g., ChatResponse, UploadResponse)
│   ├── services/       # Core logic and AI services
│   │   ├── chat_handler.py
│   │   ├── decision_maker.py
│   │   ├── database_manager.py
│   │   ├── embedding_generator.py
│   │   ├── file_manager.py
│   │   ├── image_processor.py
│   │   ├── image_uploader.py
│   │   └── llm_service.py
│   ├── routes/
│   │   ├── chat.py
│   │   ├── gallery.py
│   │   ├── homepage.py
│   │   ├── image-viewer.py
│   │   └── upload.py
│   ├── main.py         # main file   
│   ├── templates/          # HTML templates
│   ├── static/             # Static files
│   ├── images/             # Directory for uploaded images
│   ├── database/           # ChromaDB storage
│   │   └── chromadb/
│   └── .env                # Environment variables
├── requirements.txt    # Python dependencies
└── .gitignore          # gitignore file
            
```


## Known Issues
- **Upload Performance**: Uploading large images or many images at once can be slow due to sequential processing. Future improvements include async uploads and batch processing.
- **Search Accuracy**: Embedding-based search may occasionally miss nuanced queries; ongoing enhancements involve hybrid search techniques.

## Future Enhancements
- Add batch processing for image uploads and embeddings.
- Implement user authentication and personalized galleries.
- Enhance search with advanced filtering (e.g., by date, color).


## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


