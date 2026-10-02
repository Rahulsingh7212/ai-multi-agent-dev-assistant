from langchain_core.tools import tool
from tavily import TavilyClient
from config.settings import settings
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def _normalize_search_results(results: dict) -> List[Dict[str, Any]]:
    """
    Convert Tavily results into a clean frontend-friendly structure.
    """
    normalized = []

    for item in results.get("results", []):
        normalized.append({
            "title": item.get("title", "No Title"),
            "url": item.get("url", ""),
            "content": item.get("content", "No content"),
            "score": item.get("score"),
            "published_date": item.get("published_date"),
        })

    return normalized


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for real-time information using Tavily.
    Returns JSON string containing structured search results.
    """
    logger.info(f"🔧 web_search: {query}")

    try:
        client = TavilyClient(
            api_key=settings.TAVILY_API_KEY
        )

        results = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
        )

        normalized = _normalize_search_results(results)

        if not normalized:
            return '{"results": [], "message": "No search results found."}'

        import json

        return json.dumps({
            "results": normalized,
            "query": query,
            "result_count": len(normalized),
        })

    except Exception as e:
        import json

        return json.dumps({
            "results": [],
            "query": query,
            "error": str(e),
        })


@tool
def web_search_detailed(
    query: str,
    max_results: int = 3,
) -> str:
    """
    Perform a detailed web search using Tavily.
    Returns structured JSON.
    """
    logger.info(
        f"🔧 web_search_detailed: {query}"
    )

    try:
        client = TavilyClient(
            api_key=settings.TAVILY_API_KEY
        )

        results = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
        )

        normalized = _normalize_search_results(results)

        import json

        return json.dumps({
            "query": query,
            "answer": results.get("answer", ""),
            "results": normalized,
            "result_count": len(normalized),
        })

    except Exception as e:
        import json

        return json.dumps({
            "query": query,
            "answer": "",
            "results": [],
            "error": str(e),
        })


@tool
def web_get_latest_news(
    topic: str,
    max_results: int = 5,
) -> str:
    """
    Get the latest news about a specific topic.
    Returns structured JSON.
    """
    logger.info(
        f"🔧 web_get_latest_news: {topic}"
    )

    try:
        client = TavilyClient(
            api_key=settings.TAVILY_API_KEY
        )

        results = client.search(
            query=f"latest news {topic}",
            max_results=max_results,
            search_depth="basic",
            topic="news",
        )

        normalized = _normalize_search_results(results)

        import json

        if not normalized:
            return json.dumps({
                "topic": topic,
                "results": [],
                "message": (
                    f"No recent news found for: {topic}"
                ),
            })

        return json.dumps({
            "topic": topic,
            "results": normalized,
            "result_count": len(normalized),
        })

    except Exception as e:
        import json

        return json.dumps({
            "topic": topic,
            "results": [],
            "error": str(e),
        })


# ============================
# TOOL REGISTRY
# ============================
WEB_AGENT_TOOLS = [web_search, web_search_detailed, web_get_latest_news]

WEB_TOOL_MAP = {
    "web_search": web_search,
    "web_search_detailed": web_search_detailed,
    "web_get_latest_news": web_get_latest_news,
}