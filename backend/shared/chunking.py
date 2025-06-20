import re

# Splits text into smart, context-aware chunks for vectorization and retrieval
def adaptive_chunking(text, structure=None, max_chunk_size=1000, overlap=200, page_offset=0, page_map=None):
    """
    Splits text into smart, context-aware chunks for vectorization and retrieval.
    Returns a list of dicts: [{chunk, start_page, end_page}]
    - Prefers splitting at detected headers (e.g., 'Chapter', 'Section', all-caps lines).
    - Falls back to paragraph or fixed-size chunking if no headers found.
    - If page_map is provided, maps character offsets to page numbers.
    Args:
        text: The full text to chunk (string)
        structure: (optional) Structure info from Document Intelligence (not used yet)
        max_chunk_size: Maximum number of characters per chunk
        overlap: Number of characters to overlap between chunks
        page_offset: Offset to add to page numbers (if needed)
        page_map: Optional list mapping character offsets to page numbers
    Returns:
        List of dicts: [{chunk, start_page, end_page}]
    """
    # Regex to detect headers: lines starting with 'Chapter', 'Section', 'Part', or all-caps lines
    header_pattern = re.compile(r'^(chapter|section|part)\b|^[A-Z][A-Z\s\d\-:]{8,}$', re.IGNORECASE | re.MULTILINE)
    header_indices = [m.start() for m in header_pattern.finditer(text)]
    chunks = []
    chunk_spans = []
    if header_indices and len(header_indices) > 1:
        # If headers are found, split at each header
        for i in range(len(header_indices)):
            start = header_indices[i]
            end = header_indices[i+1] if i+1 < len(header_indices) else len(text)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
                chunk_spans.append((start, end))
    else:
        # If no headers, split by paragraphs or fixed-size windows
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        current = ''
        start = 0
        for para in paragraphs:
            if len(current) + len(para) + 2 <= max_chunk_size:
                if not current:
                    start = text.find(para)
                current += (para + '\n\n')
            else:
                if current:
                    end = start + len(current)
                    chunks.append(current.strip())
                    chunk_spans.append((start, end))
                start = text.find(para, start)
                current = para + '\n\n'
        if current:
            end = start + len(current)
            chunks.append(current.strip())
            chunk_spans.append((start, end))
    final_chunks = []
    for chunk, (start, end) in zip(chunks, chunk_spans):
        if len(chunk) <= max_chunk_size:
            # If the chunk is within the size limit, add as is
            final_chunks.append({'chunk': chunk, 'start_offset': start, 'end_offset': end})
        else:
            # If the chunk is too large, split into overlapping windows
            for i in range(0, len(chunk), max_chunk_size - overlap):
                c_start = start + i
                c_end = min(start + i + max_chunk_size, end)
                final_chunks.append({'chunk': chunk[i:i+max_chunk_size], 'start_offset': c_start, 'end_offset': c_end})
    # Map offsets to page numbers if page_map is provided
    for fc in final_chunks:
        if page_map:
            fc['start_page'] = page_map.get(fc['start_offset'], None)
            fc['end_page'] = page_map.get(fc['end_offset'], None)
        else:
            fc['start_page'] = None
            fc['end_page'] = None
    return final_chunks 