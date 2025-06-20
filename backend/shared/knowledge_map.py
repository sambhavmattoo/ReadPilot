import random

# Generates a knowledge map (chapter summaries) for the document using GPT-4
def generate_knowledge_map(sections, pages, gpt_client):
    """
    For each section, sample up to 3 pages, concatenate their text, and ask GPT-4 to summarize.
    Returns a list of dicts: [{chapter_name, start_page, end_page, summary}]
    Args:
        sections: List of section dicts (with start_page, end_page, title)
        pages: List of page texts
        gpt_client: AzureOpenAI client for GPT-4
    Returns:
        List of knowledge map entries
    """
    knowledge_map = []
    for section in sections:
        # Randomly sample up to 3 pages from this section for summarization
        sample_pages = random.sample(range(section['start_page'], section['end_page']), min(3, section['end_page']-section['start_page']))
        sample_text = "\n".join([pages[i] for i in sample_pages])
        # Use GPT-4 to summarize the sampled text with a system prompt
        system_prompt = (
            "You are ReadPilot, an AI copilot that helps users understand, summarize, and answer questions about their book or document. "
            "If the user asks for a summary, provide a concise and clear summary of the provided text."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Summarize: {sample_text}"}
        ]
        summary = gpt_client.chat_completion(messages=messages, model="gpt-4")
        knowledge_map.append({
            'chapter_name': section['title'],
            'start_page': section['start_page'],
            'end_page': section['end_page'],
            'summary': summary
        })
    return knowledge_map 