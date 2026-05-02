"""
tools/market.py
Tool: market_analyzer
Analyze job market demand + skill gap for a given role
"""

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from tavily import TavilyClient
from config import GROQ_API_KEY, TAVILY_API_KEY, MODEL_FAST


def _get_llm():
    return ChatGroq(model=MODEL_FAST, api_key=GROQ_API_KEY, temperature=0.2)


@tool
def market_analyzer(
    target_role: str,
    user_skills: str,
    location: str = "Indonesia"
) -> str:
    """
    Analyze job market demand for a role and identify your skill gaps.
    Returns top demanded skills, what you're missing, learning priorities, salary range.

    Args:
        target_role: Role to analyze (e.g., "AI Engineer", "Backend Engineer")
        user_skills: Your current skills as comma-separated string
                     (e.g., "Python, FastAPI, LangChain, SQL")
        location: Job market location (default: "Indonesia")

    Returns:
        Structured market report with skill gap analysis and salary range
    """
    client = TavilyClient(api_key=TAVILY_API_KEY)
    llm = _get_llm()

    # Search job market data
    snippets = []
    queries = [
        f"{target_role} required skills {location} 2025",
        f"{target_role} job market demand salary {location}",
        f"{target_role} top companies hiring {location} 2025",
    ]

    for q in queries:
        try:
            resp = client.search(q, max_results=3, search_depth="basic")
            for r in resp.get("results", []):
                snippets.append(f"- {r.get('title','')}: {r.get('content','')[:300]}")
        except Exception:
            continue

    raw_data = "\n".join(snippets[:10]) if snippets else "No market data found."

    prompt = f"""Analyze the job market for: {target_role} in {location}

Market data from web:
{raw_data}

Applicant's current skills: {user_skills}

Produce a structured analysis in this EXACT format:

## Market Analysis: {target_role} ({location})

**Top 5 Skills Companies Want:**
1. [skill] [✓ if user has it, ✗ if missing]
2. [skill] [✓ or ✗]
3. [skill] [✓ or ✗]
4. [skill] [✓ or ✗]
5. [skill] [✓ or ✗]

**Your Match Score:** [X/5 skills (Y%)]

**Priority Skills to Learn Next:**
→ #1: [skill] — [why it matters + realistic time to learn basics]
→ #2: [skill] — [why it matters + realistic time to learn basics]

**Salary Range ({location}):**
- Junior (0-2yr): [range in IDR/month]
- Mid (2-4yr): [range in IDR/month]
- Senior (4yr+): [range in IDR/month]

**Top Companies Hiring Now:** [3-5 company names from search results]

Keep it factual. Only list skills that genuinely appear in job postings."""

    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Market analysis unavailable. Error: {str(e)}"
