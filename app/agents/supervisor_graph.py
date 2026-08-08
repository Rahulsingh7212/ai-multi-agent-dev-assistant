from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.supervisor import supervisor
from app.agents.agent_instances import AGENT_REGISTRY
import logging

logger = logging.getLogger(__name__)


def build_supervisor_graph() -> StateGraph:
    """
    Build the Multi-Agent Supervisor Graph.

    Architecture:
                    ┌──────────────┐
                    │  SUPERVISOR  │
                    └──────┬───────┘
                           │ (conditional edge)
              ┌────────────┼────────────┬────────────┬────────────┐
              ▼            ▼            ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  CODE    │ │  RESUME  │ │   PDF    │ │  GITHUB  │ │   WEB    │
        │  AGENT   │ │  AGENT   │ │  AGENT   │ │  AGENT   │ │  AGENT   │
        │(3 nodes) │ │(3 nodes) │ │(3 nodes) │ │(3 nodes) │ │(3 nodes) │
        └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │            │            │
             ▼            ▼            ▼            ▼            ▼
           END          END          END          END          END

    Each agent has 3 internal nodes:
    - route_query: Select tool
    - execute_tool: Run tool
    - generate_response: Create final answer
    """

    graph = StateGraph(AgentState)

    # ============================
    # ADD SUPERVISOR NODE
    # ============================
    graph.add_node("supervisor", supervisor.route)

    # ============================
    # ADD ALL AGENT NODES
    # ============================
    for agent_name, agent_instance in AGENT_REGISTRY.items():
        # Each agent gets 3 nodes
        route_name = f"{agent_name}_route"
        tool_name = f"{agent_name}_tool"
        response_name = f"{agent_name}_response"

        graph.add_node(route_name, agent_instance.route_query)
        graph.add_node(tool_name, agent_instance.execute_tool)
        graph.add_node(response_name, agent_instance.generate_response)

        # Internal agent edges: route → tool → response
        graph.add_edge(route_name, tool_name)
        graph.add_edge(tool_name, response_name)
        graph.add_edge(response_name, END)

        logger.info(f"✅ Added {agent_name} nodes: {route_name} → {tool_name} → {response_name}")

    # ============================
    # ENTRY POINT
    # ============================
    graph.set_entry_point("supervisor")

    # ============================
    # CONDITIONAL EDGES
    # ============================
    # Supervisor routes to the correct agent's route node
    def supervisor_router(state: AgentState) -> str:
        """Determine which agent to route to based on supervisor decision"""
        next_agent = state.get("next_agent", "code_agent")
        target = f"{next_agent}_route"
        logger.info(f"🔀 Conditional edge: supervisor → {target}")
        return target

    graph.add_conditional_edges(
        "supervisor",
        supervisor_router,
        {
            "code_agent_route": "code_agent_route",
            "resume_agent_route": "resume_agent_route",
            "pdf_agent_route": "pdf_agent_route",
            "github_agent_route": "github_agent_route",
            "web_agent_route": "web_agent_route",
        }
    )

    # ============================
    # COMPILE
    # ============================
    compiled_graph = graph.compile()

    logger.info("✅ Multi-Agent Supervisor Graph compiled successfully!")
    logger.info("   supervisor → [code|resume|pdf|github|web]_route → _tool → _response → END")

    return compiled_graph


# ============================
# Singleton compiled graph
# ============================
supervisor_graph = build_supervisor_graph()