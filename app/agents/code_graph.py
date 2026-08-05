from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.code_agent import code_agent
import logging

logger = logging.getLogger(__name__)


def build_code_agent_graph() -> StateGraph:
    """
    Build the LangGraph for the Code Agent.

    Graph Structure:
    ┌──────────┐     ┌──────────────┐     ┌───────────────────┐
    │  ROUTER  │────▶│ TOOL EXECUTOR│────▶│ RESPONSE GENERATOR│
    └──────────┘     └──────────────┘     └───────────────────┘

    1. ROUTER:            Analyzes query → selects tool
    2. TOOL EXECUTOR:     Executes selected tool
    3. RESPONSE GENERATOR: Generates final answer using tool output
    """

    # Create the graph with our state schema
    graph = StateGraph(AgentState)

    # ============================
    # ADD NODES
    # ============================
    graph.add_node("router", code_agent.route_query)
    graph.add_node("tool_executor", code_agent.execute_tool)
    graph.add_node("response_generator", code_agent.generate_response)

    # ============================
    # SET ENTRY POINT
    # ============================
    graph.set_entry_point("router")

    # ============================
    # ADD EDGES
    # ============================
    # router → tool_executor
    graph.add_edge("router", "tool_executor")

    # tool_executor → response_generator
    graph.add_edge("tool_executor", "response_generator")

    # response_generator → END
    graph.add_edge("response_generator", END)

    # ============================
    # COMPILE THE GRAPH
    # ============================
    compiled_graph = graph.compile()

    logger.info("✅ Code Agent graph compiled: router → tool_executor → response_generator → END")

    return compiled_graph


# ============================
# Singleton compiled graph
# ============================
code_agent_graph = build_code_agent_graph()