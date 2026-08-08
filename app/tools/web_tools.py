from langchain_core.tools import tool
from tavily import TavilyClient
from config.settings import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for real-time information using Tavily.

    Args:
        query: Search query string
        max_results: Maximum number of results

    Returns:
        Search results as formatted string
    """
    logger.info(f"🔧 web_search: {query}")

    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        results = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
        )

        if not results.get("results"):
            return "No search results found."

        formatted = []
        for r in results["results"]:
            formatted.append(
                f"• {r.get('title', 'No Title')}\n"
                f"  URL: {r.get('url', 'N/A')}\n"
                f"  {r.get('content', 'No content')[:300]}"
            )

        return "\n\n".join(formatted)

    except Exception as e:
        return f"Web search error: {str(e)}"


@tool
def web_search_detailed(query: str, max_results: int = 3) -> str:
    """
    Perform a detailed/advanced web search using Tavily.
    Returns more comprehensive results with extracted content.

    Args:
        query: Search query string
        max_results: Maximum number of results

    Returns:
        Detailed search results
    """
    logger.info(f"🔧 web_search_detailed: {query}")

    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        results = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
        )

        answer = results.get("answer", "")
        output_parts = []

        if answer:
            output_parts.append(f"**Direct Answer:** {answer}\n")

        output_parts.append("**Sources:**")
        for r in results.get("results", []):
            output_parts.append(
                f"\n• {r.get('title', 'No Title')}\n"
                f"  URL: {r.get('url', 'N/A')}\n"
                f"  {r.get('content', 'No content')[:500]}"
            )

        return "\n".join(output_parts) if output_parts else "No results found."

    except Exception as e:
        return f"Detailed web search error: {str(e)}"


@tool
def web_get_latest_news(topic: str, max_results: int = 5) -> str:
    """
    Get the latest news about a specific topic.

    Args:
        topic: News topic to search for
        max_results: Maximum number of articles

    Returns:
        Latest news articles
    """
    logger.info(f"🔧 web_get_latest_news: {topic}")

    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        results = client.search(
            query=f"latest news {topic} 2025",
            max_results=max_results,
            search_depth="basic",
            topic="news",
        )

        if not results.get("results"):
            return f"No recent news found for: {topic}"

        formatted = []
        for r in results["results"]:
            formatted.append(
                f"• {r.get('title', 'No Title')}\n"
                f"  URL: {r.get('url', 'N/A')}\n"
                f"  {r.get('content', 'No content')[:250]}"
            )

        return "\n\n".join(formatted)

    except Exception as e:
        return f"News search error: {str(e)}"


# ============================
# TOOL REGISTRY
# ============================
WEB_AGENT_TOOLS = [web_search, web_search_detailed, web_get_latest_news]

WEB_TOOL_MAP = {
    "web_search": web_search,
    "web_search_detailed": web_search_detailed,
    "web_get_latest_news": web_get_latest_news,
}