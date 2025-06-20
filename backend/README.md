# ReadPilot Backend

## Quickstart (for Experienced Users)
1. **Clone the repo:**
   ```bash
   git clone <your-repo-url>
   cd ReadPilot/backend
   ```
2. **Install Azure Functions Core Tools v4 (Linux):**
   ```bash
   # Import the Microsoft repository key
   curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
   sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
   # Add the Azure Functions Core Tools v4 apt repository
   echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ focal main" | sudo tee /etc/apt/sources.list.d/azure-cli.list
   sudo apt-get update
   sudo apt-get install azure-functions-core-tools-4
   ```
3. **Install Python dependencies:**
   ```bash
   cd upload_function && pip install -r requirements.txt
   cd ../chat_function && pip install -r requirements.txt
   ```
4. **Create all required Azure resources (see below).**
5. **Set environment variables in `local.settings.json` or Azure portal.**
6. **Run locally:**
   ```bash
   func start
   ```
7. **Deploy to Azure Function App when ready.**

---

## Prerequisites
- **Azure Account:** [Sign up free](https://azure.microsoft.com/en-us/free/)
- **Python 3.10+** (recommended for Azure Functions)
- **Azure Functions Core Tools v4:** [Install guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)
- **Git**
- **A modern browser** (for the Chrome extension)

---

## Azure Resources to Create (Step-by-Step)

1. **Azure Blob Storage**
   - Go to [Azure Portal](https://portal.azure.com/)
   - Search for "Storage accounts" > "Create"
   - Choose a name, region, and resource group
   - After creation, go to the storage account > "Containers" > "+ Container"
   - Name it (e.g., `readpilotpdfs`), set access level to private
   - Copy the **connection string** and **account URL**

2. **Azure AI Document Intelligence (Form Recognizer)**
   - Go to [Create Form Recognizer](https://portal.azure.com/#create/Microsoft.CognitiveServicesFormRecognizer)
   - Choose a name, region, and pricing tier (S0 for >2 pages)
   - After creation, go to the resource > "Keys and Endpoint"
   - Copy the **endpoint** and **key**

3. **Azure OpenAI**
   - Apply for access if needed: [Azure OpenAI](https://aka.ms/oai/access)
   - Go to [Create Azure OpenAI](https://portal.azure.com/#create/Microsoft.CognitiveServicesOpenAI)
   - After creation, go to the resource > "Keys and Endpoint"
   - Deploy a GPT-4 model and an embedding model (e.g., `text-embedding-ada-002`)
   - Copy the **endpoint** and **key**

4. **Azure AI Search**
   - Go to [Create Azure Cognitive Search](https://portal.azure.com/#create/Microsoft.Search)
   - Choose a name, region, and pricing tier (Basic or higher for vector search)
   - After creation, go to the resource > "Keys"
   - Copy the **endpoint** and **key**
   - Create an **index** (e.g., `readpilot-chunks`) with vector search enabled

5. **Azure Function App**
   - Go to [Create Function App](https://portal.azure.com/#create/Microsoft.FunctionApp)
   - Choose Python 3.10+, region, and resource group
   - After creation, go to "Configuration" and add all environment variables (see below)

---

## Environment Variables
Set these in your Azure Function App settings or `local.settings.json`:

- `BLOB_CONN_STR`: Connection string for Azure Blob Storage.
- `BLOB_CONTAINER`: Name of the blob container (default: `readpilot-docs`).
- `BLOB_ACCOUNT_URL`: Base URL for your blob storage account (e.g., `https://<account>.blob.core.windows.net`).
- `FORMRECOGNIZER_ENDPOINT`: Endpoint for Document Intelligence.
- `FORMRECOGNIZER_KEY`: API key for Document Intelligence.
- `OPENAI_API_KEY`: API key for Azure OpenAI.
- `OPENAI_ENDPOINT`: Endpoint for Azure OpenAI.
- `AI_SEARCH_ENDPOINT`: Endpoint for Azure AI Search.
- `AI_SEARCH_KEY`: API key for Azure AI Search.
- `AI_SEARCH_INDEX`: Name of the Azure AI Search index (default: `readpilot-chunks`).

---

## Setup & Deployment (Step-by-Step)

### 1. **Clone the Repository**
```bash
git clone <your-repo-url>
cd ReadPilot/backend
```

### 2. **Install Azure Functions Core Tools v4 (Linux)**
```bash
# Import the Microsoft repository key
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
# Add the Azure Functions Core Tools v4 apt repository
echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ focal main" | sudo tee /etc/apt/sources.list.d/azure-cli.list
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
```

### 3. **Install Python Dependencies**
```bash
cd upload_function && pip install -r requirements.txt
cd ../chat_function && pip install -r requirements.txt
```

### 4. **Configure Azure Resources**
- Follow the step-by-step above to create all required Azure resources.
- Note all keys, endpoints, and container names.

### 5. **Set Environment Variables**
- Edit `local.settings.json` for local dev:
  ```json
  {
    "IsEncrypted": false,
    "Values": {
      "AzureWebJobsStorage": "UseDevelopmentStorage=true",
      "FUNCTIONS_WORKER_RUNTIME": "python",
      "BLOB_CONN_STR": "<your-blob-connection-string>",
      "BLOB_CONTAINER": "readpilot-docs",
      "BLOB_ACCOUNT_URL": "https://<account>.blob.core.windows.net",
      "FORMRECOGNIZER_ENDPOINT": "<your-formrecognizer-endpoint>",
      "FORMRECOGNIZER_KEY": "<your-formrecognizer-key>",
      "OPENAI_API_KEY": "<your-openai-key>",
      "OPENAI_ENDPOINT": "<your-openai-endpoint>",
      "AI_SEARCH_ENDPOINT": "<your-search-endpoint>",
      "AI_SEARCH_KEY": "<your-search-key>",
      "AI_SEARCH_INDEX": "readpilot-chunks"
    }
  }
  ```
- In Azure, set these as Application Settings for your Function App.

### 6. **Run Locally (for development/testing)**
```bash
func start
```
- Endpoints will be at `http://localhost:7071/api/upload` and `http://localhost:7071/api/chat`.
- Test with Postman or curl:
  ```bash
  curl -X POST http://localhost:7071/api/upload -H "Content-Type: application/json" -d '{"blob_url": "https://.../file.pdf"}'
  curl -X POST http://localhost:7071/api/chat -H "Content-Type: application/json" -d '{"query": "What is chapter 2 about?", "blob_url": "https://.../file.pdf"}'
  ```

### 7. **Deploy to Azure**
- [Deploy using VS Code, Azure CLI, or GitHub Actions](https://learn.microsoft.com/en-us/azure/azure-functions/functions-deployment-technologies)
- Typical steps:
  1. Create a Function App (Python 3.10+) in Azure.
  2. Deploy the `backend/` folder (or each function subfolder) to your Function App.
  3. Set all environment variables in the Azure portal.
  4. Test endpoints using the Azure Function URL (e.g., `https://<your-func-app>.azurewebsites.net/api/upload`).

### 8. **Integrate with the Chrome Extension**
- The extension should call the deployed backend endpoints for `/upload` and `/chat`.
- Update the endpoint URLs in your frontend code (e.g., `sidepanel.js`).

---

## How It Works

### Upload/Analyze Flow
1. **Frontend uploads PDF to Blob Storage.**
2. **Backend `/upload` endpoint:**
   - Extracts text and structure from the PDF.
   - Scans for a multi-page index/TOC (first 50 pages).
   - Builds a knowledge map (with summaries via OpenAI).
   - Stores `.knowledge_map.json` and `.pages.json` in Blob Storage.
   - Returns metadata and the knowledge map.

### Chat Flow
1. **Frontend sends user query and document reference to `/chat`.**
2. **Backend `/chat` endpoint:**
   - Loads the knowledge map and per-page text.
   - Scores and selects the most relevant chapters/sections.
   - Extracts real text for those chapters.
   - Chunks, vectorizes, and stores/queries these in Azure AI Search.
   - Retrieves the most relevant chunks for the query.
   - Uses GPT-4 to answer, using only the most relevant content.
   - Returns the answer, context sections, and chunks used.

---

## Frontend Integration

- The Chrome extension uploads PDFs directly to Blob Storage.
- After upload, it calls the `/upload` endpoint to build the knowledge map.
- For user queries, it calls the `/chat` endpoint with the query and document reference.
- The backend handles all smart processing, chunking, and retrieval.

---

## Troubleshooting & Tips

- **Document Intelligence only processes 2 pages on the free tier.** Upgrade to S0 for full document analysis.
- **Blob Storage permissions:** Ensure the backend has access to the container and blobs.
- **Environment variables:** Double-check all keys, endpoints, and container names.
- **Logs:** Check Azure Function logs for errors and stack traces.
- **Testing:** Use Postman or curl to test endpoints independently of the frontend.
- **Chunking:** Tune the chunking strategy in `shared/chunking.py` for your document types.
- **Vector search:** Ensure your AI Search index is set up for vector search and can store embeddings.
- **Python version:** Use Python 3.10+ for Azure Functions compatibility.

---

## Extending the Backend

- **Advanced semantic scoring:** Improve `score_relevant_sections` for better chapter/section prioritization.
- **Custom chunking:** Enhance `adaptive_chunking` to use document structure (headers, tables, etc.).
- **UI enhancements:** Display knowledge map and context sections in the frontend.
- **Security:** Add authentication and authorization as needed.
- **Logging & monitoring:** Integrate with Azure Monitor for production use.

---

## Contact & Support

For questions, issues, or feature requests, please open an issue or contact the project maintainer.

## PDF Viewing and Reference Links

- For clickable reference links (e.g., to jump to a specific page), you must open your PDF in the [PDF.js web viewer](https://mozilla.github.io/pdf.js/web/viewer.html).
- Direct links to PDFs (e.g., opening in Chrome's built-in viewer) do **not** support this feature due to browser security restrictions.
- **Recommended workflow:** Download your PDF, open the PDF.js viewer, and use the "Open File" dialog to load your PDF. Reference links from ReadPilot will now work as intended.

## What if References Are Missing?

- If the backend response omits the `references` field or it is empty, the frontend will display the answer but without any clickable links to jump to specific pages or sections in the PDF.
- This is not an error, but reduces the utility of the extension for navigation.

## Polite Themed Introduction for General Queries

- If you greet ReadPilot or ask a general question (e.g., "Hi there!", "Who are you?"), ReadPilot will respond with a friendly, themed introduction:

  > Hello! I am ReadPilot, your AI copilot. I can help you understand, summarize, and answer questions about your book or document. Just ask me anything about the content, chapters, or specific topics!

- This ensures a welcoming experience even if your query is not document-specific. 