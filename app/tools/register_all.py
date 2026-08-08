from app.tools.registry import tool_registry
from app.tools.code_tools import CODE_AGENT_TOOLS
from app.tools.resume_tools import RESUME_AGENT_TOOLS
from app.tools.pdf_tools import PDF_AGENT_TOOLS
from app.tools.github_tools import GITHUB_AGENT_TOOLS
from app.tools.web_tools import WEB_AGENT_TOOLS
import logging

logger = logging.getLogger(__name__)


def register_all_tools():
    """
    Register all agent tools into the central registry.
    Called once on application startup.
    """
    logger.info("🔧 Registering all agent tools...")

    # Code Agent Tools
    tool_registry.register_agent_tools(
        agent_name="code_agent",
        tools=CODE_AGENT_TOOLS,
        category="code",
        tags=["development", "programming", "debugging"],
    )

    # Resume Agent Tools
    tool_registry.register_agent_tools(
        agent_name="resume_agent",
        tools=RESUME_AGENT_TOOLS,
        category="resume",
        tags=["career", "hr", "ats"],
    )

    # PDF Agent Tools
    tool_registry.register_agent_tools(
        agent_name="pdf_agent",
        tools=PDF_AGENT_TOOLS,
        category="document",
        tags=["pdf", "analysis", "rag"],
    )

    # GitHub Agent Tools
    tool_registry.register_agent_tools(
        agent_name="github_agent",
        tools=GITHUB_AGENT_TOOLS,
        category="github",
        tags=["repository", "issues", "pull-requests"],
    )

    # Web Agent Tools
    tool_registry.register_agent_tools(
        agent_name="web_agent",
        tools=WEB_AGENT_TOOLS,
        category="search",
        tags=["web", "tavily", "real-time", "news"],
    )

    # Print summary
    logger.info(tool_registry.get_summary())
    stats = tool_registry.get_stats()
    logger.info(
        f"✅ Tool Registry: {stats['total_tools']} tools, "
        f"{stats['total_agents']} agents, "
        f"categories: {list(stats['categories'].keys())}"
    )


# Auto-register on import
register_all_tools()