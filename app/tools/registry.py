from langchain_core.tools import BaseTool
from typing import Dict, List, Any, Optional, TypedDict
import logging

logger = logging.getLogger(__name__)


class ToolInfo(TypedDict):
    """Metadata about a registered tool"""
    name: str
    description: str
    agent: str
    category: str
    tags: List[str]
    requires_context: bool
    requires_file: bool


class ToolRegistry:
    """
    Central registry for all agent tools.

    Each agent declares its tools here on startup.
    Provides a single source of truth for:
    - Tool discovery
    - Tool metadata
    - Tool execution
    - Tool categories and tags
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_info: Dict[str, ToolInfo] = {}
        self._agent_tools: Dict[str, List[str]] = {}
        logger.info("✅ ToolRegistry initialized")

    # ============================
    # REGISTER
    # ============================

    def register_agent_tools(
        self,
        agent_name: str,
        tools: List[BaseTool],
        category: str = "general",
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Register all tools for an agent.

        Args:
            agent_name: Name of the agent (e.g., 'code_agent')
            tools: List of LangChain tool instances
            category: Tool category (e.g., 'code', 'search', 'analysis')
            tags: Optional tags for filtering
        """
        tool_names = []

        for tool in tools:
            tool_name = tool.name

            # Store tool instance
            self._tools[tool_name] = tool

            # Store tool metadata
            self._tool_info[tool_name] = ToolInfo(
                name=tool_name,
                description=tool.description[:200] if tool.description else "",
                agent=agent_name,
                category=category,
                tags=tags or [],
                requires_context="context" in tool.description.lower() if tool.description else False,
                requires_file="file" in tool.description.lower() if tool.description else False,
            )

            tool_names.append(tool_name)
            logger.info(f"   🔧 Registered tool: {tool_name} → {agent_name}")

        # Map agent to its tools
        self._agent_tools[agent_name] = tool_names

        logger.info(f"✅ Registered {len(tools)} tools for {agent_name}")

    # ============================
    # GET TOOLS
    # ============================

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a specific tool by name"""
        return self._tools.get(tool_name)

    def get_agent_tools(self, agent_name: str) -> List[BaseTool]:
        """Get all tool instances for an agent"""
        tool_names = self._agent_tools.get(agent_name, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tool instances"""
        return list(self._tools.values())

    # ============================
    # GET INFO
    # ============================

    def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        """Get metadata for a specific tool"""
        return self._tool_info.get(tool_name)

    def get_agent_tool_info(self, agent_name: str) -> List[ToolInfo]:
        """Get metadata for all tools of an agent"""
        tool_names = self._agent_tools.get(agent_name, [])
        return [self._tool_info[name] for name in tool_names if name in self._tool_info]

    def get_all_tool_info(self) -> List[ToolInfo]:
        """Get metadata for all registered tools"""
        return list(self._tool_info.values())

    # ============================
    # SEARCH & FILTER
    # ============================

    def search_tools(self, query: str) -> List[ToolInfo]:
        """Search tools by name or description"""
        query_lower = query.lower()
        results = []

        for info in self._tool_info.values():
            if (
                query_lower in info["name"].lower()
                or query_lower in info["description"].lower()
                or query_lower in info["category"].lower()
                or any(query_lower in tag.lower() for tag in info["tags"])
            ):
                results.append(info)

        return results

    def get_tools_by_category(self, category: str) -> List[ToolInfo]:
        """Get all tools in a category"""
        return [
            info for info in self._tool_info.values()
            if info["category"] == category
        ]

    # ============================
    # EXECUTE
    # ============================

    def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
    ) -> Any:
        """
        Execute a tool by name with given input.

        Args:
            tool_name: Name of the tool
            tool_input: Dictionary of input parameters

        Returns:
            Tool execution result
        """
        tool = self._tools.get(tool_name)

        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry")

        try:
            result = tool.invoke(tool_input)
            logger.info(f"✅ Tool executed: {tool_name}")
            return result
        except Exception as e:
            logger.error(f"❌ Tool execution failed: {tool_name} — {e}")
            raise

    # ============================
    # STATISTICS
    # ============================

    def get_stats(self) -> dict:
        """Get registry statistics"""
        categories = {}
        for info in self._tool_info.values():
            cat = info["category"]
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_tools": len(self._tools),
            "total_agents": len(self._agent_tools),
            "tools_per_agent": {
                agent: len(tools) for agent, tools in self._agent_tools.items()
            },
            "categories": categories,
        }

    def get_summary(self) -> str:
        """Get human-readable summary"""
        lines = ["📋 Tool Registry Summary", "=" * 40]

        for agent, tool_names in self._agent_tools.items():
            lines.append(f"\n🤖 {agent}:")
            for name in tool_names:
                info = self._tool_info.get(name, {})
                desc = info.get("description", "")[:60]
                lines.append(f"   • {name}: {desc}...")

        return "\n".join(lines)


# ============================
# Singleton instance
# ============================
tool_registry = ToolRegistry()