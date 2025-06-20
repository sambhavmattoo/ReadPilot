import azure.functions as func
import os
import json
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
from ..shared.azure_clients import get_document_intelligence_client, get_blob_client, get_openai_client
from ..shared.document_analysis import detect_index, calculate_page_offset, segment_document
from ..shared.knowledge_map import generate_knowledge_map

# Environment variables for Azure resources (to be set in Azure or local.settings.json)
BLOB_CONN_STR = os.environ.get('BLOB_CONN_STR')  # Connection string for Azure Blob Storage
BLOB_CONTAINER = os.environ.get('BLOB_CONTAINER', 'readpilot-docs')  # Default container name
FORMRECOGNIZER_ENDPOINT = os.environ.get('FORMRECOGNIZER_ENDPOINT')  # Document Intelligence endpoint
FORMRECOGNIZER_KEY = os.environ.get('FORMRECOGNIZER_KEY')  # Document Intelligence key
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')  # Azure OpenAI key
OPENAI_ENDPOINT = os.environ.get('OPENAI_ENDPOINT')  # Azure OpenAI endpoint
BLOB_ACCOUNT_URL = os.environ.get('BLOB_ACCOUNT_URL')  # e.g., https://<account>.blob.core.windows.net

# Helper function to construct blob URL from blob name
def construct_blob_url(blob_name):
    """
    Constructs the full blob URL from the blob name and environment variables.
    Args:
        blob_name: Name of the blob (PDF file)
    Returns:
        Full URL to the blob
    """
    return f"{BLOB_ACCOUNT_URL}/{BLOB_CONTAINER}/{blob_name}"

# Helper function to extract text and structure from PDF using Azure Document Intelligence
def extract_document_text(form_client, pdf_url):
    """
    Uses Azure Document Intelligence to extract text and structure from the PDF.
    Args:
        form_client: DocumentAnalysisClient instance
        pdf_url: URL of the PDF in Blob Storage
    Returns:
        List of page texts (one string per page)
    """
    # Start the analysis job using the prebuilt-layout model
    poller = form_client.begin_analyze_document_from_url("prebuilt-layout", pdf_url)
    result = poller.result()
    pages = []
    for page in result.pages:
        # Concatenate all lines on the page into a single string
        page_text = "\n".join([line.content for line in page.lines])
        pages.append(page_text)
    return pages

# Main Azure Function entry point
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP POST endpoint for knowledge map creation from a PDF in Blob Storage.
    Expects JSON payload with either 'blob_url' or 'blob_name'.
    Steps:
    1. Parse JSON payload and determine PDF location.
    2. Use Document Intelligence to extract text/structure.
    3. Detect index (TOC), calculate page offset, segment document.
    4. Generate knowledge map using GPT-4.
    5. Store knowledge map and per-page text in Blob Storage.
    6. Return knowledge map metadata as JSON.
    """
    try:
        # 1. Parse JSON payload
        try:
            data = req.get_json()
        except ValueError:
            # If the request body is not valid JSON, return an error
            return func.HttpResponse("Invalid JSON payload.", status_code=400)

        # Determine PDF location: blob_url or blob_name
        blob_url = data.get('blob_url')
        blob_name = data.get('blob_name')
        if not blob_url and not blob_name:
            # Require at least one way to identify the PDF
            return func.HttpResponse("Must provide either 'blob_url' or 'blob_name' in payload.", status_code=400)
        if not blob_url:
            # If only blob_name is provided, construct the full URL
            blob_url = construct_blob_url(blob_name)
        if not blob_name:
            # If only blob_url is provided, extract the blob name from the URL
            blob_name = blob_url.split('/')[-1]

        # 2. Extract text/structure using Document Intelligence
        form_client = get_document_intelligence_client(FORMRECOGNIZER_ENDPOINT, FORMRECOGNIZER_KEY)
        pages = extract_document_text(form_client, blob_url)

        # 3. Detect index (TOC), calculate page offset, segment document
        # Scan up to 50 pages for multi-page TOC
        index = detect_index(pages, max_toc_pages=50)
        # Assume first chapter starts at the first non-empty page after TOC
        actual_first_chapter_page = next((i for i, p in enumerate(pages) if p.strip()), 0)
        page_offset = calculate_page_offset(index, actual_first_chapter_page)
        sections = segment_document(pages, index)

        # 4. Generate knowledge map using GPT-4
        gpt_client = get_openai_client(OPENAI_API_KEY, OPENAI_ENDPOINT)
        knowledge_map = generate_knowledge_map(sections, pages, gpt_client)

        # 5. Store knowledge map and per-page text in Blob Storage (as JSON)
        blob_client = get_blob_client(BLOB_CONN_STR)
        map_blob_name = blob_name + '.knowledge_map.json'  # Name for the knowledge map blob
        map_blob = blob_client.get_container_client(BLOB_CONTAINER).get_blob_client(map_blob_name)
        map_blob.upload_blob(json.dumps(knowledge_map), overwrite=True)
        # Store per-page text for later chapter extraction
        pages_blob_name = blob_name + '.pages.json'
        pages_blob = blob_client.get_container_client(BLOB_CONTAINER).get_blob_client(pages_blob_name)
        pages_blob.upload_blob(json.dumps(pages), overwrite=True)

        # 6. Return knowledge map metadata
        return func.HttpResponse(
            json.dumps({
                'file_name': blob_name,
                'pdf_url': blob_url,
                'knowledge_map_blob': map_blob_name,
                'pages_blob': pages_blob_name,
                'knowledge_map': knowledge_map
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        # Return error details for debugging
        return func.HttpResponse(f"Error: {str(e)}", status_code=500) 