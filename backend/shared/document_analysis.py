import re

# Detects a table of contents (TOC) or index in the first N pages of a document
def detect_index(pages, max_toc_pages=50):
    """
    Scans the first max_toc_pages for a table of contents (TOC) or index.
    Handles multi-page indices by aggregating all detected entries.
    Args:
        pages: List of page texts (strings)
        max_toc_pages: Number of pages to scan for TOC/index
    Returns:
        List of index entries: [{title, page_ref, line, toc_page}]
    """
    # Pattern matches lines like 'Chapter 1 .... 5', 'Section 2.3 .... 12', etc.
    toc_pattern = re.compile(r'(chapter|section|part)\s+([\w\d\.\-]+).*?(\d+)', re.IGNORECASE)
    index = []
    for i, page in enumerate(pages[:max_toc_pages]):
        for line in page.split('\n'):
            match = toc_pattern.search(line)
            if match:
                # If a TOC entry is found, add it to the index list
                index.append({
                    'title': match.group(2),  # The chapter/section/part name
                    'page_ref': int(match.group(3)),  # The referenced page number
                    'line': line,  # The full line text
                    'toc_page': i+1  # The page number in the PDF where this TOC entry was found
                })
    return index

# Calculates the offset between the first index reference and the actual content start
def calculate_page_offset(index, actual_first_chapter_page):
    """
    Calculates the offset between the first index reference and the actual content start.
    Args:
        index: List of index entries
        actual_first_chapter_page: Detected first content page (int)
    Returns:
        Integer offset
    """
    if not index:
        # If no index is found, assume no offset
        return 0
    # Offset = where content actually starts - what the TOC says
    return actual_first_chapter_page - index[0]['page_ref']

# Segments the document into sections/chapters using the index if found, otherwise creates synthetic sections
def segment_document(pages, index):
    """
    Segments the document into sections/chapters using the index if found, otherwise creates synthetic sections.
    Args:
        pages: List of page texts
        index: List of index entries
    Returns:
        List of sections: [{title, start_page, end_page}]
    """
    if index:
        sections = []
        for i, entry in enumerate(index):
            start = entry['page_ref']
            # The end of this section is the start of the next, or the end of the document
            end = index[i+1]['page_ref'] if i+1 < len(index) else len(pages)
            sections.append({'title': entry['title'], 'start_page': start, 'end_page': end})
        return sections
    else:
        # Fallback: split by every N pages if no TOC/index is found
        N = max(5, len(pages)//10)  # At least 5 pages per section, or 10 sections
        return [{'title': f'Section {i+1}', 'start_page': i*N, 'end_page': min((i+1)*N, len(pages))} for i in range((len(pages)+N-1)//N)] 