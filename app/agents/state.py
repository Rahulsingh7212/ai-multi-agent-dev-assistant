from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator


class AgentState(TypedDict):
    """
    Shared state that flows through ALL nodes in the Multi-Agent Graph.

    Updated for Stage 4: Added supervisor routing fields.
    """

    # ============================
    # Conversation History
    # ============================
    messages: Annotated[List[BaseMessage], operator.add]

    # ============================
    # Current Interaction
    # ============================
    user_query: str
    agent_type: str                        # Which agent is handling this
    tool_name: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    tool_output: Optional[str]

    # ============================
    # Supervisor Routing
    # ============================
    next_agent: str                        # Supervisor decision: code|resume|pdf|github|web
    supervisor_reasoning: Optional[str]    # Why supervisor chose this agent
    agent_handoff: Optional[bool]          # True if agent needs to hand off to another

    # ============================
    # RAG Context
    # ============================
    rag_context: Optional[str]
    rag_sources: Optional[List[str]]

    # ============================
    # File Upload Context
    # ============================
    uploaded_file_path: Optional[str]      # Path to uploaded file (resume, PDF)
    uploaded_file_content: Optional[str]   # Extracted text content of uploaded file

    # ============================
    # Final Output
    # ============================
    final_response: Optional[str]

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
) -> Dict[str, Any]:
    """Factory function to create a fresh AgentState."""
    return {
        "messages": [HumanMessage(content=user_query)],
        "user_query": user_query,
        "agent_type": "",
        "tool_name": None,
        "tool_input": None,
        "tool_output": None,
        "next_agent": "",
        "supervisor_reasoning": None,
        "agent_handoff": False,
        "rag_context": None,
        "rag_sources": None,
        "uploaded_file_path": uploaded_file_path,
        "uploaded_file_content": uploaded_file_content,
        "final_response": None,
        "session_id": session_id or "default",
        "iteration_count": 0,
        "error": None,
    }