import azure.functions as func
import os
import json
from ..shared.azure_clients import get_blob_client, get_openai_client, get_search_client
from ..shared.document_analysis import segment_document
from ..shared.chunking import adaptive_chunking

# Environment variables for Azure resources
BLOB_CONN_STR = os.environ.get('BLOB_CONN_STR')  # Connection string for Azure Blob Storage
BLOB_CONTAINER = os.environ.get('BLOB_CONTAINER', 'readpilot-docs')  # Default container name
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')  # Azure OpenAI key
OPENAI_ENDPOINT = os.environ.get('OPENAI_ENDPOINT')  # Azure OpenAI endpoint
BLOB_ACCOUNT_URL = os.environ.get('BLOB_ACCOUNT_URL')  # e.g., https://<account>.blob.core.windows.net
AI_SEARCH_ENDPOINT = os.environ.get('AI_SEARCH_ENDPOINT')  # Azure AI Search endpoint
AI_SEARCH_KEY = os.environ.get('AI_SEARCH_KEY')  # Azure AI Search key
AI_SEARCH_INDEX = os.environ.get('AI_SEARCH_INDEX', 'readpilot-chunks')  # Default search index name

# Helper to construct blob URL from blob name
def construct_blob_url(blob_name):
    # Returns the full URL to a blob given its name
    return f"{BLOB_ACCOUNT_URL}/{BLOB_CONTAINER}/{blob_name}"

# Helper to download a blob as text
def download_blob_as_text(blob_client, container, blob_name):
    # Downloads the specified blob and decodes it as UTF-8 text
    blob = blob_client.get_container_client(container).get_blob_client(blob_name)
    return blob.download_blob().readall().decode('utf-8')

# Helper to download a blob as bytes
def download_blob_as_bytes(blob_client, container, blob_name):
    # Downloads the specified blob and returns its raw bytes
    blob = blob_client.get_container_client(container).get_blob_client(blob_name)
    return blob.download_blob().readall()

# LLM-based chapter/section scoring using GPT-4
def llm_score_sections(query, knowledge_map, gpt_client):
    """
    Uses GPT-4 to rate each chapter summary for relevance to the query.
    Returns a priority queue: list of (score, index) tuples, sorted descending.
    """
    summaries = [section['summary'] for section in knowledge_map]
    # Build a batch prompt for efficiency
    prompt = (
        "Given the following user question and a list of chapter summaries, "
        "rate each summary from 1 (not relevant) to 5 (highly relevant) for answering the question. "
        "Return a JSON list of numbers in the same order as the summaries.\n\n"
        f"User question: {query}\n\n"
        "Summaries:\n" +
        "\n".join(f"{i+1}. {s}" for i, s in enumerate(summaries))
    )
    scores_str = gpt_client.chat_completion(prompt=prompt, model="gpt-4")
    try:
        scores = json.loads(scores_str)
        if not isinstance(scores, list) or len(scores) != len(summaries):
            raise ValueError("Invalid LLM output for chapter scores.")
    except Exception:
        # Fallback: if LLM output is not valid JSON, treat all as low relevance
        scores = [1] * len(summaries)
    # Build a priority queue (list of tuples: (score, index)), sorted descending
    pq = sorted([(score, i) for i, score in enumerate(scores)], reverse=True)
    return pq

# Helper to extract real text for selected chapters from pre-extracted pages
def extract_chapter_texts(pages, sections):
    # For each selected section, extract the text from start_page to end_page (inclusive)
    chapter_texts = []
    for section in sections:
        # Extract text from start_page to end_page (inclusive)
        text = '\n'.join(pages[section['start_page']:section['end_page']])
        chapter_texts.append(text)
    return chapter_texts

