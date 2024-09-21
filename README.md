# Real Estate System Technical Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Components](#components)
   - [Database](#database)
   - [QdrantClient](#qdrantclient)
   - [SentenceTransformer](#sentencetransformer)
   - [TelegramBot](#telegrambot)
   - [UserManagement](#usermanagement)
   - [PropertyManagement](#propertymanagement)
   - [ClientManagement](#clientmanagement)
   - [DocumentManagement](#documentmanagement)
   - [GeminiAI](#geminiai)
3. [System Architecture](#system-architecture)
4. [Setup and Installation](#setup-and-installation)
5. [Usage](#usage)
6. [UML Diagram](#uml-diagram)

## System Overview

This real estate system is a Telegram bot-based application that helps real estate agents manage properties, clients, and documents. It uses vector search capabilities (Qdrant) for property matching and AI-powered text generation (Google's Gemini API) for improving queries and generating property descriptions.

## Components

### Database
- Handles creation and setup of SQLite databases for storing user, agent, property, client, and document information.
- Key functions: `create_database()`, `setup_user_db()`, `setup_databases()`

### QdrantClient
- Manages the vector database for efficient property searching.
- Key functions: `setup_qdrant()`, `retrieve_relevant_properties()`

### SentenceTransformer
- Converts text descriptions into vector representations for use with Qdrant.
- Key function: `encode()`

### TelegramBot
- Main interface for user interactions via Telegram.
- Handles commands, messages, and button callbacks.
- Key functions: `start()`, `handle_message()`, `handle_referral()`, `button_callback()`

### UserManagement
- Manages user credits and referral system.
- Key functions: `get_user_credits()`, `update_user_credits()`, `add_referral()`

### PropertyManagement
- Handles adding and retrieving property information.
- Key functions: `add_property()`, `get_property()`

### ClientManagement
- Manages client information.
- Key functions: `add_client()`, `get_client()`

### DocumentManagement
- Handles creation, retrieval, and management of documents related to property transactions.
- Key functions: `create_document()`, `get_document()`, `update_document_status()`, `generate_document()`

### GeminiAI
- Utilizes Google's Gemini API for natural language processing tasks.
- Key functions: `improve_query()`, `generate_property_description()`, `is_real_estate_query()`

## System Architecture

The system follows a modular architecture with the TelegramBot at its core, integrating various components for specific functionalities. The bot interacts with users, manages data through the Database component, uses QdrantClient for vector search, and leverages GeminiAI for text processing and generation.

## Setup and Installation

1. Clone the repository
2. Install required dependencies:
   ```
   pip install python-telegram-bot python-dotenv sentence-transformers qdrant-client google-generativeai sqlite3 python-docx docx2pdf PyPDF2
   ```
3. Set up environment variables in a `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   GOOGLE_API_KEY=your_google_api_key
   ```
4. Run the main script:
   ```
   python main.py
   ```

## Usage

1. Start the bot by sending `/start` command in Telegram.
2. Use the provided buttons to add properties, clients, or prepare documents.
3. Follow the prompts to input required information.
4. Use natural language queries to search for properties or get assistance.

## UML Diagram

The UML class diagram for this system is created using Mermaid. To save and view the diagram:

1. Save the Mermaid code in a file with `.mmd` extension (e.g., `real_estate_uml.mmd`).
2. Use a Mermaid-compatible viewer or online editor (like [Mermaid Live Editor](https://mermaid.live/)) to render the diagram.
3. For embedding in documentation, you can use Mermaid-supported Markdown renderers or convert the diagram to an image file.

Example Mermaid code file content:

```mermaid
# Real Estate System Technical Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Components](#components)
   - [Database](#database)
   - [QdrantClient](#qdrantclient)
   - [SentenceTransformer](#sentencetransformer)
   - [TelegramBot](#telegrambot)
   - [UserManagement](#usermanagement)
   - [PropertyManagement](#propertymanagement)
   - [ClientManagement](#clientmanagement)
   - [DocumentManagement](#documentmanagement)
   - [GeminiAI](#geminiai)
3. [System Architecture](#system-architecture)
4. [Setup and Installation](#setup-and-installation)
5. [Usage](#usage)
6. [UML Diagram](#uml-diagram)

## System Overview

This real estate system is a Telegram bot-based application that helps real estate agents manage properties, clients, and documents. It uses vector search capabilities (Qdrant) for property matching and AI-powered text generation (Google's Gemini API) for improving queries and generating property descriptions.

## Components

### Database
- Handles creation and setup of SQLite databases for storing user, agent, property, client, and document information.
- Key functions: `create_database()`, `setup_user_db()`, `setup_databases()`

### QdrantClient
- Manages the vector database for efficient property searching.
- Key functions: `setup_qdrant()`, `retrieve_relevant_properties()`

### SentenceTransformer
- Converts text descriptions into vector representations for use with Qdrant.
- Key function: `encode()`

### TelegramBot
- Main interface for user interactions via Telegram.
- Handles commands, messages, and button callbacks.
- Key functions: `start()`, `handle_message()`, `handle_referral()`, `button_callback()`

### UserManagement
- Manages user credits and referral system.
- Key functions: `get_user_credits()`, `update_user_credits()`, `add_referral()`

### PropertyManagement
- Handles adding and retrieving property information.
- Key functions: `add_property()`, `get_property()`

### ClientManagement
- Manages client information.
- Key functions: `add_client()`, `get_client()`

### DocumentManagement
- Handles creation, retrieval, and management of documents related to property transactions.
- Key functions: `create_document()`, `get_document()`, `update_document_status()`, `generate_document()`

### GeminiAI
- Utilizes Google's Gemini API for natural language processing tasks.
- Key functions: `improve_query()`, `generate_property_description()`, `is_real_estate_query()`

## System Architecture

The system follows a modular architecture with the TelegramBot at its core, integrating various components for specific functionalities. The bot interacts with users, manages data through the Database component, uses QdrantClient for vector search, and leverages GeminiAI for text processing and generation.

## Setup and Installation

1. Clone the repository
2. Install required dependencies:
   ```
   pip install python-telegram-bot python-dotenv sentence-transformers qdrant-client google-generativeai sqlite3 python-docx docx2pdf PyPDF2
   ```
3. Set up environment variables in a `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   GOOGLE_API_KEY=your_google_api_key
   ```
4. Run the main script:
   ```
   python main.py
   ```

## Usage

1. Start the bot by sending `/start` command in Telegram.
2. Use the provided buttons to add properties, clients, or prepare documents.
3. Follow the prompts to input required information.
4. Use natural language queries to search for properties or get assistance.

## UML Diagram

The UML class diagram for this system is created using Mermaid. To save and view the diagram:

1. Save the Mermaid code in a file with `.mmd` extension (e.g., `real_estate_uml.mmd`).
2. Use a Mermaid-compatible viewer or online editor (like [Mermaid Live Editor](https://mermaid.live/)) to render the diagram.
3. For embedding in documentation, you can use Mermaid-supported Markdown renderers or convert the diagram to an image file.

Example Mermaid code file content:

```mermaid
classDiagram
    class Database {
        +create_database()
        +setup_user_db()
        +setup_databases()
    }
    % ... (rest of the diagram code)
```

Remember to replace the placeholder content with the actual Mermaid code provided in the UML diagram artifact.
```

Remember to replace the placeholder content with the actual Mermaid code provided in the UML diagram artifact.