# ConsultAID: A Universal Conversational AI Platform

ConsultAID is a sophisticated, modular, and multilingual chatbot powered by a Retrieval-Augmented Generation (RAG) architecture. It is designed to be a universal platform that can be easily adapted to any domain by providing it with a custom knowledge base. The current MVP is configured as a friendly and helpful student support assistant for a university.

## Appendix
  * [Features](https://github.com/CodeCrew0/ConsultAID/new/main?filename=README.md#features)
  * [Architecture Overview](https://github.com/CodeCrew0/ConsultAID/new/main?filename=README.md#architecture-overview)
  * [Tech Stack](https://github.com/CodeCrew0/ConsultAID/new/main?filename=README.md#technology-stack)
  * [Test Hardware](https://github.com/CodeCrew0/ConsultAID/new/main?filename=README.md#test-hardware)
  * [Limitations](https://github.com/CodeCrew0/ConsultAID/new/main?filename=README.md#limitations)
  * [Project Structure](https://github.com/CodeCrew0/ConsultAID/new/main?filename=README.md#project-structure)
  * [Getting Started](https://github.com/CodeCrew0/ConsultAID/new/main?filename=README.md#getting-started)
  * [Usage](https://github.com/CodeCrew0/ConsultAID/new/main?filename=README.md#usage)
  * [Front-end Integration](https://github.com/CodeCrew0/ConsultAID/new/main?filename=README.md#front-end-integration-chatbotjs)
  * [API Endpoints](https://github.com/CodeCrew0/ConsultAID/README.md#api-endpoints)
  * [Customization](https://github.com/CodeCrew0/ConsultAID/new/main?filename=README.md#-customization)

## Features

  * **Retrieval-Augmented Generation (RAG)**: Provides accurate, context-aware answers by retrieving information from a local knowledge base of PDF documents.
  * **Modular Architecture**: A clear separation of concerns between the web server (`app.py`), the core RAG logic (`model_loader.py`), and the translation service (`translation_service.py`).
  * **Local First**: Utilizes local language models via Ollama (`qwen2.5:3b`), ensuring data privacy and reducing reliance on external APIs.
  * **Multilingual Support**: Automatically detects the user's language and provides translations for both incoming queries and outgoing responses, thanks to the integrated `TranslationService`.
  * **Robust Session Management**: Maintains separate conversational contexts for each user and includes an automatic cleanup mechanism for inactive sessions to manage resources efficiently.
  * **Customizable Persona**: The chatbot's personality, tone, and operational guidelines are defined in a simple text file (`SYSTEM_MODELFILE.txt`), making it easy to customize.
  * **RESTful API**: Exposes a clean and simple API for easy integration with any front-end application.



## Architecture Overview

The system is composed of three main components that work together to deliver a seamless conversational experience:

1.  **Flask Web Server (`app.py`)**: This is the front door of the application. It handles all incoming HTTP requests, manages user sessions, and communicates with the RAG core. It's responsible for initializing new sessions and routing user queries.

2.  **Conversational RAG Core (`model_loader.py`)**: This is the brain of the operation. The `ConversationalRAG` class encapsulates all the logic for the RAG pipeline. When a session is initialized, it loads the language model, creates a vector store from the documents in the `/documents` folder, and sets up a LangChain QA chain. It also manages conversation history to provide context to the LLM.

3.  **Translation Service (`translation_service.py`)**: This utility module provides the multilingual capabilities. It detects the language of an incoming query, translates it to English for the RAG core to process, and then translates the English response back to the user's original language.

### How a Query is Processed

1.  A user sends a query to the `/api/ask` endpoint on the Flask server.
2.  The server identifies the user's session and forwards the query to the corresponding `ConversationalRAG` instance.
3.  The `TranslationService` detects the query's language. If it's not English, the query is translated.
4.  The RAG instance appends the recent conversation history to the query for context.
5.  The query is sent to the vector store (FAISS) to find the most relevant document chunks.
6.  The LLM (Ollama) receives the query, the conversational context, and the retrieved document chunks to generate an answer in English.
7.  If needed, the `TranslationService` translates the English answer back to the user's language.
8.  The final response is sent back to the user through the API.



## Technology Stack

  * **Backend Framework**: Flask
  * **LLM Serving**: Ollama
  * **Core AI/RAG Framework**: LangChain
  * **Vector Store**: FAISS (Facebook AI Similarity Search)
  * **Embeddings Model**: `sentence-transformers/all-mpnet-base-v2`
  * **Translation**: `googletrans`, `langdetect`



## Test Hardware

This application was developed and tested on the following hardware. Performance may vary on different configurations.

  * **CPU**: AMD Ryzen 7 7840HS w/ Radeon 780M Graphics
      * **Cores**: 8
      * **Logical Processors**: 16
      * **Base Speed**: 3.80 GHz
  * **Memory**: 16.0 GB DDR5
      * **Speed**: 5600 MT/s
  * **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU
      * **Dedicated VRAM**: 6.0 GB



## Limitations

  * **Hardware Dependency**: The performance and quality of the chatbot are directly influenced by the underlying hardware. While the default model (`qwen2.5:3b`) is lightweight, using larger and more powerful language models will significantly boost the output quality but will require a more robust hardware setup (e.g., more RAM and a powerful GPU with more VRAM).



## Project Structure

```
ConsultAID/
│
├── app.py                  # Flask web server and API endpoints
├── model_loader.py         # Core RAG logic and session handling
├── translation_service.py  # Language detection and translation
├── SYSTEM_MODELFILE.txt    # Defines the chatbot's persona and rules
│
├── documents/              # Place your PDF knowledge base files here
│   └── *.pdf
│
├── user_sessions/          # Stores active session data (auto-generated)
│   └── <session_id>/
│       ├── conversations.json
│       └── faiss_index/
│
└── templates/              # Mockup front-end files for testing
    ├── index.html
    └── chatbot.js
```


## Getting Started

### Prerequisites

  * Python 3.9+
  * [Ollama](https://ollama.com/) installed and running.

### 1\. Setup the Language Model

First, pull the language model that the application uses:

```bash
ollama pull qwen2.5:3b
```

### 2\. Clone and Install Dependencies

```bash
git clone https://github.com/your-username/ConsultAID.git
cd ConsultAID
pip install -r requirements.txt
```

*(Note: A `requirements.txt` file would need to be created from the project's dependencies, such as Flask, LangChain, Ollama, FAISS, etc.)*

### 3\. Add Your Knowledge Base

Place all your PDF documents inside the `/documents` folder. The application will automatically process these files to build its knowledge base.



## Usage

You can run this application in two ways: locally on your machine for development and testing, or exposed to the internet using `ngrok` for public access and integration testing.

### Option 1: Running on Localhost

This is the standard way to run the application for development.

1.  **Start the Server**:
    Run the `app.py` file from your terminal:

    ```bash
    python app.py
    ```

2.  **Access the API**:
    The server will start, and the API will be available at `http://127.0.0.1:5001`. You can now send requests to the API endpoints from your front-end application or tools like Postman.

### Option 2: Exposing with Ngrok

If you need to share your application with others or test webhook integrations, you can use `ngrok` to create a secure public URL for your local server.

1.  **Install Ngrok**:
    If you don't have it already, download and install `ngrok` from the [official website](https://ngrok.com/download).

2.  **Start Your Local Server**:
    First, make sure your Flask application is running locally as described in the previous section.

3.  **Expose Your Port with Ngrok**:
    Open a *new* terminal window and run the following command to tell `ngrok` to expose port `5001`:

    ```bash
    ngrok http 5001
    ```

4.  **Get Your Public URL**:
    `ngrok` will generate a public URL that forwards to your local server. It will look something like this:

    ```
    Forwarding                    https://random-string-of-characters.ngrok-free.app -> http://localhost:5001
    ```

    You can now use this `https` URL to access your chatbot from anywhere in the world.



## Front-end Integration (`chatbot.js`)

The `chatbot.js` file is now hosted on a CDN, making it even easier to integrate into any website. To connect it to the backend API, simply add the script tag to your HTML and specify your API's URL using the `data-api-url` attribute.

### Example Usage:

**1. For Local Development:**
Point the `data-api-url` to your local server.

```html
<script src="https://cdn.jsdelivr.net/gh/CodeCrew0/ConsultAID@main/templates/chatbot.js" 
        data-api-url="http://localhost:5001"></script>
```

**2. For Ngrok Testing:**
Use the public URL generated by `ngrok`.

```html
<script src="https://cdn.jsdelivr.net/gh/CodeCrew0/ConsultAID@main/templates/chatbot.js" 
        data-api-url="https://abc123xyz.ngrok-free.app"></script>
```

**3. For Production:**
Use your production API's domain name.

```html
<script src="https://cdn.jsdelivr.net/gh/CodeCrew0/ConsultAID@main/templates/chatbot.js" 
        data-api-url="https://your-production-api.com"></script>
```



## API Endpoints

The application exposes the following RESTful API endpoints:

#### `POST /api/init`

Initializes a new user session. This should be called before any other interaction.

  * **Request Body**:
    ```json
    {
      "session_id": "some-unique-session-id"
    }
    ```
  * **Success Response (200)**:
    ```json
    {
      "status": "initialized",
      "message": "Session is ready.",
      "welcome_message": "Hello! How can I help you? ..."
    }
    ```

#### `POST /api/ask`

Sends a query to the chatbot.

  * **Request Body**:
    ```json
    {
      "session_id": "some-unique-session-id",
      "query": "What is the fee structure for B.Tech?"
    }
    ```
  * **Success Response (200)**:
    ```json
    {
      "response": "According to the fee structure document, the tuition fee for the B.Tech program is..."
    }
    ```

#### `POST /api/reset`

Resets a user session, clearing all conversation history.

  * **Request Body**:
    ```json
    {
      "session_id": "some-unique-session-id"
    }
    ```
  * **Success Response (200)**:
    ```json
    {
      "message": "Session reset successful"
    }
    ```

#### `GET /api/health`

Checks the health of the server.

  * **Success Response (200)**:
    ```json
    {
        "status": "healthy",
        "active_sessions": 5,
        "timestamp": 1725167095.123
    }
    ```



## Customization

This platform is designed to be universal. To adapt it to your own use case:

1.  **Update the Knowledge Base**: Clear the `/documents` folder and add your own set of PDF files.
2.  **Change the Chatbot's Persona**: Modify the `SYSTEM_MODELFILE.txt` file to define the new persona, tone, and rules for your chatbot.
3.  **Use a Different LLM**: Change the model name in `model_loader.py` (line 140) to any other model supported by Ollama. Make sure you have pulled the new model locally.
