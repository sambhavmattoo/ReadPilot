# Import Azure SDK clients for Form Recognizer (Document Intelligence), Blob Storage, OpenAI, and Search
from azure.ai.formrecognizer import DocumentAnalysisClient  # For extracting text/structure from PDFs
from azure.core.credentials import AzureKeyCredential  # For authenticating Azure SDK clients
from azure.storage.blob import BlobServiceClient  # For accessing Azure Blob Storage
from openai import AzureOpenAI  # For calling Azure OpenAI (GPT-4, embeddings)
from azure.search.documents import SearchClient  # For Azure AI Search (vector search)

# Factory for Document Intelligence (Form Recognizer) client
def get_document_intelligence_client(endpoint, key):
    # Returns a DocumentAnalysisClient for the given endpoint and key
    return DocumentAnalysisClient(endpoint, AzureKeyCredential(key))

# Factory for Blob Storage client
def get_blob_client(conn_str):
    # Returns a BlobServiceClient for the given connection string
    return BlobServiceClient.from_connection_string(conn_str)

# Factory for Azure OpenAI client
def get_openai_client(api_key, endpoint):
    # Returns an AzureOpenAI client for the given API key and endpoint
    return AzureOpenAI(api_key=api_key, api_base=endpoint)

# Factory for Azure AI Search client
def get_search_client(endpoint, key, index_name):
    # Returns a SearchClient for the given endpoint, key, and index name
    return SearchClient(endpoint, AzureKeyCredential(key), index_name=index_name) 