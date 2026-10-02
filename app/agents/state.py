from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
import operator


class AgentState(TypedDict):
    """
    Shared state that flows through ALL nodes in the Multi-Agent Graph.

    Supports:
    - Supervisor-based automatic routing
    - User-selected agent routing
    - Persistent conversation memory
    - RAG context
    - File uploads
    """

    # ============================
    # Conversation History
    # ============================
    messages: Annotated[List[BaseMessage], operator.add]

    # ============================
    # Current Interaction
    # ============================
    user_query: str
    agent_type: str
    tool_name: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    tool_output: Optional[str]

    # ============================
    # Supervisor Routing
    # ============================
    next_agent: str
    supervisor_reasoning: Optional[str]
    agent_handoff: Optional[bool]

    # ============================
    # USER SELECTED AGENT
    # ============================
    selected_agent: Optional[str]

    # ============================
    # RAG Context
    # ============================
    rag_context: Optional[str]
    rag_sources: Optional[List[str]]

    # ============================
    # File Upload Context
    # ============================
    uploaded_file_path: Optional[str]
    uploaded_file_content: Optional[str]

    # ============================
    # Final Output
    # ============================
    final_response: Optional[str]

    # ============================
# Web Search Results
# ============================
    web_results: Optional[List[Dict[str, Any]]]

    # ============================
# GitHub Results
# ============================
    github_results: Optional[List[Dict[str, Any]]]

    # ============================
    # Metadata
    # ============================
    session_id: Optional[str]
    iteration_count: int
    error: Optional[str]


def create_initial_state(
    user_query: str,
    session_id: Optional[str] = None,
    uploaded_file_path: Optional[str] = None,
    uploaded_file_content: Optional[str] = None,
    selected_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Factory function to create a fresh AgentState.

    selected_agent:
        None  -> Supervisor automatically chooses the agent.
        code_agent
        resume_agent
        pdf_agent
        github_agent
        web_agent
    """

    return {
        "messages": [
            HumanMessage(content=user_query)
        ],

        "user_query": user_query,

        "agent_type": "",

        "tool_name": None,

        "tool_input": None,

        "tool_output": None,

        "next_agent": "",

        "supervisor_reasoning": None,

        "agent_handoff": False,

        # User-selected agent
        "selected_agent": selected_agent,

        "rag_context": None,

        "rag_sources": None,

        "uploaded_file_path": uploaded_file_path,

        "uploaded_file_content": uploaded_file_content,

        "final_response": None,

        "github_results": [],

        "web_results": [],

        "session_id": session_id or "default",

        "iteration_count": 0,

        "error": None,
    }