# Main Azure Function entry point
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP POST endpoint for user chat queries.
    Steps:
    1. Parse JSON payload for query and document reference.
    2. Load knowledge map and pre-extracted pages from Blob Storage.
    3. Use LLM to score and prioritize chapters/sections.
    4. Extract real text for those chapters.
    5. Chunk, vectorize, and store/query in Azure AI Search.
    6. Retrieve top relevant chunks for context.
    7. Generate and return the answer using GPT, with references.
    """
    try:
        # 1. Parse JSON payload
        try:
            data = req.get_json()
        except ValueError:
            # If the request body is not valid JSON, return an error
            return func.HttpResponse("Invalid JSON payload.", status_code=400)
        query = data.get('query')
        blob_url = data.get('blob_url')
        blob_name = data.get('blob_name')
        if not query or (not blob_url and not blob_name):
            # Require both a query and a document reference
            return func.HttpResponse("Must provide 'query' and either 'blob_url' or 'blob_name' in payload.", status_code=400)
        if not blob_url:
            # If only blob_name is provided, construct the full URL
            blob_url = construct_blob_url(blob_name)
        if not blob_name:
            # If only blob_url is provided, extract the blob name from the URL
            blob_name = blob_url.split('/')[-1]

        # 2. Load knowledge map and pre-extracted pages from Blob Storage
        blob_client = get_blob_client(BLOB_CONN_STR)
        map_blob_name = blob_name + '.knowledge_map.json'
        pages_blob_name = blob_name + '.pages.json'
        knowledge_map_json = download_blob_as_text(blob_client, BLOB_CONTAINER, map_blob_name)
        knowledge_map = json.loads(knowledge_map_json)
        pages_json = download_blob_as_text(blob_client, BLOB_CONTAINER, pages_blob_name)
        pages = json.loads(pages_json)

        # 3. Use LLM to score and prioritize chapters/sections
        gpt_client = get_openai_client(OPENAI_API_KEY, OPENAI_ENDPOINT)
        pq = llm_score_sections(query, knowledge_map, gpt_client)
        # Only consider chapters with score >= 3 (configurable threshold)
        relevant_indices = [i for score, i in pq if score >= 3]
        if not relevant_indices:
            # If no chapter is relevant, let the LLM handle the response with system prompt and no context
            system_prompt = (
                "You are ReadPilot, an AI copilot that helps users understand, summarize, and answer questions about their book or document. "
                "If the user asks a general question or greeting, introduce yourself and explain your capabilities. "
                "If the question is about the document, answer using the provided context. If you don't know, say so politely."
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            answer = gpt_client.chat_completion(messages=messages, model="gpt-4")
            return func.HttpResponse(
                json.dumps({
                    'answer': answer,
                    'references': [],
                    'context_sections': []
                }),
                mimetype="application/json",
                status_code=200
            )
        # Build a priority queue of relevant sections
        selected_sections = [knowledge_map[i] for i in relevant_indices]

        # 4. Extract real text for those chapters
        chapter_texts = extract_chapter_texts(pages, selected_sections)

        # 5. Chunk, vectorize, and store/query in Azure AI Search
        search_client = get_search_client(AI_SEARCH_ENDPOINT, AI_SEARCH_KEY, AI_SEARCH_INDEX)
        all_chunks = []
        chunk_metadata = []
        for text, section in zip(chapter_texts, selected_sections):
            # Adaptive chunking (by headers, paragraphs, etc.)
            chunks = adaptive_chunking(text, structure=None)  # returns list of dicts
            for c in chunks:
                chunk = c['chunk']
                meta = {
                    'chunk': chunk,
                    'chapter': section['chapter_name'],
                    'start_page': section.get('start_page'),
                    'end_page': section.get('end_page'),
                    'start_offset': c.get('start_offset'),
                    'end_offset': c.get('end_offset')
                }
                embedding = gpt_client.create_embedding(chunk)
                doc = {
                    'id': f"{blob_name}_{section['start_page']}_{section['end_page']}_{c.get('start_offset',0)}",
                    'chunk': chunk,
                    'embedding': embedding,
                    'chapter': section['chapter_name'],
                    'doc_id': blob_name,
                    'start_page': meta['start_page'],
                    'end_page': meta['end_page']
                }
                search_client.upload_documents([doc])
                all_chunks.append(doc)
                chunk_metadata.append(meta)
        # Query Azure AI Search for top relevant chunks
        query_embedding = gpt_client.create_embedding(query)
        results = search_client.search("*", vector=query_embedding, top=3)
        context = '\n'.join([r['chunk'] for r in results])

        # 6. Generate answer using GPT with system prompt and context
        system_prompt = (
            "You are ReadPilot, an AI copilot that helps users understand, summarize, and answer questions about their book or document. "
            "If the user asks a general question or greeting, introduce yourself and explain your capabilities. "
            "If the question is about the document, answer using the provided context. If you don't know, say so politely."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
        answer = gpt_client.chat_completion(messages=messages, model="gpt-4")

        # 7. Build references for the frontend
        references = []
        for r in results:
            references.append({
                'chunk': r['chunk'],
                'chapter': r.get('chapter'),
                'start_page': r.get('start_page'),
                'end_page': r.get('end_page')
            })

        return func.HttpResponse(
            json.dumps({
                'answer': answer,
                'references': references,
                'context_sections': [s['chapter_name'] for s in selected_sections]
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        # Return error details for debugging
        return func.HttpResponse(f"Error: {str(e)}", status_code=500) 