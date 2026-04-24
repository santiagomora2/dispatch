from ddgs import DDGS
import httpx
import trafilatura
import re

from agent.tools import tool

def chunk_by_headings(text: str):
    sections = re.split(r'\n(?=#{1,3} )', text)
    return [{"heading": s.split("\n")[0], "content": s} for s in sections]

@tool({
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for relevant URLs for a given query. Hint: After fetching URLs, use fetch_url to get content from the most relevant ones.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The query to search for."}
            },
            "required": ["query"]
        }
    }
}, lazy = True)
def web_search(query: str, max_results: int = 3):
    """
    Perform a web search using DuckDuckGo and return the top results.
    Each result includes the title, URL, and a brief snippet of text.
    """
    try:
        results = DDGS().text(query, max_results=max_results)
    except Exception as e:
        return {"error": f"Could not perform web search: {e}"}
    return {"Fetched_Results": [{"title": r["title"], "url": r["href"]} for r in results]}

@tool({
    "type": "function",
    "function": {
        "name": "fetch_url",
        "description": "Fetch the content of a given URL. "
        "If focus is none, it returns a map of the content with its headers."
        "After deciding which headers to use, call fetch_url again to extract only the most relevant information",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to be fetched."},
                "focus": {"type": "list", "description": "The list of headers to be extracted."}
            },
            "required": ["url"]
        }
    }
}, lazy = True)
def fetch_url(url: str, focus: list[str] = None):
    """
    Extract website text for a given URL using Jina with Trafilatura as a fallback.
    
    """
    jina_url = f"https://r.jina.ai/{url}"
    try:
        text = httpx.get(jina_url, timeout=10).text
    except Exception as e1:
        try:
            downloaded = trafilatura.fetch_url(url)
            text = trafilatura.extract(downloaded)
        except Exception as e2:
            return {"error": f"Could not fetch the requested URL: {e1}, {e2}"}
    sections = chunk_by_headings(text)
    if not focus:
        # return headings map only, agent picks what it needs
        return {
            "sections": [{"heading": s["heading"], "preview": s["content"][:100]} for s in sections],
            "hint": "call fetch_url again with focus=[list of headings] to get full content; focused on what you need"
        }
    
    # return full content of requested sections only
    selected = [s for s in sections if any(f.lower() in s["heading"].lower() for f in focus)]
    content = "\n\n".join(s["content"] for s in selected)
    return {"content": content[:5000], "truncated": len(content) > 5000}