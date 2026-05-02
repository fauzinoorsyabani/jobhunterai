"""
tools/research.py
Tool: company_research
Menggunakan Tavily untuk web search + Groq untuk summarization
"""

import time
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from tavily import TavilyClient
from config import GROQ_API_KEY, TAVILY_API_KEY, MODEL_FAST, TAVILY_MAX_RESULTS

# In-memory cache {company_lower: (timestamp, result)}
_cache: dict[str, tuple[float, str]] = {}
CACHE_TTL_SECONDS = 3600  # 1 jam


def _get_llm():
    return ChatGroq(model=MODEL_FAST, api_key=GROQ_API_KEY, temperature=0.3)


def _get_tavily():
    return TavilyClient(api_key=TAVILY_API_KEY)


def _search_company(company_name: str) -> list[dict]:
    """Run 3 Tavily queries, deduplicate by URL, return top snippets."""
    client = _get_tavily()
    queries = [
        f"{company_name} technology stack engineering team 2025",
        f"{company_name} company news product launch 2024 2025",
        f"{company_name} work culture employee review glassdoor",
    ]

    seen_urls = set()
    snippets = []

    for q in queries:
        try:
            resp = client.search(q, max_results=TAVILY_MAX_RESULTS, search_depth="basic")
            for r in resp.get("results", []):
                url = r.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    snippets.append({
                        "title": r.get("title", ""),
                        "content": r.get("content", "")[:400],
                        "url": url,
                    })
        except Exception:
            continue  # Skip failed queries, jangan crash

    return snippets[:12]  # cap 12 snippets ke LLM


def _summarize(company_name: str, snippets: list[dict]) -> str:
    """Summarize raw snippets into structured markdown."""
    if not snippets:
        return f"Limited information found for **{company_name}**. Proceed with general knowledge."

    raw = "\n".join([f"- {s['title']}: {s['content']}" for s in snippets])
    llm = _get_llm()

    prompt = f"""You are helping a job applicant research {company_name} before writing a cold email.

Summarize this raw data into a structured markdown report. Be specific and factual.

Raw data:
{raw}

Output format (use exactly this structure):
## {company_name}

**What they do:** [1-2 sentence description]

**Tech stack:** [bullet list of technologies mentioned]

**Recent highlights:** [2-3 bullet points of recent news/launches]

**Culture signals:** [1-2 bullet points from reviews/press]

**Hook for email:** [1 sentence — a specific, compelling reason to mention in a cold email]

Keep total output under 300 words. Only include facts from the data provided."""

    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Research summary unavailable for {company_name}. Error: {str(e)}"


@tool
def company_research(company_name: str) -> str:
    """
    Research a company's tech stack, culture, and recent news.
    Use this tool BEFORE writing any cold email.

    Args:
        company_name: Name of the company to research (e.g., "Tokopedia", "Gojek")

    Returns:
        Structured markdown summary: what they do, tech stack, news, culture, email hook
    """
    cache_key = company_name.lower().strip()

    # Check cache
    if cache_key in _cache:
        cached_time, cached_result = _cache[cache_key]
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            return f"[cached] {cached_result}"

    # Fetch + summarize
    snippets = _search_company(company_name)
    result = _summarize(company_name, snippets)

    # Store in cache
    _cache[cache_key] = (time.time(), result)

    return result
