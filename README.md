# ReadPilot: AI Document Chat Extension
![ReadPilot_Banner](https://github.com/user-attachments/assets/456764c7-bcba-49a4-8b01-5b686a79e0f5)

ReadPilot is a Chrome extension that lets you chat with any PDF or document using advanced AI. It features intelligent document mapping, selective processing, and efficient retrieval, powered by Azure AI services. The system is designed for privacy, scalability, and cost-efficiency, making it ideal for both personal and enterprise use.

---

## Table of Contents
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Frontend (Chrome Extension)](#frontend-chrome-extension)
- [Backend (Azure Functions)](#backend-azure-functions)
- [Azure Resources Used](#azure-resources-used)
- [Setup & Installation](#setup--installation)
- [How It Works](#how-it-works)
- [Troubleshooting & Tips](#troubleshooting--tips)
- [Extending ReadPilot](#extending-readpilot)
- [Contact & Support](#contact--support)
- [Responsible AI](#responsible-ai)

---

## Features
- **Chat with any PDF or document** using natural language.
- **Smart document mapping:** Detects table of contents (TOC), builds a knowledge map, and understands document structure.
- **Selective processing:** Only processes and vectorizes relevant chapters/sections for each query, saving compute and cost.
- **Efficient retrieval:** Uses Azure AI Search for fast, semantic chunk retrieval.
- **Modern, privacy-first Chrome extension UI.**
- **Scalable, serverless backend** using Azure Functions and AI services.

---

## Architecture Overview

```
+-------------------+         +-------------------+         +-------------------+
|  Chrome Extension | <-----> |  Azure Functions  | <-----> |   Azure Services  |
+-------------------+         +-------------------+         +-------------------+
        |                          |                               |
        | 1. Upload PDF            |                               |
        |------------------------->|                               |
        |                          | 2. Extract, map, store        |
        |                          |------------------------------>|
        |                          |                               |
        | 3. User query            |                               |
        |------------------------->|                               |
        |                          | 4. Smart retrieval, answer    |
        |                          |------------------------------>|
        |                          |                               |
        |<-------------------------|<------------------------------|
        | 5. Display answer        |                               |
```

---

## Frontend (Chrome Extension)

- **Files:**
  - `manifest.json`: Chrome extension manifest (v3).
  - `sidepanel.html`, `sidepanel.js`, `sidepanel.css`: Side panel UI and logic.
  - `content.js`: Content script for interacting with web pages.
  - `background.js`: Background service worker.
  - `assets/`: Extension icons and images.
- **Key Features:**
  - Lets users select and upload PDFs to Azure Blob Storage.
  - Calls backend endpoints to build knowledge maps and answer queries.
  - Displays chat UI for user interaction.
- **How to Use:**
  1. Load the extension as "unpacked" in Chrome (see below).
  2. Open the side panel, select a PDF, and start chatting!

---

## Backend (Azure Functions)

- **Location:** `backend/`
- **Endpoints:**
  - `/upload` (or `/analyze`): Builds a knowledge map from a PDF in Blob Storage.
  - `/chat`: Answers user queries by selectively processing only the most relevant chapters/sections.
- **Key Features:**
  - Extracts text and structure from PDFs using Azure Document Intelligence.
  - Detects multi-page TOCs or creates synthetic sections.
  - Builds a knowledge map and stores it in Blob Storage.
  - For each query, only processes and vectorizes relevant chapters.
  - Uses Azure AI Search for fast, semantic retrieval.
  - Uses Azure OpenAI (GPT-4) for summarization and answering.
- **See [`backend/README.md`](backend/README.md) for full backend details.**

---

## Azure Resources Used

- **Azure Blob Storage:** Stores PDFs, per-page text, and knowledge maps.
- **Azure AI Document Intelligence:** Extracts text and structure from PDFs.
- **Azure OpenAI:** Summarizes content, generates answers, and creates embeddings.
- **Azure AI Search:** Stores and retrieves vectorized document chunks for efficient semantic search.

---

## Setup & Installation

### 1. **Frontend (Chrome Extension)**
- Open Chrome and go to `chrome://extensions/`.
- Enable "Developer mode".
- Click "Load unpacked" and select the project root folder (where `manifest.json` is).
- The extension is now ready to use!

### 2. **Backend (Azure Functions)**
- See [`backend/README.md`](backend/README.md) for detailed setup, environment variables, and deployment instructions.
- You will need to:
  - Set up Azure Blob Storage, Document Intelligence, OpenAI, and AI Search resources.
  - Deploy the backend functions to Azure.
  - Set environment variables for all keys, endpoints, and container names.

---

## How It Works

### **PDF Upload & Knowledge Map Creation**
1. User selects a PDF in the extension.
2. The extension uploads the PDF to Azure Blob Storage.
3. The extension calls the `/upload` backend endpoint with the blob URL or name.
4. The backend extracts text, scans for a TOC, builds a knowledge map, and stores it in Blob Storage.

### **Chatting with the Document**
1. User enters a question in the extension.
2. The extension sends the query and document reference to the `/chat` backend endpoint.
3. The backend loads the knowledge map and per-page text, selects the most relevant chapters, chunks and vectorizes them, and retrieves the best context using Azure AI Search.
4. The backend uses GPT-4 to answer, using only the most relevant content.
5. The extension displays the answer and supporting context.

---

## Troubleshooting & Tips

- **Document Intelligence only processes 2 pages on the free tier.** Upgrade to S0 for full document analysis.
- **Blob Storage permissions:** Ensure the backend has access to the container and blobs.
- **Environment variables:** Double-check all keys, endpoints, and container names.
- **Logs:** Check Azure Function logs for errors and stack traces.
- **Testing:** Use Postman or curl to test backend endpoints independently of the frontend.
- **Chunking:** Tune the chunking strategy in `backend/shared/chunking.py` for your document types.
- **Vector search:** Ensure your AI Search index is set up for vector search and can store embeddings.

---

## Extending ReadPilot

- **Advanced semantic scoring:** Improve chapter/section prioritization for queries.
- **Custom chunking:** Enhance chunking to use document structure (headers, tables, etc.).
- **UI enhancements:** Display knowledge map and context sections in the frontend.
- **Security:** Add authentication and authorization as needed.
- **Logging & monitoring:** Integrate with Azure Monitor for production use.
- **Support for more file types:** Extend backend to handle DOCX, PPTX, etc.

---

## Contact & Support

For questions, issues, or feature requests, please open an issue or contact the project maintainer.

## Responsible AI

- **Accessibility:** The chat UI is fully accessible, with ARIA labels, high-contrast colors, keyboard navigation, and screen reader support.
- **Auditability:** The backend logic is transparent and can be extended to log which chapters were selected, what scores were given, and what answer was returned for review and improvement.
- **No hallucinations:** If a user question is not relevant to the document, the system will say so instead of making up an answer. 
